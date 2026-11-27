# Rede Raízes do Nordeste – API Backend

API REST desenvolvida em Python com FastAPI para gerenciamento de uma rede de lanchonetes. O sistema contempla o gerenciamento de usuários, unidades, produtos, estoque, pedidos, cozinha, pagamentos e fidelidade.

## 1. Tecnologias utilizadas

- **Python** – linguagem de programação.
- **FastAPI** – desenvolvimento da API REST.
- **SQLAlchemy** – ORM para comunicação com o banco de dados.
- **SQLite** – banco de dados relacional.
- **Pydantic** – validação dos dados de entrada.
- **JWT** – autenticação e controle de acesso.
- **Passlib e bcrypt** – hash e verificação de senhas.
- **Uvicorn** – servidor ASGI para execução da aplicação.

## 2. Funcionalidades

A API possui os seguintes módulos:

| Módulo | Funcionalidade |
|---|---|
| Autenticação | Login e geração de token de acesso JWT. |
| Usuários | Cadastro, consulta e gerenciamento de usuários e perfis. |
| Unidades | Consulta e gerenciamento das unidades da rede. |
| Produtos | Cadastro, consulta, atualização e desativação de produtos. |
| Estoque | Consulta de estoque e registro de entradas e saídas. |
| Pedidos | Criação, consulta, cancelamento e acompanhamento de pedidos. |
| Cozinha | Consulta da fila de pedidos e atualização dos status de preparação. |
| Pagamentos | Registro, consulta e processamento de pagamentos por meio de integração simulada com webhook. |
| Fidelidade | Consulta de saldo, histórico de movimentações, gerenciamento de consentimento e resgate de pontos. |

O sistema também contempla regras de promoções e campanhas.

### 2.1. Pagamentos

O módulo de pagamentos permite registrar e acompanhar os pagamentos associados aos pedidos.

Principais funcionalidades:

- Registro de pagamentos com os métodos PIX, cartão de crédito, cartão de débito e dinheiro.
- Geração automática de código único de transação.
- Inicialização do pagamento com status PENDENTE.
- Consulta dos dados de pagamento associados a um pedido.
- Recebimento de confirmações por meio de webhook.
- Validação de autenticação do webhook por segredo compartilhado.
- Atualização do pedido conforme o resultado do pagamento.
- Criação automática de registro na fila da cozinha após aprovação.

A integração utiliza um fluxo simulado, sem realização de transações financeiras reais.

### 2.2. Programa de fidelidade

O módulo de fidelidade permite que os clientes acumulem e utilizem pontos conforme as regras implementadas no sistema.

Principais funcionalidades:

- Consulta do saldo atual de pontos.
- Consulta do histórico de créditos e resgates.
- Registro de consentimento para participação no programa.
- Revogação do consentimento.
- Crédito automático de pontos após a aprovação de pagamentos, quando o cliente possui consentimento ativo.
- Resgate de pontos para obtenção de descontos.

**Regra de conversão:** 100 pontos equivalem a R$ 1,00 de desconto.

O sistema registra as movimentações de crédito e resgate, mantendo o histórico das operações.

## 3. Estrutura do projeto

```text
Back-End_Raizes-Nordeste/
│
├── application/
│   ├── database.db
│   └── app/
│       ├── main.py
│       │
│       ├── api/
│       │   ├── security.py
│       │   ├── dependencies.py
│       │   ├── permissions.py
│       │   └── routes/
│       │       ├── auth.py
│       │       ├── usuarios.py
│       │       ├── unidades.py
│       │       ├── produtos.py
│       │       ├── estoque.py
│       │       ├── pedidos.py
│       │       ├── cozinha.py
│       │       ├── pagamentos.py
│       │       └── fidelidade.py
│       │
│       └── infrastructure/
│           └── database/
│               └── database.py
│
├── .env.example
├── requirements.txt
└── README.md
```

## 4. Requisitos para execução

- Python 3.10 ou superior.
- pip.
- Git.
- Editor de código, como Visual Studio Code.

## 5. Como executar o projeto

### 5.1. Clonar o repositório

```bash
git clone https://github.com/b6ugawara/back-end-uninter
```

Acesse a pasta do projeto:

```bash
cd back-end-uninter
```

### 5.2. Criar e ativar o ambiente virtual

No Windows, execute:

```powershell
python -m venv .venv
```

Ative o ambiente virtual:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 5.3. Instalar as dependências

```bash
pip install -r requirements.txt
```

### 5.4. Configurar as variáveis de ambiente

O projeto utiliza variáveis de ambiente para configurar parâmetros de segurança e integração.

1. Na raiz do projeto, crie uma cópia do arquivo `.env.example`.
2. Renomeie a cópia para `.env`.
3. Preencha os valores necessários conforme as configurações utilizadas pela aplicação.

Não compartilhe o arquivo `.env` nem publique chaves e segredos no repositório.

### 5.5. Preparar o banco de dados

A aplicação utiliza SQLite para persistência dos dados.

O SQLAlchemy é responsável pelo mapeamento das entidades e pela comunicação com o banco de dados.

As tabelas são inicializadas pela aplicação por meio da configuração do banco de dados e da criação das estruturas definidas nos modelos.

O arquivo do banco de dados utilizado pelo projeto é:

```text
application/database.db
```

### 5.6. Iniciar a API

Acesse a pasta `application`:

```bash
cd application
```

Inicie o servidor:

```bash
uvicorn app.main:app --reload
```

Após a inicialização, a API estará disponível em:

```text
http://127.0.0.1:8000
```

## 6. Documentação da API

A documentação interativa é disponibilizada automaticamente pelo FastAPI por meio do Swagger UI.

**Swagger UI:**

http://127.0.0.1:8000/docs

**ReDoc:**

http://127.0.0.1:8000/redoc

A documentação permite visualizar os endpoints implementados, seus parâmetros, modelos de requisição e respostas, além de possibilitar a execução de operações diretamente pela interface.

## 7. Banco de dados

O projeto utiliza SQLite, com persistência dos dados em `application/database.db`.

O SQLAlchemy é utilizado como ORM para mapear as entidades e realizar as operações no banco de dados.

As principais entidades contemplam:

- Usuários e clientes.
- Unidades.
- Produtos.
- Estoque e movimentações de estoque.
- Pedidos e itens de pedido.
- Cozinha.
- Pagamentos.
- Fidelidade.
- Movimentações de fidelidade.
- Consentimentos de fidelidade.

As operações que envolvem múltiplas alterações relacionadas utilizam transações no banco de dados, permitindo confirmar ou reverter as alterações em caso de falha.

## 8. Segurança

A API implementa mecanismos de segurança, incluindo:

- Autenticação por token JWT.
- Controle de acesso conforme o perfil do usuário.
- Armazenamento de senhas por hash.
- Validação dos dados recebidos por meio do Pydantic.
- Verificação de permissões para operações protegidas.
- Validação do segredo compartilhado nas requisições do webhook de pagamento.
- Controle de acesso aos dados de clientes autenticados.
- Tratamento de conflitos e operações duplicadas.

## 9. Testes

Os testes da API são realizados por meio do Postman ou Insomnia, utilizando uma coleção organizada por módulos.

Os cenários contemplam testes positivos e negativos, incluindo:

- Autenticação e geração de token.
- Cadastro e consulta de usuários.
- Controle de permissões por perfil.
- Consulta e gerenciamento de produtos e estoque.
- Criação, consulta e cancelamento de pedidos.
- Acompanhamento dos pedidos na cozinha.
- Registro e consulta de pagamentos.
- Aprovação e recusa de pagamentos por webhook.
- Validação de pagamentos duplicados.
- Consulta de saldo e histórico de fidelidade.
- Aceite e revogação de consentimento.
- Resgate de pontos e validação de saldo insuficiente.

Os testes devem respeitar os fluxos principais do sistema, utilizando os dados e identificadores retornados pelas operações anteriores.

## 10. Observações

A integração de pagamentos representa um fluxo simulado (mock), sem realização de transações financeiras reais.

O programa de fidelidade contempla o controle de consentimento do cliente e resgate de pontos.

Existem credenciais já criadas para função de testes:

Cliente:
```
{
"email": "marcelosantos@email.com",
"senha": "M@rceloTeste"
}
```
Atendente:
```
{
"email": "atendente@raizes.com",
"senha": "Senha123!"
}
```
Cozinha:
```
{
"email": "cozinha@raizes.com",
"senha": "Senha123!"
}
```
Gerente:
```
{
"email": "gerente@raizes.com",
"senha": "Senha123!
}
```
## 11. Repositório

**GitHub:**

https://github.com/b6ugawara/back-end-uninter