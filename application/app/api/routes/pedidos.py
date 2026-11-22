
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.infrastructure.database.database import get_db
from app.api.dependencies import get_current_user
from app.models import (
    Pedido,
    ItemPedido,
    Produto,
    Estoque,
    Cozinha,
    Cliente,
    Unidade
)

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])


class ItemPedidoRequest(BaseModel):
    idProduto: int
    quantidade: int = Field(gt=0)


class PedidoRequest(BaseModel):
    unidadeId: int
    canalPedido: str = Field(min_length=1, max_length=30)
    itens: list[ItemPedidoRequest] = Field(min_length=1)


def verificar_acesso_pedido(pedido, conta):
    # Cliente só acessa os próprios pedidos.
    if isinstance(conta, Cliente):
        if pedido.idCliente != conta.idCliente:
            raise HTTPException(
                status_code=403,
                detail="Você não tem permissão para acessar este pedido"
            )

    # Atendente só acessa pedidos da própria unidade.
    elif getattr(conta, "tipo_usuario", None) == "ATENDENTE":
        if pedido.idUnidade != conta.idUnidade:
            raise HTTPException(
                status_code=403,
                detail="Você não tem permissão para acessar este pedido"
            )


@router.post("/")
def criar_pedido(
    dados: PedidoRequest,
    conta=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    eh_cliente = isinstance(conta, Cliente)
    eh_atendente = getattr(conta, "tipo_usuario", None) == "ATENDENTE"

    if not eh_cliente and not eh_atendente:
        raise HTTPException(
            status_code=403,
            detail="Apenas clientes e atendentes podem criar pedidos"
        )

    # Cliente escolhe a unidade.
    # Atendente utiliza a unidade vinculada à sua conta.
    unidade_id = dados.unidadeId if eh_cliente else conta.idUnidade

    if unidade_id is None:
        raise HTTPException(
            status_code=400,
            detail="Não foi possível identificar a unidade do pedido"
        )

    unidade = db.query(Unidade).filter(
        Unidade.idUnidade == unidade_id
    ).first()

    if unidade is None:
        raise HTTPException(
            status_code=404,
            detail="Unidade não encontrada"
        )

    # Soma as quantidades de produtos repetidos.
    quantidades_por_produto = {}

    for item in dados.itens:
        quantidades_por_produto[item.idProduto] = (
            quantidades_por_produto.get(item.idProduto, 0)
            + item.quantidade
        )

    valor_total = Decimal("0.00")
    itens_para_salvar = []

    # Valida cada produto e o total necessário em estoque.
    for id_produto, quantidade_total in quantidades_por_produto.items():

        produto = db.query(Produto).filter(
            Produto.idProduto == id_produto,
            Produto.status == "ATIVO"
        ).first()

        if produto is None:
            raise HTTPException(
                status_code=404,
                detail=f"Produto {id_produto} não encontrado ou inativo"
            )

        estoque = db.query(Estoque).filter(
            Estoque.idProduto == id_produto,
            Estoque.idUnidade == unidade_id
        ).first()

        if estoque is None or estoque.quantidade < quantidade_total:
            raise HTTPException(
                status_code=400,
                detail=f"Estoque insuficiente para o produto {produto.nome}"
            )

    # Calcula o valor e prepara os itens do pedido.
    # Mantém as linhas originais enviadas na requisição.
    for item in dados.itens:
        produto = db.query(Produto).filter(
            Produto.idProduto == item.idProduto
        ).first()

        preco = Decimal(str(produto.preco))
        valor_total += preco * item.quantidade

        itens_para_salvar.append({
            "idProduto": produto.idProduto,
            "quantidade": item.quantidade,
            "preco_unitario": preco
        })

    try:
        pedido = Pedido(
            idCliente=conta.idCliente if eh_cliente else None,
            idUsuario=conta.idUsuario if eh_atendente else None,
            idUnidade=unidade_id,
            data_hora=datetime.now(timezone.utc).replace(tzinfo=None),
            status="PENDENTE",
            valor_total=valor_total,
            canalPedido=dados.canalPedido
        )

        db.add(pedido)
        db.flush()

        cozinha = Cozinha(
            idPedido=pedido.idPedido,
            status="AGUARDANDO"
        )

        db.add(cozinha)

        for item in itens_para_salvar:
            novo_item = ItemPedido(
                idPedido=pedido.idPedido,
                idProduto=item["idProduto"],
                quantidade=item["quantidade"],
                preco_unitario=item["preco_unitario"]
            )

            db.add(novo_item)

        db.commit()
        db.refresh(pedido)

    except Exception:
        db.rollback()
        raise

    return {
        "mensagem": "Pedido criado com sucesso",
        "idPedido": pedido.idPedido,
        "status": pedido.status,
        "canalPedido": pedido.canalPedido,
        "valor_total": float(pedido.valor_total)
    }


@router.get("/")
def listar_pedidos(
    canalPedido: str | None = None,
    status: str | None = None,
    unidadeId: int | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    conta=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    consulta = db.query(Pedido)

    if isinstance(conta, Cliente):
        consulta = consulta.filter(
            Pedido.idCliente == conta.idCliente
        )

    elif getattr(conta, "tipo_usuario", None) == "ATENDENTE":
        consulta = consulta.filter(
            Pedido.idUnidade == conta.idUnidade
        )

    if canalPedido:
        consulta = consulta.filter(
            Pedido.canalPedido == canalPedido
        )

    if status:
        consulta = consulta.filter(
            Pedido.status == status
        )

    if unidadeId is not None:
        consulta = consulta.filter(
            Pedido.idUnidade == unidadeId
        )

    total = consulta.count()

    pedidos = (
        consulta
        .order_by(Pedido.data_hora.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "pedidos": [
            {
                "idPedido": pedido.idPedido,
                "idCliente": pedido.idCliente,
                "idUsuario": pedido.idUsuario,
                "unidadeId": pedido.idUnidade,
                "canalPedido": pedido.canalPedido,
                "status": pedido.status,
                "data_hora": pedido.data_hora.isoformat(),
                "valor_total": float(pedido.valor_total)
            }
            for pedido in pedidos
        ]
    }


@router.get("/{id}")
def consultar_pedido(
    id: int,
    conta=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    pedido = db.query(Pedido).filter(
        Pedido.idPedido == id
    ).first()

    if pedido is None:
        raise HTTPException(
            status_code=404,
            detail="Pedido não encontrado"
        )

    verificar_acesso_pedido(pedido, conta)

    itens = (
        db.query(ItemPedido, Produto.nome)
        .join(
            Produto,
            ItemPedido.idProduto == Produto.idProduto
        )
        .filter(ItemPedido.idPedido == pedido.idPedido)
        .all()
    )

    return {
        "idPedido": pedido.idPedido,
        "idCliente": pedido.idCliente,
        "idUsuario": pedido.idUsuario,
        "unidadeId": pedido.idUnidade,
        "canalPedido": pedido.canalPedido,
        "status": pedido.status,
        "data_hora": pedido.data_hora.isoformat(),
        "valor_total": float(pedido.valor_total),
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

@router.patch("/{idPedido}/cancelar")
def cancelar_pedido(
    idPedido: int,
    conta=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    pedido = (
        db.query(Pedido)
        .filter(Pedido.idPedido == idPedido)
        .first()
    )

    if pedido is None:
        raise HTTPException(
            status_code=404,
            detail="Pedido não encontrado"
        )

    verificar_acesso_pedido(pedido, conta)

    if pedido.status not in ["PENDENTE", "AGUARDANDO"]:
        raise HTTPException(
            status_code=400,
            detail="Não é possível cancelar este pedido"
        )

    cozinha = (
        db.query(Cozinha)
        .filter(Cozinha.idPedido == idPedido)
        .first()
    )

    pedido.status = "CANCELADO"

    if cozinha:
        cozinha.status = "CANCELADO"

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "mensagem": "Pedido cancelado com sucesso",
        "idPedido": pedido.idPedido,
        "status": pedido.status
    }

@router.patch("/{idPedido}/entregar")
def iniciar_entrega(
    idPedido: int,
    conta=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    pedido = (
        db.query(Pedido)
        .filter(Pedido.idPedido == idPedido)
        .first()
    )

    if pedido is None:
        raise HTTPException(
            status_code=404,
            detail="Pedido não encontrado"
        )

    verificar_acesso_pedido(pedido, conta)

    if pedido.status != "PRONTO":
        raise HTTPException(
            status_code=400,
            detail="Somente pedidos prontos podem entrar em entrega"
        )

    pedido.status = "EM_ENTREGA"

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "mensagem": "Pedido saiu para entrega",
        "idPedido": pedido.idPedido,
        "status": pedido.status
    }