
import sqlite3

conn = sqlite3.connect("database.db")

try:
    conn.execute("BEGIN")

    conn.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_pagamento_codigo_transacao
        ON tb_pagamento (codigo_transacao)
        WHERE codigo_transacao IS NOT NULL
    """)

    conn.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_fidelidade_credito_pedido
        ON tb_movimentacao_fidelidade (idPedido)
        WHERE tipo = 'CREDITO' AND idPedido IS NOT NULL
    """)

    conn.commit()
    print("Migração de fidelidade concluída com sucesso!")

except Exception as erro:
    conn.rollback()
    print("Erro na migração:", erro)

finally:
    conn.close()
