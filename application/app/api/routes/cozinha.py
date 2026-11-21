from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.infrastructure.database.database import get_db
from app.api.dependencies import get_current_user
from app.models import (
    Cliente,
    Cozinha,
    Pedido,
    ItemPedido,
    Produto,
)


router = APIRouter(prefix="/cozinha", tags=["Cozinha"])


class AtualizarStatusRequest(BaseModel):
    status: Literal["EM_PREPARO", "PRONTO"]


def verificar_permissao_cozinha(conta, permitir_gerente=True):
    if isinstance(conta, Cliente):
        raise HTTPException(
            status_code=403,
            detail="Acesso permitido apenas à equipe da cozinha"
        )

    perfil = conta.tipo_usuario

    perfis_permitidos = ["COZINHA", "GERENTE"] if permitir_gerente else ["COZINHA"]

    if perfil not in perfis_permitidos:
        raise HTTPException(
            status_code=403,
            detail="Você não tem permissão para acessar este recurso"
        )


@router.get("/pedidos")
def listar_pedidos_cozinha(
    status: str | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    conta=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verificar_permissao_cozinha(conta)

    consulta = (
        db.query(Cozinha, Pedido)
        .join(Pedido, Cozinha.idPedido == Pedido.idPedido)
    )

    if status:
        consulta = consulta.filter(Cozinha.status == status)

    total = consulta.count()

    registros = (
        consulta
        .order_by(Pedido.data_hora.asc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    pedidos = []

    for cozinha, pedido in registros:
        itens = (
            db.query(ItemPedido, Produto.nome)
            .join(Produto, ItemPedido.idProduto == Produto.idProduto)
            .filter(ItemPedido.idPedido == pedido.idPedido)
            .all()
        )

        pedidos.append({
            "idPedido": pedido.idPedido,
            "status": cozinha.status,
            "canalPedido": pedido.canalPedido,
            "data_hora": pedido.data_hora.isoformat(),
            "itens": [
                {
                    "idProduto": item.idProduto,
                    "produto": nome,
                    "quantidade": item.quantidade
                }
                for item, nome in itens
            ]
        })

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "pedidos": pedidos
    }


@router.get("/pedidos/{idPedido}")
def consultar_pedido_cozinha(
    idPedido: int,
    conta=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verificar_permissao_cozinha(conta)

    registro = (
        db.query(Cozinha, Pedido)
        .join(Pedido, Cozinha.idPedido == Pedido.idPedido)
        .filter(Pedido.idPedido == idPedido)
        .first()
    )

    if registro is None:
        raise HTTPException(
            status_code=404,
            detail="Pedido não encontrado na fila da cozinha"
        )

    cozinha, pedido = registro

    itens = (
        db.query(ItemPedido, Produto.nome)
        .join(Produto, ItemPedido.idProduto == Produto.idProduto)
        .filter(ItemPedido.idPedido == idPedido)
        .all()
    )

    return {
        "idPedido": pedido.idPedido,
        "status": cozinha.status,
        "canalPedido": pedido.canalPedido,
        "unidadeId": pedido.idUnidade,
        "data_hora": pedido.data_hora.isoformat(),
        "hora_inicio": (
            cozinha.hora_inicio.isoformat()
            if cozinha.hora_inicio else None
        ),
        "hora_conclusao": (
            cozinha.hora_conclusao.isoformat()
            if cozinha.hora_conclusao else None
        ),
        "itens": [
            {
                "idProduto": item.idProduto,
                "produto": nome,
                "quantidade": item.quantidade,
                "preco_unitario": float(item.preco_unitario)
            }
            for item, nome in itens
        ]
    }


@router.patch("/pedidos/{idPedido}/status")
def atualizar_status_cozinha(
    idPedido: int,
    dados: AtualizarStatusRequest,
    conta=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verificar_permissao_cozinha(conta, permitir_gerente=False)

    registro = (
        db.query(Cozinha, Pedido)
        .join(Pedido, Cozinha.idPedido == Pedido.idPedido)
        .filter(Pedido.idPedido == idPedido)
        .first()
    )

    if registro is None:
        raise HTTPException(
            status_code=404,
            detail="Pedido não encontrado na fila da cozinha"
        )

    cozinha, pedido = registro

    if cozinha.status == "AGUARDANDO" and dados.status == "EM_PREPARO":
        cozinha.status = "EM_PREPARO"
        cozinha.hora_inicio = datetime.now(timezone.utc).replace(tzinfo=None)
        cozinha.idUsuario = conta.idUsuario

    elif cozinha.status == "EM_PREPARO" and dados.status == "PRONTO":
        cozinha.status = "PRONTO"
        cozinha.hora_conclusao = datetime.now(timezone.utc).replace(tzinfo=None)

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Não é possível alterar de {cozinha.status} para {dados.status}"
        )

    pedido.status = cozinha.status

    db.commit()
    db.refresh(cozinha)

    return {
        "mensagem": "Status atualizado com sucesso",
        "idPedido": pedido.idPedido,
        "status": cozinha.status,
        "hora_inicio": (
            cozinha.hora_inicio.isoformat()
            if cozinha.hora_inicio else None
        ),
        "hora_conclusao": (
            cozinha.hora_conclusao.isoformat()
            if cozinha.hora_conclusao else None
        )
    }