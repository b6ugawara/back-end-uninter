
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from passlib.context import CryptContext

from app.infrastructure.database.database import get_db
from app.api.dependencies import (
    get_current_user,
    get_optional_current_user
)
from app.models import Usuario, Cliente


router = APIRouter(prefix="/usuarios", tags=["Usuários"])

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


class CadastroRequest(BaseModel):
    nome: str
    email: str
    senha: str = Field(min_length=8)
    telefone: str | None = None
    tipo_usuario: str | None = None
    idUnidade: int | None = None


@router.post("/cadastrar")
def cadastrar(
    dados: CadastroRequest,
    db: Session = Depends(get_db),
    usuario_logado=Depends(get_optional_current_user)
):
    usuario_existente = db.query(Usuario).filter(
        Usuario.email == dados.email
    ).first()

    cliente_existente = db.query(Cliente).filter(
        Cliente.email == dados.email
    ).first()

    if usuario_existente or cliente_existente:
        raise HTTPException(
            status_code=409,
            detail="E-mail já cadastrado"
        )

    senha_hash = pwd_context.hash(dados.senha)

    # Cadastro público: cria somente clientes
    if usuario_logado is None:
        novo_cliente = Cliente(
            nome=dados.nome,
            email=dados.email,
            telefone=dados.telefone,
            senha=senha_hash
        )

        db.add(novo_cliente)
        db.commit()
        db.refresh(novo_cliente)

        return {
            "mensagem": "Cliente cadastrado com sucesso",
            "id": novo_cliente.idCliente,
            "perfil": "CLIENTE"
        }

    # Cliente autenticado não pode cadastrar funcionários
    if isinstance(usuario_logado, Cliente):
        raise HTTPException(
            status_code=403,
            detail="Clientes não podem cadastrar funcionários"
        )

    # Somente gerente pode cadastrar funcionários
    if usuario_logado.tipo_usuario != "GERENTE":
        raise HTTPException(
            status_code=403,
            detail="Somente o gerente pode cadastrar funcionários"
        )

    perfis_permitidos = [
        "GERENTE",
        "ATENDENTE",
        "COZINHA"
    ]

    if dados.tipo_usuario not in perfis_permitidos:
        raise HTTPException(
            status_code=400,
            detail="Perfil de funcionário inválido"
        )

    novo_usuario = Usuario(
        nome=dados.nome,
        email=dados.email,
        senha=senha_hash,
        tipo_usuario=dados.tipo_usuario,
        idUnidade=dados.idUnidade
    )

    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)

    return {
        "mensagem": "Funcionário cadastrado com sucesso",
        "id": novo_usuario.idUsuario,
        "perfil": novo_usuario.tipo_usuario
    }


@router.get("/perfil")
def consultar_perfil(
    conta=Depends(get_current_user)
):
    if isinstance(conta, Cliente):
        return {
            "id": conta.idCliente,
            "nome": conta.nome,
            "email": conta.email,
            "telefone": conta.telefone,
            "perfil": "CLIENTE"
        }

    return {
        "id": conta.idUsuario,
        "nome": conta.nome,
        "email": conta.email,
        "idUnidade": conta.idUnidade,
        "perfil": conta.tipo_usuario
    }
