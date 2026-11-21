from fastapi import FastAPI

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

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Rede Raízes do Nordeste",
    description="API de gerenciamento da rede de lanchonetes",
    version="1.0.0"
)

app.include_router(auth_router)
app.include_router(usuarios_router)
app.include_router(unidades_router)
app.include_router(produtos_router)
app.include_router(estoque_router)
app.include_router(pedidos_router)
app.include_router(cozinha_router)
app.include_router(pagamentos_router)

@app.get("/")
def inicio():
    return {
        "mensagem": "API funcionando!"
    }
