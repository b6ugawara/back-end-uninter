from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app import models
from app.infrastructure.database.database import Base, engine

from app.api.routes.auth import router as auth_router
from app.api.routes.usuarios import router as usuarios_router
from app.api.routes.unidades import router as unidades_router
from app.api.routes.produtos import router as produtos_router
from app.api.routes.estoque import router as estoque_router
from app.api.routes.pedidos import router as pedidos_router
from app.api.routes.cozinha import router as cozinha_router
from app.api.routes.pagamentos import router as pagamentos_router
from app.api.routes.fidelidade import router as fidelidade_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Rede Raízes do Nordeste",
    description="API de gerenciamento da rede de lanchonetes",
    version="1.0.0"
)


# Tratamento padronizado de HTTPException
@app.exception_handler(HTTPException)
async def tratar_http_exception(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "erro": {
                "codigo": exc.status_code,
                "mensagem": str(exc.detail)
            }
        },
        headers=exc.headers
    )


# Tratamento padronizado de erros de validação (422)
@app.exception_handler(RequestValidationError)
async def tratar_erro_validacao(
    request: Request,
    exc: RequestValidationError
):
    erros = []

    for erro in exc.errors():
        erros.append({
            "campo": ".".join(str(item) for item in erro["loc"]),
            "mensagem": erro["msg"]
        })

    return JSONResponse(
        status_code=422,
        content={
            "erro": {
                "codigo": 422,
                "mensagem": "Dados enviados inválidos ou incompletos",
                "detalhes": erros
            }
        }
    )


# Tratamento padronizado de erros inesperados (500)
@app.exception_handler(Exception)
async def tratar_erro_interno(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "erro": {
                "codigo": 500,
                "mensagem": "Erro interno do servidor"
            }
        }
    )

app.include_router(auth_router)
app.include_router(usuarios_router)
app.include_router(unidades_router)
app.include_router(produtos_router)
app.include_router(estoque_router)
app.include_router(pedidos_router)
app.include_router(cozinha_router)
app.include_router(pagamentos_router)
app.include_router(fidelidade_router)

@app.get("/")
def inicio():
    return {
        "mensagem": "API funcionando!"
    }
