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
| Autenticação | Login e geração de token de acesso. |
| Usuários | Cadastro e consulta de perfil. |
| Unidades | Consulta das unidades da rede. |
| Produtos | Cadastro, consulta, atualização e desativação de produtos. |
| Estoque | Consulta de estoque e registro de entradas e saídas. |
| Pedidos | Criação, consulta, cancelamento e atualização de pedidos. |
| Cozinha | Acompanhamento e atualização do preparo dos pedidos. |
| Pagamentos | Gerenciamento do fluxo de pagamento simulado. |
| Fidelidade | Gerenciamento de pontos e resgates. |

O sistema também contempla regras de promoções e campanhas.

## 3. Estrutura do projeto

```text
Back-End_Raizes-Nordeste/
│
├── application/
│   ├── database.db
│   ├── seed.py
│   ├── migracao.py
│   │
│   └── app/
│       ├── main.py
│       ├── models.py
│       │
│       ├── api/
│       │   ├── security.py
│       │   ├── dependencies.py
│       │   ├── permissions.py
│       │   │
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
git clone URL_DO_REPOSITORIO
```

Acesse a pasta do projeto:

```bash
cd Back-End_Raizes-Nordeste
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

O projeto utiliza variáveis de ambiente para configurar a autenticação e a conexão com o banco de dados.

1. Na raiz do projeto, crie uma cópia do arquivo `.env.example`.
2. Renomeie a cópia para `.env`.
3. Confira as variáveis de configuração:

```env
SECRET_KEY=chave-temporaria-rede-raizes-trocar-depois
ALGORITHM=HS256
DATABASE_URL=sqlite:///./database.db
```

### 5.5. Preparar o banco de dados

A aplicação utiliza SQLite para persistência dos dados.

Os arquivos de preparação do banco e carga inicial estão disponíveis em:

- `application/migracao.py`
- `application/seed.py`

Execute os procedimentos de migração e carga inicial conforme a configuração do projeto.

### 5.6. Iniciar a API

Acesse a pasta `application`:

```bash
cd application
```

Inicie o servidor:

```bash
uvicorn app.main:app --reload
```

## 6. Documentação da API

A documentação interativa é disponibilizada automaticamente pelo FastAPI por meio do Swagger UI.

Acesse:

`http://127.0.0.1:8000/docs`

Também é possível consultar a documentação pelo ReDoc:

`http://127.0.0.1:8000/redoc`

## 7. Banco de dados

O projeto utiliza SQLite, com persistência dos dados em `application/database.db`.

O SQLAlchemy é utilizado para mapear as entidades e realizar as operações no banco de dados.

As principais entidades contemplam usuários, clientes, unidades, produtos, estoque, movimentações, pedidos, itens de pedido, cozinha, pagamentos e fidelidade.

## 8. Segurança

A API implementa mecanismos de segurança, incluindo:

- Autenticação por token JWT.
- Controle de acesso conforme o perfil do usuário.
- Armazenamento de senhas por hash.
- Validação dos dados recebidos.
- Padronização das respostas de erro.

## 9. Testes

Os testes da API serão organizados em uma coleção do Postman ou Insomnia, contemplando cenários positivos e negativos.

A coleção deverá incluir testes de autenticação, autorização, validação de dados e regras de negócio dos principais fluxos.

## 10. Observações

Este projeto foi desenvolvido como atividade prática da disciplina de Projeto Multidisciplinar – Trilha Back-End.

A integração de pagamentos representa um fluxo simulado (mock), sem realização de transações financeiras reais.

## 11. Repositório

**GitHub:** [https://github.com/b6ugawara/back-end-uninter]

