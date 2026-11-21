from datetime import datetime
from decimal import Decimal

from passlib.context import CryptContext

from app.infrastructure.database.database import SessionLocal
from app.models import (
    Unidade,
    Usuario,
    Cliente,
    Produto,
    Estoque,
    Pedido,
    ItemPedido,
    Pagamento,
    Cozinha
)

# Criptografia das senhas de teste
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

db = SessionLocal()

try:
    # Previne a inserção de dados repetidos
    unidade_existente = db.query(Unidade).filter_by(
        nome="Unidade Centro"
    ).first()

    if unidade_existente:
        print("Os dados de teste já foram inseridos.")
    else:

        # 1. UNIDADE
        unidade = Unidade(
            nome="Unidade Centro",
            endereco="Rua das Flores, 100 - Recife/PE"
        )
        db.add(unidade)
        db.flush()

        # 2. USUÁRIOS
        gerente = Usuario(
            idUnidade=unidade.idUnidade,
            nome="Carlos Silva",
            email="gerente@raizes.com",
            senha=pwd_context.hash("Senha123!"),
            tipo_usuario="GERENTE"
        )

        atendente = Usuario(
            idUnidade=unidade.idUnidade,
            nome="Maria Souza",
            email="atendente@raizes.com",
            senha=pwd_context.hash("Senha123!"),
            tipo_usuario="ATENDENTE"
        )

        cozinha = Usuario(
            idUnidade=unidade.idUnidade,
            nome="João Santos",
            email="cozinha@raizes.com",
            senha=pwd_context.hash("Senha123!"),
            tipo_usuario="COZINHA"
        )

        db.add_all([gerente, atendente, cozinha])
        db.flush()

        # 3. CLIENTE
        cliente = Cliente(
            nome="Ana Oliveira",
            email="ana@email.com",
            telefone="81999999999"
        )
        db.add(cliente)
        db.flush()

        # 4. PRODUTOS
        coxinha = Produto(
            nome="Coxinha de Frango",
            preco=Decimal("8.50"),
            status="ATIVO"
        )

        tapioca = Produto(
            nome="Tapioca de Queijo",
            preco=Decimal("12.00"),
            status="ATIVO"
        )

        suco = Produto(
            nome="Suco de Acerola",
            preco=Decimal("6.00"),
            status="ATIVO"
        )

        db.add_all([coxinha, tapioca, suco])
        db.flush()

        # 5. ESTOQUE
        estoques = [
            Estoque(
                idUnidade=unidade.idUnidade,
                idProduto=coxinha.idProduto,
                quantidade=50
            ),
            Estoque(
                idUnidade=unidade.idUnidade,
                idProduto=tapioca.idProduto,
                quantidade=30
            ),
            Estoque(
                idUnidade=unidade.idUnidade,
                idProduto=suco.idProduto,
                quantidade=40
            )
        ]

        db.add_all(estoques)
        db.flush()

        # 6. PEDIDO
        pedido = Pedido(
            idCliente=cliente.idCliente,
            idUnidade=unidade.idUnidade,
            idUsuario=atendente.idUsuario,
            data_hora=datetime.now(),
            status="EM_PREPARO",
            valor_total=Decimal("20.50")
        )

        db.add(pedido)
        db.flush()

        # 7. ITENS DO PEDIDO
        itens = [
            ItemPedido(
                idPedido=pedido.idPedido,
                idProduto=coxinha.idProduto,
                quantidade=1,
                preco_unitario=Decimal("8.50")
            ),
            ItemPedido(
                idPedido=pedido.idPedido,
                idProduto=tapioca.idProduto,
                quantidade=1,
                preco_unitario=Decimal("12.00")
            )
        ]

        db.add_all(itens)
        db.flush()

        # 8. PAGAMENTO
        pagamento = Pagamento(
            idPedido=pedido.idPedido,
            valor=Decimal("20.50"),
            metodo_pagamento="PIX",
            status="APROVADO",
            codigo_transacao="TESTE-001",
            data_pagamento=datetime.now()
        )

        db.add(pagamento)
        db.flush()

        # 9. COZINHA
        registro_cozinha = Cozinha(
            idPedido=pedido.idPedido,
            idUsuario=cozinha.idUsuario,
            status="EM_PREPARO",
            hora_inicio=datetime.now(),
            hora_conclusao=None
        )

        db.add(registro_cozinha)

        # Salva tudo no banco
        db.commit()

        print("Dados de teste inseridos com sucesso!")
        print(f"Unidade: {unidade.idUnidade}")
        print(f"Pedido: {pedido.idPedido}")
        print(f"Cliente: {cliente.nome}")

except Exception as erro:
    db.rollback()
    print("Erro ao inserir dados:", erro)

finally:
    db.close()
