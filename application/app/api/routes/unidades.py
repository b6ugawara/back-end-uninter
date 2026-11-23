from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.infrastructure.database.database import get_db
from app.api.dependencies import get_current_user
from app.models import Unidade


router = APIRouter(prefix="/unidades", tags=["Unidades"])


@router.get("/")
def listar_unidades(
    conta=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    unidades = db.query(Unidade).all()

    return [
        {
            "idUnidade": unidade.idUnidade,
            "nome": unidade.nome,
            "endereco": unidade.endereco
        }
        for unidade in unidades
    ]
