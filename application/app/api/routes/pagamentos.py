from datetime import datetime, timezone
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.infrastructure.database.database import get_db
from app.api.dependencies import get_current_user
from app.models import Cliente, Pagamento, Pedido

router = APIRouter(prefix="/pagamentos", tags=["Pagamentos"])


class CriarPagamentoRequest(BaseModel):
    idPedido: int
    metodo_pagamento: Literal[
        "PIX", "CARTAO_CREDITO", "CARTAO_DEBITO", "DINHEIRO"
    ]


class RetornoPagamentoRequest(BaseModel):
    codigo_transacao: str
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
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    if isinstance(conta, Cliente) and pedido.idCliente != conta.idCliente:
        raise HTTPException(status_code=403, detail="Pedido não pertence ao cliente")

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
        status="PENDENTE"
    )

    db.add(pagamento)
    db.commit()
    db.refresh(pagamento)

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
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    if isinstance(conta, Cliente):
        if pedido.idCliente != conta.idCliente:
            raise HTTPException(status_code=403, detail="Acesso não permitido")
    elif conta.tipo_usuario not in ["ATENDENTE", "GERENTE"]:
        raise HTTPException(status_code=403, detail="Acesso não permitido")

    pagamento = db.query(Pagamento).filter(
        Pagamento.idPedido == idPedido
    ).first()

    if not pagamento:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado")

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
    db: Session = Depends(get_db)
):
    pagamento = db.query(Pagamento).filter(
        Pagamento.idPagamento == idPagamento
    ).first()

    if not pagamento:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado")

    if pagamento.status != "PENDENTE":
        raise HTTPException(
            status_code=409,
            detail="Este pagamento já foi processado"
        )

    pagamento.status = dados.status
    pagamento.codigo_transacao = dados.codigo_transacao
    pagamento.data_pagamento = datetime.now(timezone.utc).replace(tzinfo=None)

    db.commit()
    db.refresh(pagamento)

    return {
        "mensagem": "Retorno do pagamento recebido",
        "idPagamento": pagamento.idPagamento,
        "status": pagamento.status
    }
