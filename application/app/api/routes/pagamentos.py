import os
import hmac
import uuid

from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.infrastructure.database.database import get_db
from app.api.dependencies import get_current_user
from app.models import (
    Cliente,
    Pagamento,
    Pedido,
    Fidelidade,
    MovimentacaoFidelidade,
    ConsentimentoFidelidade,
    Cozinha
)


router = APIRouter(prefix="/pagamentos", tags=["Pagamentos"])

class CriarPagamentoRequest(BaseModel):
    idPedido: int

    metodo_pagamento: Literal[
        "PIX",
        "CARTAO_CREDITO",
        "CARTAO_DEBITO",
        "DINHEIRO"
    ]


class RetornoPagamentoRequest(BaseModel):
    status: Literal["APROVADO", "RECUSADO"]

def verificar_permissao(conta):
    if isinstance(conta, Cliente):
        return

    if conta.tipo_usuario not in ["ATENDENTE", "GERENTE"]:
        raise HTTPException(
            status_code=403,
            detail="Você não tem permissão para realizar esta operação"
        )


@router.post("/")
def criar_pagamento(
    dados: CriarPagamentoRequest,
    conta=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verificar_permissao(conta)

    pedido = db.query(Pedido).filter(
        Pedido.idPedido == dados.idPedido
    ).first()

    if not pedido:
        raise HTTPException(
            status_code=404,
            detail="Pedido não encontrado"
        )

    if isinstance(conta, Cliente) and pedido.idCliente != conta.idCliente:
        raise HTTPException(
            status_code=403,
            detail="Pedido não pertence ao cliente"
        )

    pagamento_existente = db.query(Pagamento).filter(
        Pagamento.idPedido == dados.idPedido
    ).first()

    if pagamento_existente:
        raise HTTPException(
            status_code=409,
            detail="Este pedido já possui um pagamento registrado"
        )


    pagamento = Pagamento(
        idPedido=pedido.idPedido,
        valor=pedido.valor_total,
        metodo_pagamento=dados.metodo_pagamento,
        status="PENDENTE",
        codigo_transacao=f"SIM-{uuid.uuid4().hex}"
)

    try:
        db.add(pagamento)
        db.commit()
        db.refresh(pagamento)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Este pedido já possui um pagamento registrado"
        )

    except Exception:
        db.rollback()
        raise

    return {
        "mensagem": "Pagamento registrado e aguardando confirmação",
        "idPagamento": pagamento.idPagamento,
        "idPedido": pagamento.idPedido,
        "valor": pagamento.valor,
        "status": pagamento.status
    }


@router.get("/{idPedido}")
def consultar_pagamento(
    idPedido: int,
    conta=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    pedido = db.query(Pedido).filter(
        Pedido.idPedido == idPedido
    ).first()

    if not pedido:
        raise HTTPException(
            status_code=404,
            detail="Pedido não encontrado"
        )

    if isinstance(conta, Cliente):
        if pedido.idCliente != conta.idCliente:
            raise HTTPException(
                status_code=403,
                detail="Acesso não permitido"
            )

    elif conta.tipo_usuario not in ["ATENDENTE", "GERENTE"]:
        raise HTTPException(
            status_code=403,
            detail="Acesso não permitido"
        )

    pagamento = db.query(Pagamento).filter(
        Pagamento.idPedido == idPedido
    ).first()

    if not pagamento:
        raise HTTPException(
            status_code=404,
            detail="Pagamento não encontrado"
        )

    return {
        "idPagamento": pagamento.idPagamento,
        "idPedido": pagamento.idPedido,
        "valor": pagamento.valor,
        "metodo_pagamento": pagamento.metodo_pagamento,
        "status": pagamento.status,
        "codigo_transacao": pagamento.codigo_transacao,
        "data_pagamento": pagamento.data_pagamento
    }


@router.post("/webhook")
def receber_retorno_pagamento(
    dados: RetornoPagamentoRequest,
    idPagamento: int,
    db: Session = Depends(get_db),
    webhook_secret: str | None = Header(
        default=None,
        alias="X-Webhook-Secret"
    )
):
    segredo_configurado = os.getenv("PAGAMENTO_WEBHOOK_SECRET")

    if not segredo_configurado:
        raise HTTPException(
            status_code=503,
            detail="Segredo do webhook não configurado no servidor"
        )

    if not webhook_secret or not hmac.compare_digest(
        webhook_secret,
        segredo_configurado
    ):
        raise HTTPException(
            status_code=401,
            detail="Autenticação do webhook inválida"
        )

    agora = datetime.now(timezone.utc).replace(tzinfo=None)

    try:
        # Atualiza somente pagamentos ainda pendentes.

        resultado = db.query(Pagamento).filter(
            Pagamento.idPagamento == idPagamento,
            Pagamento.status == "PENDENTE"
        ).update(
            {
                Pagamento.status: dados.status,
                Pagamento.data_pagamento: agora
            },
            synchronize_session=False
        )
        if resultado == 0:
            pagamento_existente = db.query(Pagamento).filter(
                Pagamento.idPagamento == idPagamento
            ).first()

            if not pagamento_existente:
                raise HTTPException(
                    status_code=404,
                    detail="Pagamento não encontrado"
                )

            raise HTTPException(
                status_code=409,
                detail="Este pagamento já foi processado"
            )

        pagamento = db.query(Pagamento).filter(
            Pagamento.idPagamento == idPagamento
        ).first()

        pontos_creditados = 0
        pedido = None

        if dados.status == "APROVADO":
            pedido = db.query(Pedido).filter(
                Pedido.idPedido == pagamento.idPedido
            ).first()

            if pedido:
                cozinha = db.query(Cozinha).filter(
                    Cozinha.idPedido == pedido.idPedido
                ).first()

                if not cozinha:
                    cozinha = Cozinha(
                        idPedido=pedido.idPedido,
                        status="AGUARDANDO"
                    )
                    db.add(cozinha)

                pedido.status = "AGUARDANDO"

                if pedido.idCliente:
                    consentimento = db.query(
                        ConsentimentoFidelidade
                    ).filter(
                        ConsentimentoFidelidade.idCliente == pedido.idCliente,
                        ConsentimentoFidelidade.aceito.is_(True)
                    ).first()

                    if consentimento:
                        credito_existente = db.query(
                            MovimentacaoFidelidade
                        ).filter(
                            MovimentacaoFidelidade.idPedido == pedido.idPedido,
                            MovimentacaoFidelidade.tipo == "CREDITO"
                        ).first()

                        if not credito_existente:
                            fidelidade = db.query(Fidelidade).filter(
                                Fidelidade.idCliente == pedido.idCliente
                            ).first()

                            if not fidelidade:
                                fidelidade = Fidelidade(
                                    idCliente=pedido.idCliente,
                                    saldo_pontos=0
                                )
                                db.add(fidelidade)
                                db.flush()

                            pontos_creditados = int(pagamento.valor)

                            if pontos_creditados > 0:
                                fidelidade.saldo_pontos += pontos_creditados

                                movimentacao = MovimentacaoFidelidade(
                                    idFidelidade=fidelidade.idFidelidade,
                                    idPedido=pedido.idPedido,
                                    tipo="CREDITO",
                                    pontos=pontos_creditados,
                                    descricao="Pontos recebidos por compra"
                                )
                                db.add(movimentacao)

        else:
            pedido = db.query(Pedido).filter(
                Pedido.idPedido == pagamento.idPedido
            ).first()

            if pedido:
                pedido.status = "CANCELADO"

        db.commit()
        db.refresh(pagamento)

    except HTTPException:
        db.rollback()
        raise

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Conflito de integridade ao processar o pagamento"
        )
    except Exception:
        db.rollback()
        raise

    return {
        "mensagem": "Retorno do pagamento recebido",
        "idPagamento": pagamento.idPagamento,
        "status": pagamento.status,
        "pontos_creditados": pontos_creditados
    }
