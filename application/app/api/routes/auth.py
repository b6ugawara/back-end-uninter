
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from jose import jwt
from passlib.context import CryptContext

from app.config import SECRET_KEY, ALGORITHM
from app.infrastructure.database.database import get_db
from app.models import Usuario, Cliente


router = APIRouter(prefix="/auth", tags=["Autenticação"])

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

ACCESS_TOKEN_EXPIRE_MINUTES = 60

class LoginRequest(BaseModel):
    email: str
    senha: str


def criar_token(id_conta, email, perfil, entidade):
    expiracao = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    dados_token = {
        "sub": str(id_conta),
        "email": email,
        "perfil": perfil,
        "entidade": entidade,
        "exp": expiracao
    }

    return jwt.encode(
        dados_token,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


@router.post("/login")
def login(
    dados: LoginRequest,
    db: Session = Depends(get_db)
):
    usuario = db.query(Usuario).filter(
        Usuario.email == dados.email
    ).first()

    cliente = None

    if usuario is None:
        cliente = db.query(Cliente).filter(
            Cliente.email == dados.email
        ).first()

    conta = usuario or cliente

    if conta is None or not conta.senha:
        raise HTTPException(
            status_code=401,
            detail="E-mail ou senha inválidos"
        )

    if not pwd_context.verify(dados.senha, conta.senha):
        raise HTTPException(
            status_code=401,
            detail="E-mail ou senha inválidos"
        )

    if usuario is not None:
        id_conta = usuario.idUsuario
        perfil = usuario.tipo_usuario
        entidade = "usuario"
    else:
        id_conta = cliente.idCliente
        perfil = "CLIENTE"
        entidade = "cliente"

    token = criar_token(
        id_conta,
        conta.email,
        perfil,
        entidade
    )

    return {
        "mensagem": "Login realizado com sucesso",
        "access_token": token,
        "token_type": "bearer",
        "usuario": {
            "id": id_conta,
            "nome": conta.nome,
            "email": conta.email,
            "perfil": perfil
        }
    }


@router.post("/logout")
def logout():
    return {
        "mensagem": "Logout solicitado. Descarte o token de acesso no cliente."
    }
