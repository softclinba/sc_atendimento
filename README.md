# SOFT Clinic — Sistema Web CRUD de Atendimento de Pacientes

Aplicação web **CRUD plenamente funcional** para gerenciamento de **pacientes**, **médicos**, **procedimentos** e **atendimentos**, com persistência real em SQLite, painel (dashboard), filtros e exportação dos atendimentos em **CSV** e **JSON**.

---

## Stack escolhida

| Camada     | Tecnologia                                    |
| ---------- | --------------------------------------------- |
| Backend    | Python 3.11+ / Flask                          |
| ORM        | SQLAlchemy (Flask-SQLAlchemy)                 |
| Banco      | SQLite (sandbox) / PostgreSQL (PRD)           |
| Migrações  | Alembic (Flask-Migrate)                       |
| Frontend   | Bootstrap 5, HTML5, CSS3, JavaScript          |
| Templates  | Jinja2                                        |
| Segurança  | Flask-Login, Flask-WTF (CSRF)                 |
| Produção   | uWSGI (PythonAnywhere)                        |
| Testes     | pytest                                        |

### Justificativa

- **Flask** — leve, simples, gratuito e open source; ideal para aplicações de pequeno/médio porte com evolução gradual.
- **SQLite no sandbox, PostgreSQL no PRD** — no desenvolvimento, arquivo único (`instance/app.db`) e backup trivial. Em produção, o disco do servidor web é efêmero e o SQLite não é recomendado; o PostgreSQL persiste e suporta concorrência de escrita. A troca é feita por `DATABASE_URL`.
- **SQLAlchemy ORM** — abstrai o banco, evita SQL espalhado pelas rotas e facilita a migração de banco.
- **Bootstrap 5** — interface limpa, profissional e responsiva (desktop e celular).
- **Flask-Login + Flask-WTF** — autenticação por sessão, senha com hash, proteção CSRF em todos os formulários.
- **Alembic** — versionamento do esquema; permite evoluir o banco sem perder dados, em vez de recriá-lo.
- **pytest** — testes automatizados simples e diretos.

Sobre o banco, ver [Ambientes](#ambientes): SQLite no sandbox, PostgreSQL no PRD.

---

## Requisitos

```
Python 3.11+
```

---

## Criação do ambiente

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

### Linux / macOS

```bash
python -m venv .venv
source .venv/bin/activate
```

---

## Instalação

```bash
pip install -r requirements.txt
```

Opcionalmente, crie um arquivo `.env` a partir de `.env.example` para definir a `SECRET_KEY` e a `DATABASE_URL`:

```bash
copy .env.example .env
```

---

## Configuração

As variáveis são lidas do `.env` e/ou do ambiente. Veja `.env.example`.

| Variável         | Default                                        | Descrição                                                       |
| ---------------- | ---------------------------------------------- | --------------------------------------------------------------- |
| `SECRET_KEY`     | chave de desenvolvimento                       | **Obrigatória em produção.** Assina os cookies de sessão.        |
| `FLASK_ENV`      | `development`                                  | Use `production` para ativar cookies `Secure` e exigir chave.   |
| `FLASK_DEBUG`    | `0`                                            | `1` liga o depurador (apenas em desenvolvimento).               |
| `DATABASE_URL`   | `sqlite:///instance/app.db`                    | URI do banco. `postgresql://` e `mysql://` são normalizadas.    |

> **Atenção:** a `SECRET_KEY` padrão é apenas um placeholder de desenvolvimento. Com `FLASK_ENV=production` a aplicação **recusa subir** sem uma `SECRET_KEY` real — quem compartilha essa chave consegue forjar sessões de qualquer usuário.

Gere uma chave real com:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Execução

```bash
python run.py
```

Acesse:

```
http://localhost:5000
```

Na primeira execução, o banco ainda não existe. Crie-o com as migrações:

```bash
flask --app wsgi:app db upgrade
flask --app wsgi:app seed
flask --app wsgi:app criar-usuario --nome "Administrador" --email admin@clinica.local --senha "TrocarEstaSenha123" --papel admin
```

Depois entre em `http://localhost:5000/login` com o usuário criado.

> `run.py` **não** cria tabelas nem executa seed ao subir. O esquema é responsabilidade do Alembic (`flask db upgrade`), e o seed é um comando explícito (`flask seed`).

---

## Autenticação e controle de acesso

Todas as telas e endpoints exigem usuário autenticado. Sem sessão ativa, o sistema redireciona para `/login`.

### Perfis

| Perfil       | Acesso                                                                        |
| ------------ | ----------------------------------------------------------------------------- |
| `admin`      | Tudo: médicos, procedimentos, pacientes, atendimentos, usuários, configurações. |
| `atendente`  | Pacientes e atendimentos (criar, editar, excluir). **Sem** médicos e procedimentos. |

### Rotas

| Rota            | Método     | Quem pode acessar      |
| --------------- | ---------- | --------------------- |
| `/login`        | GET, POST  | público                |
| `/logout`       | POST       | autenticado            |
| `/trocar-senha` | GET, POST  | autenticado            |
| `/usuarios/`    | GET, POST  | **somente admin**      |
| `/medicos/`     | GET        | autenticado            |
| `/medicos/novo`, `/editar`, `/excluir` | GET, POST | **somente admin** |
| `/procedimentos/` e sub-rotas de escrita | | **somente admin** |
| `/pacientes/`, `/atendimentos/` | | autenticado |

Na interface web, um usuário sem permissão é redirecionado ao painel com um aviso. Na API, a resposta é `403` em JSON.

### Senhas

- Armazenadas com hash (`werkzeug.security.generate_password_hash`). O texto puro nunca é gravado nem exibido.
- Tamanho mínimo de 8 caracteres.
- Ao trocar a senha, **todas** as sessões abertas do usuário caem e o token de API é revogado.

### Token de API

Para integrações e acesso via `curl`, um admin pode gerar um token em `/usuarios/` (ícone de chave).

```
Authorization: Bearer <token>
```

Características:

- O valor em claro aparece **uma única vez**, no momento em que é gerado. O banco guarda apenas o hash SHA-256.
- Gerar um novo token invalida o anterior.
- Revogar o token, desativar o usuário ou trocar a senha imediatamente derruba o acesso.
- Trate o token como senha pessoal: ele concede os mesmos poderes que o login do usuário.

---

## Banco de dados

### Localização

No sandbox, o banco SQLite fica em:

```
instance/app.db
```

No PRD, é o PostgreSQL do add-on, e a conexão vem da `DATABASE_URL`. Ver [Ambientes](#ambientes).

### Como é criado

O esquema é criado e alterado **exclusivamente** pelo Alembic:

```bash
flask --app wsgi:app db upgrade            # aplica as migrações pendentes
flask --app wsgi:app db current            # versão aplicada
flask --app wsgi:app db history            # histórico de migrações
flask --app wsgi:app db migrate -m "msg"   # gera migração após alterar models/
```

As migrações em `migrations/versions/` são:

| Revisão | Conteúdo                                    |
| ------- | ------------------------------------------- |
| `0001`  | Esquema inicial (médicos, procedimentos, pacientes, atendimentos) |
| `0002`  | Tabela `usuario`                            |

> Banco já existente criado antes do Alembic: use `flask db stamp 0001` para marcá-lo como versão 0001 sem recriar tabelas, depois `flask db upgrade`.

### Como o seed funciona

- **Médicos** iniciais: Nedy Neves, Marcela Souza, Vilane Dias, Juliana.
- **Procedimentos** iniciais (IDs preservados **101–105**): Consulta Particular, Lente de Contato, Teste Ortóptico, Exames, Outros.

> Os valores dos procedimentos são definidos na seção `PROCEDIMENTOS_INICIAIS` de `app/seed.py`. Os valores `0` são placeholders e devem ser ajustados conforme necessário.

O seed é **idempotente**: só insere registros que ainda não existem.

### Backup

Estas instruções são para o **SQLite do sandbox**, cujo banco é um arquivo único:

```bash
# Windows
copy instance\app.db instance\backup_2026-01-01.db

# Linux/macOS
cp instance/app.db instance/backup_2026-01-01.db
```

**Recomendação adicional:** para um backup consistente (sem dados pela metade durante uma gravação), faça a cópia com a aplicação preferencialmente parada, ou use o utilitário `sqlite3`:

```bash
sqlite3 instance/app.db ".backup instance/backup_2026-01-01.db"
```

No **PRD**, o backup é do PostgreSQL e precisa de `pg_dump` pelo console do PythonAnywhere. Como o banco não é acessível de fora da plataforma, a cópia fica no próprio servidor — mova para fora dele se quiser guardar em local permanente.

### Restauração

Para restaurar o SQLite, substitua o arquivo `instance/app.db` pelo backup desejado:

```bash
# Windows
copy instance\backup_2026-01-01.db instance\app.db

# Linux/macOS
cp instance/backup_2026-01-01.db instance/app.db
```

---

## Funcionamento do CRUD

- **Atendimentos:** criar, listar, visualizar, editar e excluir (com confirmação). Formulário com preenchimento automático do valor ao selecionar o procedimento.
- **Pacientes:** criar, listar, pesquisar, editar e excluir. Exclusão bloqueada quando há atendimentos relacionados.
- **Médicos:** criar, listar, pesquisar, editar e excluir. Exclusão bloqueada quando há atendimentos relacionados.
- **Procedimentos:** criar, listar, pesquisar, editar e excluir. Exclusão bloqueada quando há atendimentos relacionados. O valor é armazenado como número.

### Valor automático e histórico

Ao selecionar um procedimento no formulário de atendimento, o campo **Valor** é preenchido automaticamente com o valor cadastrado no procedimento. O usuário pode alterar manualmente.

O valor **efetivamente utilizado** é armazenado na tabela `Atendimento`, independentemente do valor atual do procedimento. Assim, se o preço de um procedimento mudar no futuro, os atendimentos antigos preservam o valor utilizado na época.

### Filtros

A tela de atendimentos filtra por paciente, médico, procedimento, forma de pagamento e intervalo de datas. Os filtros são aplicados **no banco de dados** (não em JavaScript).

---

## Exportação

- **CSV:** botão `Exportar CSV` — gera `atendimentos_AAAA-MM-DD.csv` em **UTF-8 with BOM** (compatível com Excel), com cabeçalho e caracteres acentuados preservados.
- **JSON:** botão `Exportar JSON` — gera `atendimentos_AAAA-MM-DD.json` em UTF-8, com `valor` como número e datas em ISO 8601.

**Requisito fundamental:** a exportação respeita os filtros atualmente aplicados na tela. Se nenhum filtro estiver aplicado, exporta todos os atendimentos.

### Endpoints de exportação

```text
GET /api/atendimentos/export/csv
GET /api/atendimentos/export/json
```

Exemplos:

```text
/api/atendimentos/export/csv?medico_id=1&data_inicio=2026-09-01&data_fim=2026-09-03
/api/atendimentos/export/json?medico_id=1&data_inicio=2026-09-01&data_fim=2026-09-03
```

A lógica de consulta é compartilhada (listagem, CSV e JSON) em `app/services/atendimento_service.py` — não há duplicação de código.

---

## API RESTful

API JSON dedicada sob prefixo `/api`. Todos os endpoints retornam JSON; erros de validação usam `400`, registro inexistente `404`, e exclusão de registro com atendimentos vinculados retorna `409` (para evitar registros órfãos).

### Autenticação

Todas as rotas exigem autenticação, **exceto** `GET /api/health`:

| Situação                              | Resposta                       |
| ------------------------------------- | ------------------------------ |
| Sem sessão e sem token                 | `401` `{"erro": "Autenticação necessária."}` |
| Autenticado, mas sem permissão de perfil | `403` `{"erro": "Permissão insuficiente."}` |

Envie o token no cabeçalho:

```
Authorization: Bearer <token>
```

Exemplo:

```bash
curl -H "Authorization: Bearer SEU_TOKEN" http://localhost:5000/api/pacientes
```

A API também aceita autenticação por sessão (cookie), o que faz o JavaScript do painel funcionar sem token.

### Permissões por perfil

| Recurso        | Leitura     | Escrita           |
| -------------- | ----------- | ----------------- |
| Pacientes      | todos       | todos             |
| Atendimentos   | todos       | todos             |
| Médicos        | todos       | **somente admin** |
| Procedimentos   | todos       | **somente admin** |

Verificação de disponibilidade (público, para monitoração):

```text
GET /api/health   ->  200 {"status": "ok"}
```

### Endpoints

```text
# Saúde (sem autenticação)
GET    /api/health

# Pacientes
GET    /api/pacientes              # listar
POST   /api/pacientes              # criar  { "nome": ... }
GET    /api/pacientes/<id>         # consultar
PUT    /api/pacientes/<id>         # editar  { "nome": ... }
DELETE /api/pacientes/<id>         # excluir (409 se houver atendimentos)

# Médicos
GET    /api/medicos
POST   /api/medicos                # { "nome": ... }
GET    /api/medicos/<id>
PUT    /api/medicos/<id>
DELETE /api/medicos/<id>           # 409 se houver atendimentos

# Procedimentos
GET    /api/procedimentos
POST   /api/procedimentos          # { "nome": ..., "valor": ... }
GET    /api/procedimentos/<id>
PUT    /api/procedimentos/<id>
DELETE /api/procedimentos/<id>     # 409 se houver atendimentos

# Atendimentos
GET    /api/atendimentos           # listar (com filtros opcionais)
POST   /api/atendimentos           # { "paciente_id", "medico_id", "procedimento_id",
                                   #   "data_atendimento", "valor", "forma_pagamento", ... }
GET    /api/atendimentos/<id>
PUT    /api/atendimentos/<id>
DELETE /api/atendimentos/<id>

# Exportação
GET    /api/atendimentos/export/csv
GET    /api/atendimentos/export/json
```

---

## Testes automatizados

```bash
pytest
```

Os testes rodam em SQLite com banco temporário, então passam rápido e não tocam o `instance/app.db`.

**98 testes, todos passando.** Cobrem:

| Arquivo                  | Foco                                                        |
| ------------------------ | ----------------------------------------------------------- |
| `test_pacientes.py`      | CRUD de pacientes e bloqueios                               |
| `test_medicos.py`        | CRUD de médicos                                              |
| `test_procedimentos.py`  | CRUD de procedimentos                                        |
| `test_atendimentos.py`   | CRUD, filtros, CSRF, valor histórico                        |
| `test_exportacao.py`     | CSV/JSON: estrutura, UTF-8, acentuação, filtros, valores     |
| `test_dashboard.py`      | Painel, agregações e portabilidade do SQL para PostgreSQL     |
| `test_api.py`            | Endpoints JSON, validações e `409`                           |
| `test_auth.py`           | Login, logout, perfis, token de API, troca de senha, bloqueio de `/usuarios/` |

O `conftest.py` cria o banco em disco temporário e oferece clientes prontos:

| Fixture            | Sessão                                     |
| ------------------ | ------------------------------------------ |
| `client`           | admin logado (padrão)                      |
| `client_anonimo`   | sem sessão, para testar bloqueios          |
| `client_atendente` | atendente logado (sem perfil admin)        |
| `client_api`       | token `Bearer` de admin no cabeçalho       |
| `token_api`        | token em texto claro, para testes de curl  |

---

## Estrutura de diretórios

```
Soft_Clinica/
├── app/
│   ├── __init__.py            # fábrica da app, blueprints, comandos CLI
│   ├── config.py              # Config, ProductionConfig, resolucao de env
│   ├── auth.py                # login_manager, guardas de sessão/token/admin
│   ├── database.py
│   ├── seed.py
│   ├── context_processors.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── usuario.py         # hash de senha, token de API
│   │   ├── paciente.py
│   │   ├── medico.py
│   │   ├── procedimento.py
│   │   └── atendimento.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── dashboard.py
│   │   ├── auth.py            # /login, /logout, /trocar-senha
│   │   ├── usuarios.py        # CRUD de usuarios (admin)
│   │   ├── pacientes.py
│   │   ├── medicos.py
│   │   ├── procedimentos.py
│   │   ├── atendimentos.py
│   │   └── api.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── atendimento_service.py
│   │   └── exportacao.py
│   ├── static/
│   │   ├── css/style.css
│   │   └── js/app.js
│   └── templates/
│       ├── base.html
│       ├── dashboard.html
│       ├── erros.html
│       ├── auth/{login,trocar_senha}.html
│       ├── usuarios/{lista,formulario}.html
│       ├── pacientes/{lista,formulario}.html
│       ├── medicos/{lista,formulario}.html
│       ├── procedimentos/{lista,formulario}.html
│       └── atendimentos/{lista,formulario,detalhes}.html
├── migrations/                # Alembic
│   ├── env.py
│   └── versions/
│       ├── 0001_schema_inicial.py
│       └── 0002_add_usuario.py
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_api.py
│   ├── test_dashboard.py
│   ├── test_atendimentos.py
│   ├── test_exportacao.py
│   ├── test_medicos.py
│   ├── test_pacientes.py
│   └── test_procedimentos.py
├── instance/
│   └── app.db            (criado por `flask db upgrade`)
├── run.py                 # desenvolvimento
├── wsgi.py                # entrada do web app (uWSGI no PythonAnywhere)
├── requirements.txt       # runtime
├── requirements-dev.txt   # runtime + testes
├── .env.example
└── README.md
```

---

## Ambientes

A aplicação roda em dois ambientes distintos. O código é o mesmo; muda o banco e as variáveis.

|                | Sandbox (local)               | PRD (PythonAnywhere)      |
| -------------- | ----------------------------- | ------------------------- |
| Banco          | SQLite `instance/app.db`      | PostgreSQL                |
| Servidor       | Flask dev (`python run.py`)  | uWSGI (gerenciado)        |
| Acesso         | `http://127.0.0.1:5000`       | HTTPS no seu domínio      |
| Cookies        | sem `Secure`                  | com `Secure`              |
| Dados          | arquivo local                 | banco do add-on           |

### Sandbox (local)

```powershell
.\.venv\Scripts\activate
pip install -r requirements-dev.txt
flask --app wsgi:app db upgrade
flask --app wsgi:app seed
flask --app wsgi:app criar-usuario --nome "Administrador" --email admin@clinica.local --senha "TrocarEstaSenha123" --papel admin
python run.py
```

O SQLite guarda o arquivo em `instance/app.db`, que está no `.gitignore`. Para backup, copie o arquivo com a aplicação parada (ver [Backup](#backup)).

---

### PRD — PythonAnywhere

O [PythonAnywhere](https://www.pythonanywhere.com/) hospeda o web app e o banco. **Ele não usa Docker nem gunicorn**: o web app roda sobre uWSGI, gerenciado pelo painel.

#### Antes de começar: o que exige upgrade

Estes passos só existem em **plano pago**. A conta gratuita não tem web app custom nem PostgreSQL.

1. **Contrate o plano.** Aba *Account* → *Customize your plan* → **Custom plan**. Ligue o add-on **Postgres** e escolha o espaço em disco. O Postgres não está no plano padrão.
2. **Crie o servidor de banco.** Aba *Databases* → botão *Postgres* → defina a senha de administrador. Anote: host, porta, nome do banco e usuário (o padrão é `usuario`).
3. **Crie o web app.** Aba *Web* → *Add a new web app* → **Manual configuration** (não escolha Flask, para você controlar o virtualenv). Escolha a versão do Python **3.12**.
4. **Crie o virtualenv.** Ainda na aba *Web*, em *Virtualenv*, marque a caixa e informe um nome, por exemplo `softclinica`. O caminho completo fica `/home/seu_usuario/.virtualenvs/softclinica`.

> Se sua conta estiver na branch europeia (`eu.pythonanywhere.com`), todos os caminhos seguem o mesmo padrão, com o prefixo `eu.` nos endereços.

#### Envie o código

Pelo console Bash:

```bash
cd ~
git clone <url-do-seu-repositorio> soft_clinica
cd soft_clinica
```

Se o repositório for privado, use uma chave de deploy. Não cole senha nem chave de API em comandos que fiquem no histórico do shell.

#### Instale as dependências

Sempre pelo console, com o virtualenv ativado:

```bash
source ~/.virtualenvs/softclinica/bin/activate
pip install -r requirements.txt
```

Use `requirements.txt`, não o `-dev.txt`: em produção não há necessidade de `pytest`.

#### Configure as variáveis de ambiente

Abra o console Bash e exporte, ou defina na seção de variáveis do painel:

| Variável       | Valor                                                    |
| -------------- | -------------------------------------------------------- |
| `FLASK_ENV`    | `production`                                             |
| `SECRET_KEY`   | chave aleatória (veja abaixo)                            |
| `DATABASE_URL` | `postgresql://usuario:SENHA@localhost:5432/soft_clinica` |

Gere a chave e **guarde o valor** em local seguro — sem ela, todas as sessões existentes caem:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

> A `DATABASE_URL` do PostgreSQL do PythonAnywhere só responde de dentro da plataforma. Ela não é acessível da sua máquina, o que impede acesso externo direto ao banco.

Se preferir não repetir esses valores no console, crie um `.env` no servidor (fora do git, já que `.env` está no `.gitignore`):

```
FLASK_ENV=production
SECRET_KEY=<a-chave-gerada>
DATABASE_URL=postgresql://usuario:SENHA@localhost:5432/soft_clinica
```

O `python-dotenv` já está nas dependências e o `app/config.py` lê o `.env` automaticamente.

#### Crie as tabelas

Ainda pelo console, com o virtualenv ativo:

```bash
flask --app wsgi:app db upgrade
flask --app wsgi:app seed
flask --app wsgi:app criar-usuario --nome "Administrador" --email admin@clinica.local --senha "TrocarEstaSenha123" --papel admin
```

`db upgrade` cria o esquema no PostgreSQL a partir das migrações. O seed é opcional e idempotente: serve para cadastrar médicos e procedimentos iniciais. O `criar-usuario` é obrigatório — sem ele não há como entrar no sistema, porque não existe usuário padrão.

O **PostgreSQL começa vazio**: os dados do SQLite local não são transferidos automaticamente. Se quiser recadastrar pacientes e atendimentos, use a interface após o primeiro acesso.

#### Configure o WSGI file

Aba *Web* → clique no link do **WSGI file** (algo como `/var/www/seu_usuario_pythonanywhere_com_wsgi.py`). **Substitua todo o conteúdo** por:

```python
import os
import sys

# Caminho do projeto no servidor.
project_path = '/home/seu_usuario/soft_clinica'
sys.path.insert(0, project_path)

# Se usar .env em vez de variaveis do painel:
# from dotenv import load_dotenv
# load_dotenv(os.path.join(project_path, '.env'))

os.environ.setdefault('FLASK_ENV', 'production')

from wsgi import app as application
```

Ajuste `seu_usuario` e o caminho. Salve e clique em **Reload**.

> O nome que o uWSGI procura é `application`. Por isso o `import ... as application` no final — não deixe como `app`.
>
> **Não** coloque a `SECRET_KEY` neste arquivo. Ele é editável pela interface web; mantenha o segredo nas variáveis do painel ou no `.env`.

#### Teste

Acesse `https://seu_usuario.pythonanywhere.com/login`. Se aparecer a tela de login, o deploy funcionou. Os erros ficam na aba *Web* → *Error log*.

#### Checklist do que foi e do que não foi verificado

**Verificado localmente** (98 testes passando, Python 3.12.10):

- autenticação, perfis e token de API;
- o guard de `/usuarios/` bloqueia anônimo e atendente;
- a aplicação recusa subir em produção sem `SECRET_KEY`;
- `DATABASE_URL` normaliza `postgresql://` para `postgresql+psycopg2://`;
- as consultas do dashboard geram SQL compatível com PostgreSQL (`EXTRACT`, não `strftime`).

**Não verificado:** nada foi executado no PythonAnywhere. Os passos acima seguem a documentação da plataforma, mas o deploy em si precisa ser feito e conferido por você. Em particular, não há garantia de que o web app suba na primeira tentativa — o *Error log* é o lugar para diagnosticar.

Pontos que exigem atenção no primeiro deploy:

- **Versão do Python**: os testes rodaram em 3.12.10. Se o painel oferecer outra versão, use a mesma.
- **`psycopg2-binary`** precisa ter wheel compatível com a versão do Python escolhida; se falhar, o erro aparece no `pip install`.
- **Cookie `Secure`**: ativo em produção. Se você testar por HTTP simples, o login não vai "colar" — use o domínio com HTTPS, que o PythonAnywhere fornece no plano pago.
- **PDF**: o `reportlab` gera o arquivo em memória, sem escrever em disco, então funciona no ambiente sem disco persistente.

---

### Por que PostgreSQL e não SQLite em produção

O PythonAnywhere não recomenda SQLite como banco de produção, e o disco do servidor web é efêmero: arquivos criados fora do repositório podem sumir em um restart do servidor. O PostgreSQL do add-on vive em armazenamento separado e persiste.

O código não depende do banco: as migrações e as consultas usam SQL padrão. O que **não** é portátil foi tratado em `app/routes/dashboard.py`, que agrupa o gráfico mensal com `extract()` em vez de `strftime()` — `strftime` é função do SQLite e quebraria em produção. Existe um teste que falha se alguém reintroduzir `func.strftime`.

---

## Limitações conhecidas

- Sem recuperação de senha por e-mail (a redefinição é feita por um admin na tela de usuários).
- Sem registro de auditoria: não há histórico de quem alterou ou excluiu cada registro.
- Valores dos procedimentos de seed definidos no código (`app/seed.py`); podem ser ajustados lá ou pela tela de procedimentos.
- Sem paginação nas listagens: consultas crescem com o volume de dados.
- Em SQLite a concorrência de escrita é limitada; em produção use PostgreSQL (ver [Ambientes](#ambientes)).
- O deploy no PythonAnywhere ainda não foi executado: o roteiro está escrito a partir da documentação da plataforma e ainda não validado em uma conta real.
- O PostgreSQL hospedado no PythonAnywhere não responde de fora da plataforma, então não dá para conectar um cliente SQL externo nem fazer backup direto pela rede.

---

## Sugestões de evolução futura

- Log de auditoria (usuário, data, ação, registro afetado).
- Recuperação de senha por e-mail e verificação de domínio.
- Perfis mais granulares (ex.: recepção, financeiro, médico).
- Relatórios adicionais e gráficos no dashboard.
- Exportação em outros formatos (XLSX, PDF).
- Paginação nas listagens.
- Interface de upload de plano de tratamento / anexos.
