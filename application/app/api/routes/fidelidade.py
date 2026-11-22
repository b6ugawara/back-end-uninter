from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from pydantic import BaseModel, Field
from app.infrastructure.database.database import get_db
from app.api.dependencies import get_current_user
from app.models import (
    Cliente,
    Fidelidade,
    MovimentacaoFidelidade,
    ConsentimentoFidelidade
)

router = APIRouter(prefix="/fidelidade", tags=["Fidelidade"])

def verificar_cliente(conta):
    if not isinstance(conta, Cliente):
        raise HTTPException(
            status_code=403,
            detail="Recurso disponível apenas para clientes"
        )


def obter_agora():
    return datetime.now(timezone.utc).replace(tzinfo=None)


@router.get("/saldo")
def consultar_saldo(
    conta=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verificar_cliente(conta)

    fidelidade = db.query(Fidelidade).filter(
        Fidelidade.idCliente == conta.idCliente
    ).first()

    return {
        "idCliente": conta.idCliente,
        "saldo_pontos": fidelidade.saldo_pontos if fidelidade else 0
    }


@router.get("/historico")
def consultar_historico(
    conta=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verificar_cliente(conta)

    fidelidade = db.query(Fidelidade).filter(
        Fidelidade.idCliente == conta.idCliente
    ).first()

    if not fidelidade:
        return {
            "total": 0,
            "historico": []
        }

    movimentacoes = db.query(MovimentacaoFidelidade).filter(
        MovimentacaoFidelidade.idFidelidade == fidelidade.idFidelidade
    ).order_by(
        MovimentacaoFidelidade.data_hora.desc(),
        MovimentacaoFidelidade.idMovimentacao.desc()
    ).all()

    return {
        "total": len(movimentacoes),
        "historico": [
            {
                "idMovimentacao": mov.idMovimentacao,
                "idPedido": mov.idPedido,
                "tipo": mov.tipo,
                "pontos": mov.pontos,
                "descricao": mov.descricao,
                "data_hora": mov.data_hora
            }
            for mov in movimentacoes
        ]
    }


@router.post("/consentimento")
def aceitar_consentimento(
    conta=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verificar_cliente(conta)

    consentimento = db.query(ConsentimentoFidelidade).filter(
        ConsentimentoFidelidade.idCliente == conta.idCliente
    ).first()

    agora = obter_agora()

    if consentimento and consentimento.aceito:
        raise HTTPException(
            status_code=409,
            detail="Consentimento já foi aceito"
        )

    try:
        if consentimento:
            consentimento.aceito = True
            consentimento.data_aceite = agora
            consentimento.data_revogacao = None
        else:
            consentimento = ConsentimentoFidelidade(
                idCliente=conta.idCliente,
                aceito=True,
                data_aceite=agora
            )
            db.add(consentimento)

        db.commit()
        db.refresh(consentimento)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Já existe um registro de consentimento para este cliente"
        )

    except Exception:
        db.rollback()
        raise

    return {
        "mensagem": "Consentimento aceito com sucesso",
        "aceito": True,
        "data_aceite": consentimento.data_aceite
    }


@router.delete("/consentimento")
def revogar_consentimento(
    conta=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verificar_cliente(conta)

    consentimento = db.query(ConsentimentoFidelidade).filter(
        ConsentimentoFidelidade.idCliente == conta.idCliente
    ).first()

    if not consentimento or not consentimento.aceito:
        raise HTTPException(
            status_code=404,
            detail="Não existe consentimento ativo"
        )

    agora = obter_agora()

    try:
        consentimento.aceito = False
        consentimento.data_revogacao = agora

        db.commit()
        db.refresh(consentimento)

    except Exception:
        db.rollback()
        raise

    return {
        "mensagem": "Consentimento revogado com sucesso",
        "aceito": False,
        "data_revogacao": consentimento.data_revogacao
    }

class ResgateRequest(BaseModel):
    pontos: int = Field(gt=0)


@router.post("/resgatar")
def resgatar_pontos(
    dados: ResgateRequest,
    conta=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verificar_cliente(conta)

    # Verifica o consentimento do cliente.
    consentimento = db.query(ConsentimentoFidelidade).filter(
        ConsentimentoFidelidade.idCliente == conta.idCliente
    ).first()

    if not consentimento or not consentimento.aceito:
        raise HTTPException(
            status_code=403,
            detail="É necessário aceitar o consentimento da fidelidade"
        )

    # Busca o saldo de pontos.
    fidelidade = db.query(Fidelidade).filter(
        Fidelidade.idCliente == conta.idCliente
    ).with_for_update().first()

    if not fidelidade:
        raise HTTPException(
            status_code=400,
            detail="Cliente ainda não possui saldo de fidelidade"
        )

    if fidelidade.saldo_pontos < dados.pontos:
        raise HTTPException(
            status_code=400,
            detail="Saldo de pontos insuficiente"
        )

    # Conversão: 100 pontos = R$ 1,00.
    desconto = dados.pontos / 100

    try:
        fidelidade.saldo_pontos -= dados.pontos

        movimentacao = MovimentacaoFidelidade(
            idFidelidade=fidelidade.idFidelidade,
            idPedido=None,
            tipo="RESGATE",
            pontos=dados.pontos,
            descricao=f"Resgate de {dados.pontos} pontos. Desconto: R$ {desconto:.2f}",
            data_hora=obter_agora()
        )

        db.add(movimentacao)
        db.commit()
        db.refresh(fidelidade)

    except Exception:
        db.rollback()
        raise

    return {
        "mensagem": "Pontos resgatados com sucesso",
        "pontos_resgatados": dados.pontos,
        "desconto": round(desconto, 2),
        "saldo_restante": fidelidade.saldo_pontos
    }