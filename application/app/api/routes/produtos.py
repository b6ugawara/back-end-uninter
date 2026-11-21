
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from decimal import Decimal

from app.infrastructure.database.database import get_db
from app.api.permissions import verificar_perfil
from app.models import Produto, Estoque


router = APIRouter(prefix="/produtos", tags=["Produtos"])


class ProdutoRequest(BaseModel):
    nome: str
    preco: Decimal = Field(gt=0)
    status: str = "ATIVO"


class ProdutoAtualizacao(BaseModel):
    nome: str | None = None
    preco: Decimal | None = Field(default=None, gt=0)
    status: str | None = None


# Listar produtos de uma unidade
@router.get("/")
def listar_produtos(
    unidadeId: int,
    db: Session = Depends(get_db),
    conta=Depends(verificar_perfil("ATENDENTE", "GERENTE"))
):
    produtos = (
        db.query(Produto, Estoque.quantidade)
        .join(Estoque, Estoque.idProduto == Produto.idProduto)
        .filter(Estoque.idUnidade == unidadeId)
        .filter(Produto.status != "INATIVO")
        .all()
    )

    return [
        {
            "idProduto": produto.idProduto,
            "nome": produto.nome,
            "preco": float(produto.preco),
            "status": produto.status,
            "quantidade_estoque": quantidade
        }
        for produto, quantidade in produtos
    ]


# Consultar produto por ID
@router.get("/{id}")
def consultar_produto(
    id: int,
    db: Session = Depends(get_db),
    conta=Depends(verificar_perfil("ATENDENTE", "GERENTE"))
):
    produto = db.query(Produto).filter(
        Produto.idProduto == id
    ).first()

    if produto is None or produto.status == "INATIVO":
        raise HTTPException(
            status_code=404,
            detail="Produto não encontrado"
        )

    return {
        "idProduto": produto.idProduto,
        "nome": produto.nome,
        "preco": float(produto.preco),
        "status": produto.status
    }


# Cadastrar produto
@router.post("/")
def cadastrar_produto(
    dados: ProdutoRequest,
    db: Session = Depends(get_db),
    conta=Depends(verificar_perfil("GERENTE"))
):
    novo_produto = Produto(
        nome=dados.nome,
        preco=dados.preco,
        status=dados.status
    )

    db.add(novo_produto)
    db.commit()
    db.refresh(novo_produto)

    return {
        "mensagem": "Produto cadastrado com sucesso",
        "idProduto": novo_produto.idProduto
    }


# Atualizar produto
@router.patch("/{id}")
def atualizar_produto(
    id: int,
    dados: ProdutoAtualizacao,
    db: Session = Depends(get_db),
    conta=Depends(verificar_perfil("GERENTE"))
):
    produto = db.query(Produto).filter(
        Produto.idProduto == id
    ).first()

    if produto is None or produto.status == "INATIVO":
        raise HTTPException(
            status_code=404,
            detail="Produto não encontrado"
        )

    atualizacoes = dados.model_dump(exclude_unset=True)

    for campo, valor in atualizacoes.items():
        setattr(produto, campo, valor)

    db.commit()
    db.refresh(produto)

    return {
        "mensagem": "Produto atualizado com sucesso",
        "idProduto": produto.idProduto
    }


# Excluir produto
@router.delete("/{id}")
def excluir_produto(
    id: int,
    db: Session = Depends(get_db),
    conta=Depends(verificar_perfil("GERENTE"))
):
    produto = db.query(Produto).filter(
        Produto.idProduto == id
    ).first()

    if produto is None or produto.status == "INATIVO":
        raise HTTPException(
            status_code=404,
            detail="Produto não encontrado"
        )

    # Exclusão lógica para preservar relacionamentos existentes
    produto.status = "INATIVO"

    db.commit()

    return {
        "mensagem": "Produto excluído com sucesso"
    }
