from sqlalchemy import (
    Column, Integer, String, ForeignKey, DateTime,
    Numeric, Boolean, UniqueConstraint, CheckConstraint
)
from app.infrastructure.database.database import Base
from datetime import datetime, timezone

class Unidade(Base):
    __tablename__ = "tb_unidade"

    idUnidade = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    endereco = Column(String(255), nullable=False)

class Usuario(Base):
    __tablename__ = "tb_usuario"

    idUsuario = Column(Integer, primary_key=True, index=True)
    idUnidade = Column(Integer, ForeignKey("tb_unidade.idUnidade"))
    nome = Column(String(100), nullable=False)
    email = Column(String(150), nullable=False)
    senha = Column(String(255), nullable=False)
    tipo_usuario = Column(String(30), nullable=False)

class Produto(Base):
    __tablename__ = "tb_produto"

    idProduto = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    preco = Column(Numeric(10, 2), nullable=False)
    status = Column(String(30), nullable=False)

class Estoque(Base):
    __tablename__ = "tb_estoque"

    __table_args__ = (
        UniqueConstraint(
            "idUnidade",
            "idProduto",
            name="uq_estoque_unidade_produto"
        ),
        CheckConstraint(
            "quantidade >= 0",
            name="ck_estoque_quantidade"
        )
    )

    idEstoque = Column(Integer, primary_key=True, index=True)
    idUnidade = Column(Integer, ForeignKey("tb_unidade.idUnidade"), nullable=False)
    idProduto = Column(Integer, ForeignKey("tb_produto.idProduto"), nullable=False)
    quantidade = Column(Integer, nullable=False)

class Cliente(Base):
    __tablename__ = "tb_cliente"

    idCliente = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(150), nullable=False)
    telefone = Column(String(20))
    senha = Column(String(255), nullable=False)

class Pedido(Base):
    __tablename__ = "tb_pedido"

    idPedido = Column(Integer, primary_key=True, index=True)
    idCliente = Column(Integer, ForeignKey("tb_cliente.idCliente"))
    idUnidade = Column(Integer, ForeignKey("tb_unidade.idUnidade"))
    idUsuario = Column(Integer, ForeignKey("tb_usuario.idUsuario"))
    data_hora = Column(DateTime, nullable=False)
    status = Column(String(30), nullable=False)
    valor_total = Column(Numeric(10, 2), nullable=False)
    canalPedido = Column(String(30), nullable=False, default="PRESENCIAL")

class ItemPedido(Base):
    __tablename__ = "tb_item_pedido"

    idItemPedido = Column(Integer, primary_key=True, index=True)
    idPedido = Column(Integer, ForeignKey("tb_pedido.idPedido"))
    idProduto = Column(Integer, ForeignKey("tb_produto.idProduto"))
    quantidade = Column(Integer, nullable=False)
    preco_unitario = Column(Numeric(10, 2), nullable=False)

class Pagamento(Base):
    __tablename__ = "tb_pagamento"

    __table_args__ = (
        UniqueConstraint("idPedido", name="uq_pagamento_pedido"),
    )

    idPagamento = Column(Integer, primary_key=True, index=True)
    idPedido = Column(Integer, ForeignKey("tb_pedido.idPedido"), nullable=False)
    valor = Column(Numeric(10, 2), nullable=False)
    metodo_pagamento = Column(String(50), nullable=False)
    status = Column(String(30), nullable=False)
    codigo_transacao = Column(String(100))
    data_pagamento = Column(DateTime)

class Cozinha(Base):
    __tablename__ = "tb_cozinha"

    __table_args__ = (
        UniqueConstraint("idPedido", name="uq_cozinha_pedido"),
    )

    idCozinha = Column(Integer, primary_key=True, index=True)
    idPedido = Column(Integer, ForeignKey("tb_pedido.idPedido"), nullable=False)
    idUsuario = Column(Integer, ForeignKey("tb_usuario.idUsuario"))
    status = Column(String(30), nullable=False)
    hora_inicio = Column(DateTime)
    hora_conclusao = Column(DateTime)

class MovimentacaoEstoque(Base):
    __tablename__ = "tb_movimentacao_estoque"

    idMovimentacao = Column(Integer, primary_key=True, index=True)

    idEstoque = Column(
        Integer,
        ForeignKey("tb_estoque.idEstoque"),
        nullable=False
    )

    idUsuario = Column(
        Integer,
        ForeignKey("tb_usuario.idUsuario"),
        nullable=False
    )

    tipo = Column(String(10), nullable=False)
    quantidade = Column(Integer, nullable=False)

    data_hora = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )

    observacao = Column(String(255))
    
    __table_args__ = (
    CheckConstraint(
        "quantidade > 0",
        name="ck_movimentacao_estoque_quantidade"
    ),
)


class Fidelidade(Base):
    __tablename__ = "tb_fidelidade"

    idFidelidade = Column(Integer, primary_key=True, index=True)
    idCliente = Column(
        Integer,
        ForeignKey("tb_cliente.idCliente"),
        nullable=False,
        unique=True
    )
    saldo_pontos = Column(Integer, nullable=False, default=0)


class MovimentacaoFidelidade(Base):
    __tablename__ = "tb_movimentacao_fidelidade"

    idMovimentacao = Column(Integer, primary_key=True, index=True)

    idFidelidade = Column(
        Integer,
        ForeignKey("tb_fidelidade.idFidelidade"),
        nullable=False
    )

    idPedido = Column(
        Integer,
        ForeignKey("tb_pedido.idPedido"),
        nullable=True
    )

    tipo = Column(String(20), nullable=False)
    pontos = Column(Integer, nullable=False)
    descricao = Column(String(255))

    data_hora = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )


class ConsentimentoFidelidade(Base):
    __tablename__ = "tb_consentimento_fidelidade"

    idConsentimento = Column(Integer, primary_key=True, index=True)

    idCliente = Column(
        Integer,
        ForeignKey("tb_cliente.idCliente"),
        nullable=False,
        unique=True
    )

    aceito = Column(Boolean, nullable=False, default=False)
    data_aceite = Column(DateTime)
    data_revogacao = Column(DateTime)
