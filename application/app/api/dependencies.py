
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.api.security import SECRET_KEY, ALGORITHM
from app.infrastructure.database.database import get_db
from app.models import Usuario, Cliente


bearer_scheme = HTTPBearer()
bearer_scheme_optional = HTTPBearer(auto_error=False)


def buscar_conta(payload, db: Session):
    conta_id = payload.get("sub")
    entidade = payload.get("entidade")

    if conta_id is None:
        return None

    try:
        conta_id = int(conta_id)
    except (ValueError, TypeError):
        return None

    if entidade == "usuario":
        return db.query(Usuario).filter(
            Usuario.idUsuario == conta_id
        ).first()

    if entidade == "cliente":
        return db.query(Cliente).filter(
            Cliente.idCliente == conta_id
        ).first()

    return None


def decodificar_token(token: str):
    try:
        return jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
    except JWTError:
        return None


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
):
    credenciais_invalidas = HTTPException(
        status_code=401,
        detail="Token inválido ou expirado",
        headers={"WWW-Authenticate": "Bearer"}
    )

    payload = decodificar_token(credentials.credentials)

    if payload is None:
        raise credenciais_invalidas

    conta = buscar_conta(payload, db)

    if conta is None:
        raise credenciais_invalidas

    return conta


def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme_optional
    ),
    db: Session = Depends(get_db)
):
    if credentials is None:
        return None

    payload = decodificar_token(credentials.credentials)

    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Token inválido ou expirado"
        )

    conta = buscar_conta(payload, db)

    if conta is None:
        raise HTTPException(
            status_code=401,
            detail="Token inválido ou expirado"
        )

    return conta
