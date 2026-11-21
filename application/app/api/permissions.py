
from fastapi import Depends, HTTPException, status

from app.api.dependencies import get_current_user
from app.models import Cliente, Usuario


def verificar_perfil(*perfis_permitidos):
    def permissao(conta=Depends(get_current_user)):

        if isinstance(conta, Cliente):
            perfil = "CLIENTE"

        elif isinstance(conta, Usuario):
            perfil = conta.tipo_usuario

        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Perfil não reconhecido"
            )

        if perfil not in perfis_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não tem permissão para acessar este recurso"
            )

        return conta

    return permissao
