
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.infrastructure.database.database import get_db
from app.api.permissions import verificar_perfil
from app.models import (
    Estoque,
    Produto,
    Usuario,
    Unidade,
    MovimentacaoEstoque
)


router = APIRouter(prefix="/estoque", tags=["Estoque"])


class MovimentacaoRequest(BaseModel):
    idProduto: int
    unidadeId: int
    tipo: Literal["ENTRADA", "SAIDA"]
    quantidade: int = Field(gt=0)
    observacao: str | None = Field(default=None, max_length=255)


# Consultar estoque por unidade
@router.get("/")
def consultar_estoque(
    unidadeId: int,
    db: Session = Depends(get_db),
    conta=Depends(verificar_perfil("GERENTE"))
):
    unidade = db.query(Unidade).filter(
        Unidade.idUnidade == unidadeId
    ).first()

    if unidade is None:
        raise HTTPException(
            status_code=404,
            detail="Unidade não encontrada"
        )

    registros = (
        db.query(Estoque, Produto)
        .join(Produto, Estoque.idProduto == Produto.idProduto)
        .filter(Estoque.idUnidade == unidadeId)
        .all()
    )

    return [
        {
            "idEstoque": estoque.idEstoque,
            "idProduto": produto.idProduto,
            "nome": produto.nome,
            "quantidade": estoque.quantidade
        }
        for estoque, produto in registros
    ]


# Consultar histórico de movimentações
@router.get("/movimentacoes")
def consultar_movimentacoes(
    unidadeId: int | None = None,
    idProduto: int | None = None,
    tipo: Literal["ENTRADA", "SAIDA"] | None = None,
    db: Session = Depends(get_db),
    conta=Depends(verificar_perfil("GERENTE"))
):
    consulta = (
        db.query(
            MovimentacaoEstoque,
            Produto.nome,
            Estoque.idUnidade,
            Usuario.nome
        )
        .join(
            Estoque,
            MovimentacaoEstoque.idEstoque == Estoque.idEstoque
        )
        .join(
            Produto,
            Estoque.idProduto == Produto.idProduto
        )
        .join(
            Usuario,
            MovimentacaoEstoque.idUsuario == Usuario.idUsuario
        )
    )

    if unidadeId is not None:
        consulta = consulta.filter(Estoque.idUnidade == unidadeId)

    if idProduto is not None:
        consulta = consulta.filter(Estoque.idProduto == idProduto)

    if tipo is not None:
        consulta = consulta.filter(MovimentacaoEstoque.tipo == tipo)

    registros = consulta.order_by(
        MovimentacaoEstoque.data_hora.desc()
    ).all()

    return [
        {
            "idMovimentacao": movimento.idMovimentacao,
            "produto": nome_produto,
            "unidadeId": id_unidade,
            "funcionario": nome_usuario,
            "tipo": movimento.tipo,
            "quantidade": movimento.quantidade,
            "data_hora": movimento.data_hora.isoformat(),
            "observacao": movimento.observacao
        }
        for movimento, nome_produto, id_unidade, nome_usuario in registros
    ]


# Registrar entrada ou saída
@router.post("/movimentacoes")
def registrar_movimentacao(
    dados: MovimentacaoRequest,
    db: Session = Depends(get_db),
    conta=Depends(verificar_perfil("GERENTE"))
):
    unidade = db.query(Unidade).filter(
        Unidade.idUnidade == dados.unidadeId
    ).first()

    if unidade is None:
        raise HTTPException(
            status_code=404,
            detail="Unidade não encontrada"
        )

    produto = db.query(Produto).filter(
        Produto.idProduto == dados.idProduto
    ).first()

    if produto is None:
        raise HTTPException(
            status_code=404,
            detail="Produto não encontrado"
        )

    if produto.status != "ATIVO":
        raise HTTPException(
            status_code=400,
            detail="Não é possível movimentar o estoque de um produto inativo"
        )

    estoque = db.query(Estoque).filter(
        Estoque.idProduto == dados.idProduto,
        Estoque.idUnidade == dados.unidadeId
    ).first()

    if estoque is None:
        raise HTTPException(
            status_code=404,
            detail="Produto não encontrado no estoque desta unidade"
        )

    if dados.tipo == "ENTRADA":
        estoque.quantidade += dados.quantidade

    else:
        if dados.quantidade > estoque.quantidade:
            raise HTTPException(
                status_code=400,
                detail="Quantidade de saída maior que o estoque disponível"
            )

        estoque.quantidade -= dados.quantidade

    movimentacao = MovimentacaoEstoque(
        idEstoque=estoque.idEstoque,
        idUsuario=conta.idUsuario,
        tipo=dados.tipo,
        quantidade=dados.quantidade,
        observacao=dados.observacao
    )

    db.add(movimentacao)
    db.commit()
    db.refresh(movimentacao)

    return {
        "mensagem": "Movimentação registrada com sucesso",
        "idMovimentacao": movimentacao.idMovimentacao,
        "idProduto": dados.idProduto,
        "unidadeId": dados.unidadeId,
        "quantidade_atual": estoque.quantidade
    }
