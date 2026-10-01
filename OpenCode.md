# PROMPT — Sistema Web CRUD de Atendimento de Pacientes

Você é um desenvolvedor **Full-Stack Sênior**, especialista em Python, desenvolvimento web, bancos de dados relacionais e interfaces responsivas.

Crie uma aplicação web **CRUD plenamente funcional**, destinada ao gerenciamento de pacientes, médicos, procedimentos e atendimentos.

O sistema deve priorizar:

* simplicidade;
* praticidade;
* baixo custo;
* facilidade de instalação;
* facilidade de manutenção;
* código organizado;
* manutenibilidade;
* interface intuitiva;
* persistência real dos dados;
* possibilidade de evolução futura.

**Não entregue apenas um protótipo visual. A aplicação deve ser funcional de ponta a ponta.**

---

# 1. Stack tecnológica

Escolha uma stack tecnológica gratuita e, preferencialmente, open source.

O backend obrigatoriamente deverá utilizar **Python**.

Antes de implementar, apresente uma breve justificativa da stack escolhida.

Como primeira opção, considere:

* **Python 3.11+**
* **Flask**
* **SQLAlchemy**
* **SQLite**
* **Bootstrap 5**
* HTML5
* CSS3
* JavaScript
* Jinja2
* pytest

Caso escolha uma tecnologia diferente, justifique tecnicamente a decisão.

## Banco de dados

O banco deverá ser escolhido considerando principalmente:

1. praticidade;
2. simplicidade;
3. custo zero;
4. facilidade de instalação;
5. facilidade de backup;
6. facilidade de desenvolvimento;
7. desempenho adequado para uma aplicação de pequeno/médio porte;
8. possibilidade de migração futura para um banco mais robusto.

**Dê preferência ao SQLite**, caso não exista uma razão técnica relevante para utilizar outra solução.

Utilize **SQLAlchemy ORM** para acesso ao banco.

Não espalhe SQL diretamente pelas rotas da aplicação.

---

# 2. Objetivo da aplicação

A aplicação deverá permitir o gerenciamento de:

* Pacientes;
* Médicos;
* Procedimentos;
* Atendimentos.

O principal fluxo será o cadastro de um atendimento contendo:

* paciente;
* data;
* médico;
* procedimento;
* valor;
* observações;
* forma de pagamento.

---

# 3. Estrutura do banco de dados

O banco deverá possuir as seguintes tabelas:

```text
Paciente
Médico
Procedimento
Atendimento
```

Todos os campos do tipo data devem usar o padrão de formatação brasileiro (dd/mm/aaaa) nas telas e serem desta forma suportados também no banco de dados.

Todos os campos do tipo "valor" devem usar o padrão de formatação brasileiro com vírgula como separado de casas decimais e ponto como separador de milhares nas telas e serem desta forma suportados também no banco de dados.

---

# 4. Tabela Paciente

Criar a tabela `Paciente` com, no mínimo:

```text
id
nome
created_at
updated_at
```

Regras:

* `id` deve ser chave primária;
* `nome` é obrigatório;
* não permitir nome vazio;
* utilizar timestamps para controle de criação e alteração.

---

# 5. Tabela Médico

Criar a tabela `Medico` com:

```text
id
nome
created_at
updated_at
```

Regras:

* `id` como chave primária;
* `nome` obrigatório;
* não permitir nome vazio.

O sistema deverá permitir:

* cadastrar médico;
* editar médico;
* excluir médico;
* listar médicos;
* pesquisar médico.

---

# 6. Tabela Procedimento

Criar a tabela `Procedimento` com:

```text
id
nome
valor
created_at
updated_at
```

Regras:

* `id` como chave primária;
* `nome` obrigatório;
* `valor` obrigatório;
* valor deve ser maior ou igual a zero.

O sistema deverá permitir:

* cadastrar procedimento;
* editar procedimento;
* excluir procedimento;
* listar procedimentos;
* pesquisar procedimentos.

O valor do procedimento deverá ser armazenado como número no banco de dados.

**Não armazenar valores monetários como texto**, por exemplo:

```text
"R$ 150,00"
```

Armazene como valor numérico adequado.

---

# 7. Tabela Atendimento

Criar a tabela `Atendimento` com:

```text
id
paciente_id
medico_id
procedimento_id
data_atendimento
valor
observacoes
forma_pagamento
numero_parcelas
created_at
updated_at
```

Relacionamentos:

```text
Paciente       1 ---- N Atendimento
Médico         1 ---- N Atendimento
Procedimento   1 ---- N Atendimento
```

Criar corretamente as foreign keys.

---

# 8. Regra importante sobre o valor do atendimento

Quando o usuário selecionar um procedimento no formulário de atendimento, o sistema deverá automaticamente preencher o campo **Valor** utilizando o valor cadastrado para aquele procedimento.

Exemplo:

```text
Procedimento: Consulta Particular
Valor: R$ 250,00
```

Ao selecionar `Consulta Particular`, o campo `Valor` deve ser preenchido automaticamente com:

```text
R$ 250,00
```

Entretanto, o usuário poderá alterar manualmente o valor antes de salvar o atendimento.

### Regra histórica

O valor efetivamente utilizado no atendimento deve ser armazenado na tabela `Atendimento`.

Não depender exclusivamente do valor atual da tabela `Procedimento`.

Isso é fundamental porque o preço de um procedimento poderá mudar no futuro.

Exemplo:

```text
2026
Consulta Particular = R$ 250,00

2027
Consulta Particular = R$ 300,00
```

Um atendimento realizado em 2026 deverá continuar registrando:

```text
R$ 250,00
```

mesmo depois que o procedimento passar a custar R$ 300,00.

---

# 9. Seed inicial — Médicos

Na primeira execução da aplicação, cadastrar automaticamente:

```text
Juliana
Marcela Souza
Nedy Neves
Vilane Dias
```

O seed deve ser **idempotente**.

Ou seja, se a aplicação for reiniciada ou o seed for executado novamente, não deverá criar médicos duplicados.

Os médicos devem ser armazenados no banco e carregados dinamicamente no formulário.

**Não deixar os nomes dos médicos hardcoded no HTML.**

---

# 10. Seed inicial — Procedimentos

Na primeira execução da aplicação, cadastrar os seguintes procedimentos:

| Procedimento        |           Valor |
| ------------------- | --------------: |
| Consulta Particular | Definir no seed |
| Exames              | Definir no seed |
| Lente de Contato    | Definir no seed |
| Teste Ortóptico     | Definir no seed |
| Outros              | Definir no seed |

Como os valores ainda não foram fornecidos, deixe os valores claramente configurados em uma seção do seed para posterior preenchimento.

Exemplo:

```python
PROCEDIMENTOS_INICIAIS = [
    {"id": 1, "nome": "Consulta Particular", "valor": 0},
    {"id": 2, "nome": "Exames", "valor": 0},
    {"id": 3, "nome": "Lente de Contato", "valor": 0},
    {"id": 4, "nome": "Teste Ortóptico", "valor": 0},
    {"id": 5, "nome": "Outros", "valor": 0},
]
```

Os valores `0` são apenas placeholders e devem estar claramente identificados para posterior alteração.

O seed não poderá duplicar os procedimentos.

---

# 11. Formulário de Atendimento

Criar uma tela de cadastro e edição de atendimento.

Campos:

## Nome do paciente *

Campo obrigatório.

Deve permitir selecionar um paciente existente.

Disponibilizar também uma forma simples de cadastrar um novo paciente sem abandonar o fluxo atual, por exemplo:

```text
[ + Novo paciente ]
```

Pode ser implementado através de modal.

---

## Data de atendimento *

Formato visual:

```text
dd/mm/aaaa
```

Ao criar um novo atendimento, preencher automaticamente com a **data atual**.

O campo é obrigatório.

No banco, armazenar em formato adequado de data.

---

## Nome do médico *

Campo do tipo `select`.

Primeira opção:

```text
Selecione o médico...
```

Opções iniciais:

```text
Juliana
Marcela Souza
Nedy Neves
Vilane Dias
```

As opções devem ser carregadas dinamicamente da tabela `Medico`.

Campo obrigatório.

---

## Procedimento *

Campo do tipo `select`.

Primeira opção:

```text
Selecione o procedimento...
```

Procedimentos iniciais:

```text
Consulta Particular
Exames
Lente de Contato
Teste Ortóptico
Outros
```

As opções devem ser carregadas dinamicamente da tabela `Procedimento`.

Campo obrigatório.

---

## Valor

Campo monetário.

Ao selecionar um procedimento, preencher automaticamente com o valor cadastrado.

Permitir alteração manual.

Apresentar visualmente no padrão brasileiro:

```text
R$ 0,00
```

Porém, armazenar no banco como número.

---

## Observações

Campo opcional.

Utilizar `textarea`.

---

## Forma de pagamento

Campo `select`.

Opções:

```text
Dinheiro
Pix
Cartão
```

Campo obrigatório.

** No caso de selecionado "Cartão", permitir selecionar se "Crédito" ou "Débito". Se selecionar "Crédito", permitir escolher o número de parcelas (de 1 a 10 vezes) **

---

# 12. CRUD de Atendimentos

Implementar todas as operações:

## Create

Cadastrar atendimento.

## Read

Listar e visualizar atendimentos.

## Update

Editar atendimento.

## Delete

Excluir atendimento.

Antes da exclusão, apresentar confirmação ao usuário.

Todas as operações devem persistir efetivamente no banco de dados.

---

# 13. Listagem de atendimentos

Criar uma tela principal de atendimentos.

Exibir uma tabela:

| Data | Paciente | Médico | Procedimento | Valor | Pagamento | Ações |
| ---- | -------- | ------ | ------------ | ----: | --------- | ----- |

Ações:

```text
Visualizar
Editar
Excluir
```

Ordenação padrão:

```text
Data mais recente primeiro
```

---

# 14. Pesquisa e filtros

A tela de atendimentos deverá possuir filtros por:

* paciente;
* médico;
* procedimento;
* forma de pagamento;
* data inicial;
* data final.

Interface sugerida:

```text
Paciente:        [________________]

Médico:          [Selecione...]

Procedimento:    [Selecione...]

Pagamento:       [Selecione...]

Data inicial:    [__/__/____]

Data final:      [__/__/____]

[ Filtrar ] [ Limpar filtros ]
```

Os filtros deverão ser aplicados no banco de dados.

Não carregar todos os registros para depois filtrar somente no JavaScript, salvo quando houver uma razão técnica clara.

---

# 15. Exportação dos atendimentos

A aplicação deverá permitir exportar os atendimentos nos formatos:

```text
CSV
JSON
```

Na tela de listagem, apresentar:

```text
[ Exportar CSV ] [ Exportar JSON ]
```

---

# 16. Exportação CSV

Ao clicar em `Exportar CSV`, gerar e fazer o download de um arquivo `.csv`.

Colunas:

```text
ID
Data de Atendimento
Paciente
Médico
Procedimento
Valor
Forma de Pagamento
Observações
```

O arquivo deve:

* conter cabeçalho;
* utilizar UTF-8;
* preservar caracteres acentuados;
* ser compatível com Microsoft Excel;
* utilizar valores numéricos adequados para o campo Valor;
* ser gerado dinamicamente a partir do banco;
* não utilizar dados fictícios.

Preferencialmente utilizar `UTF-8 with BOM` (`utf-8-sig`) para melhor compatibilidade com Excel.

---

# 17. Exportação JSON

Ao clicar em `Exportar JSON`, gerar um arquivo `.json`.

Estrutura:

```json
[
    {
        "id": 1,
        "data_atendimento": "2026-09-03",
        "paciente": "Nome do Paciente",
        "medico": "Nedy Neves",
        "procedimento": "Consulta Particular",
        "valor": 250.00,
        "forma_pagamento": "Pix",
        "observacoes": "Observação do atendimento"
    }
]
```

Regras:

* JSON válido;
* UTF-8;
* `valor` deve ser número;
* data preferencialmente em formato ISO 8601;
* preservar caracteres acentuados;
* nomes das propriedades consistentes;
* não expor informações desnecessárias.

---

# 18. Exportação respeitando filtros

**REQUISITO FUNDAMENTAL**

A exportação deverá respeitar os filtros atualmente aplicados na tela.

Exemplo:

Se o usuário selecionar:

```text
Médico: Nedy Neves
Data inicial: 01/09/2026
Data final: 03/09/2026
```

e clicar:

```text
Exportar CSV
```

o arquivo deverá conter **somente os atendimentos correspondentes aos filtros**.

O mesmo deverá ocorrer para JSON.

Se nenhum filtro estiver aplicado:

```text
Exportar todos os atendimentos.
```

---

# 19. Endpoints de exportação

Criar endpoints específicos:

```text
GET /api/atendimentos/export/csv
GET /api/atendimentos/export/json
```

Os endpoints devem aceitar os mesmos parâmetros utilizados pela pesquisa.

Exemplo:

```text
/api/atendimentos/export/csv?medico_id=1&data_inicio=2026-09-01&data_fim=2026-09-03
```

e:

```text
/api/atendimentos/export/json?medico_id=1&data_inicio=2026-09-01&data_fim=2026-09-03
```

**Não duplicar a lógica de consulta.**

Criar uma função/serviço responsável por montar a consulta de atendimentos e reutilizá-la em:

* listagem;
* CSV;
* JSON.

---

# 20. Nome dos arquivos exportados

Utilizar nomes como:

```text
atendimentos_2026-09-03.csv
```

e:

```text
atendimentos_2026-09-03.json
```

Utilizar a data atual na geração do arquivo.

---

# 21. CRUD de Pacientes

Criar uma área específica para pacientes.

Funcionalidades:

* listar;
* pesquisar;
* cadastrar;
* editar;
* excluir.

Pesquisa por nome.

Ao tentar excluir um paciente que possua atendimentos relacionados:

* não permitir exclusão que gere registros órfãos;
* apresentar mensagem amigável;
* explicar que existem atendimentos relacionados.

---

# 22. CRUD de Médicos

Criar área específica para médicos.

Funcionalidades:

* listar;
* cadastrar;
* editar;
* excluir.

Tratar corretamente médicos que possuam atendimentos relacionados.

---

# 23. CRUD de Procedimentos

Criar área específica para procedimentos.

Funcionalidades:

* listar;
* cadastrar;
* editar;
* excluir.

Campos:

```text
Nome
Valor
```

Validar:

* nome obrigatório;
* valor obrigatório;
* valor >= 0.

Tratar corretamente procedimentos utilizados por atendimentos existentes.

---

# 24. Dashboard

Criar uma página inicial simples.

Adicionar ao título da página o logo da clínica (\Referencia\logo_soft.png) movendo o arquivo para a pasta adequada (link para página home).

Exibir cards com:

```text
Total de pacientes
Total de atendimentos
Valor Total
```
O card "Valor Total" deve permitir ocultar (padrão - exibir asteriscos) ou exibir o valor clicando sobre o ícone "exibir/ocultar".

Criar filtro "por período" no topo dashboard, conforme segue:

```text
Hoje
Esta semana (padrão)
Este mês
Este ano
Mês anterior
```

Todos os valores devem ser calculados a partir dos dados reais do banco.

---

# 25. Interface

Utilizar Bootstrap 5.

A interface deve ser:

* responsiva;
* limpa;
* profissional;
* simples;
* intuitiva;
* adequada para desktop;
* adequada para celular.

Menu lateral esqueda colapsável:

```text
Dashboard
Atendimentos
Pacientes
Médicos
Procedimentos
```

Utilizar mensagens de sucesso/erro:

```text
Cadastro realizado com sucesso.
Alteração realizada com sucesso.
Exclusão realizada com sucesso.
Exportação realizada com sucesso.
Erro de validação.
Registro não encontrado.
```

Utilizar `flash messages` do Flask quando apropriado.

---

# 26. JavaScript

Utilizar JavaScript somente onde agregar valor.

Exemplos:

* preenchimento automático do valor do procedimento;
* máscaras/formatação monetária;
* confirmação de exclusão;
* modal de novo paciente;
* interações da interface.

O preenchimento automático do valor deverá consultar uma API ou utilizar dados fornecidos pelo backend de forma segura.

Não confiar no JavaScript para validações críticas.

---

# 27. Validação

Implementar validação no:

* frontend;
* backend.

Campos obrigatórios:

```text
Paciente
Data de atendimento
Médico
Procedimento
Forma de pagamento
```

O backend deverá validar novamente todas as informações.

Nunca confiar exclusivamente na validação JavaScript/HTML.

---

# 28. Arquitetura

Utilizar uma arquitetura simples, mas organizada.

Sugestão:

```text
app/
│
├── __init__.py
│
├── models/
│   ├── __init__.py
│   ├── paciente.py
│   ├── medico.py
│   ├── procedimento.py
│   └── atendimento.py
│
├── routes/
│   ├── __init__.py
│   ├── dashboard.py
│   ├── pacientes.py
│   ├── medicos.py
│   ├── procedimentos.py
│   └── atendimentos.py
│
├── services/
│   ├── atendimento_service.py
│   └── exportacao.py
│
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   │
│   ├── pacientes/
│   │   ├── lista.html
│   │   └── formulario.html
│   │
│   ├── medicos/
│   │   ├── lista.html
│   │   └── formulario.html
│   │
│   ├── procedimentos/
│   │   ├── lista.html
│   │   └── formulario.html
│   │
│   └── atendimentos/
│       ├── lista.html
│       ├── formulario.html
│       └── detalhes.html
│
├── static/
│   ├── css/
│   │   └── style.css
│   │
│   └── js/
│       └── app.js
│
├── database.py
├── config.py
└── seed.py
│
instance/
└── app.db
│
tests/
├── test_pacientes.py
├── test_medicos.py
├── test_procedimentos.py
├── test_atendimentos.py
└── test_exportacao.py
│
run.py
requirements.txt
README.md
```

A estrutura pode ser simplificada se houver uma solução melhor para o tamanho da aplicação.

Não criar complexidade arquitetural desnecessária.

---

# 29. API

Criar endpoints RESTful quando apropriado.

Exemplo:

```text
GET    /api/pacientes
POST   /api/pacientes
GET    /api/pacientes/<id>
PUT    /api/pacientes/<id>
DELETE /api/pacientes/<id>

GET    /api/medicos
POST   /api/medicos
GET    /api/medicos/<id>
PUT    /api/medicos/<id>
DELETE /api/medicos/<id>

GET    /api/procedimentos
POST   /api/procedimentos
GET    /api/procedimentos/<id>
PUT    /api/procedimentos/<id>
DELETE /api/procedimentos/<id>

GET    /api/atendimentos
POST   /api/atendimentos
GET    /api/atendimentos/<id>
PUT    /api/atendimentos/<id>
DELETE /api/atendimentos/<id>

GET    /api/atendimentos/export/csv
GET    /api/atendimentos/export/json
```

---

# 30. Segurança e boas práticas

Mesmo sendo uma aplicação simples:

* utilizar SQLAlchemy ORM;
* não concatenar SQL com entrada do usuário;
* validar todos os dados no backend;
* utilizar variáveis de ambiente para configurações sensíveis;
* utilizar `SECRET_KEY` por variável de ambiente;
* implementar proteção CSRF para formulários tradicionais;
* tratar exceções;
* utilizar códigos HTTP apropriados;
* não expor stack traces em produção;
* não armazenar secrets no código;
* tratar corretamente arquivos de exportação;
* evitar exposição de dados desnecessários.

Não implementar autenticação/login neste primeiro momento, salvo se houver necessidade técnica.

---

# 31. Tratamento de erros

Tratar pelo menos:

* registro não encontrado;
* dados inválidos;
* campos obrigatórios ausentes;
* tentativa de exclusão de registro relacionado;
* erro de banco;
* erro na exportação;
* erro interno.

Apresentar mensagens amigáveis.

---

# 32. Testes automatizados

Utilizar `pytest`.

Criar testes para:

### Pacientes

* criar;
* consultar;
* editar;
* excluir;
* validar nome obrigatório.

### Médicos

* criar;
* consultar;
* editar;
* excluir.

### Procedimentos

* criar;
* consultar;
* editar;
* excluir;
* validar valor.

### Atendimentos

* criar;
* consultar;
* editar;
* excluir;
* validar campos obrigatórios;
* validar relacionamentos;
* verificar preenchimento do valor do procedimento;
* verificar armazenamento do valor histórico.

### Exportação

Testar:

* geração de CSV;
* geração de JSON;
* estrutura do CSV;
* estrutura do JSON;
* encoding UTF-8;
* preservação de caracteres acentuados;
* exportação de todos os registros;
* exportação respeitando filtros;
* exportação sem registros;
* valores numéricos no JSON.

---

# 33. README.md

Criar documentação completa contendo:

## Requisitos

Exemplo:

```text
Python 3.11+
```

## Criação do ambiente

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
```

## Instalação

```bash
pip install -r requirements.txt
```

## Execução

```bash
python run.py
```

Informar a URL:

```text
http://localhost:5000
```

## Banco de dados

Explicar:

* onde fica o SQLite;
* como ele é criado;
* como o seed funciona;
* como fazer backup;
* como restaurar o banco.

## Exportação

Explicar:

* como exportar CSV;
* como exportar JSON;
* como exportar PDF (formatado);
* como utilizar filtros;
* como os filtros afetam os arquivos exportados.

---

# 34. Backup

Como o banco será SQLite, documentar uma estratégia simples de backup.

Explicar que o arquivo:

```text
instance/app.db
```

é o banco de dados da aplicação.

Mostrar como fazer uma cópia de segurança.

Se houver alguma recomendação adicional para backup consistente do SQLite, documentá-la.

---

# 35. Requisitos de código

O código entregue deve ser **realmente executável**.

Não utilizar:

* pseudocódigo;
* funções vazias;
* endpoints fictícios;
* dados simulados;
* `TODO` no lugar de implementação;
* botões que não fazem nada;
* consultas simuladas;
* armazenamento temporário em memória.

Todos os dados devem ser persistidos no banco.

Todos os botões da interface devem funcionar.

---

# 36. Critérios de aceitação

Considere o sistema concluído somente quando:

1. A aplicação iniciar sem erros.
2. O SQLite for criado automaticamente.
3. O seed de médicos funcionar.
4. O seed de procedimentos funcionar.
5. Os médicos não forem duplicados.
6. Os procedimentos não forem duplicados.
7. Os IDs dos procedimentos 101–105 forem preservados.
8. Pacientes puderem ser cadastrados.
9. Pacientes puderem ser editados.
10. Pacientes puderem ser excluídos quando não houver dependências.
11. Médicos puderem ser cadastrados.
12. Médicos puderem ser editados.
13. Médicos puderem ser excluídos quando permitido.
14. Procedimentos puderem ser cadastrados.
15. Procedimentos puderem ser editados.
16. Procedimentos puderem ser excluídos quando permitido.
17. Um atendimento puder ser cadastrado.
18. A data atual seja preenchida automaticamente em um novo atendimento.
19. O médico seja selecionado a partir do banco.
20. O procedimento seja selecionado a partir do banco.
21. O valor seja preenchido automaticamente ao selecionar o procedimento.
22. O usuário possa alterar o valor.
23. O valor efetivamente utilizado seja armazenado no atendimento.
24. O atendimento possa ser editado.
25. O atendimento possa ser excluído.
26. A listagem de atendimentos funcione.
27. Os filtros funcionem.
28. O dashboard utilize dados reais.
29. Os atendimentos possam ser exportados para CSV.
30. Os atendimentos possam ser exportados para JSON.
31. CSV e JSON contenham dados reais do banco.
32. A exportação respeite os filtros.
33. CSV preserve caracteres acentuados.
34. JSON seja válido.
35. JSON represente `valor` como número.
36. Datas do JSON estejam em formato consistente.
37. Testes automatizados sejam executados com sucesso.
38. O README permita que outra pessoa instale e execute o projeto sem conhecimento prévio da implementação.
39. Não existam funcionalidades apenas simuladas.
40. A aplicação seja responsiva.

---

# 37. Processo de implementação

Siga esta ordem:

### Etapa 1 — Análise

Antes de escrever o código:

1. analisar os requisitos;
2. identificar possíveis ambiguidades;
3. escolher a stack;
4. justificar o banco de dados;
5. apresentar a arquitetura resumida;
6. apresentar o modelo de dados.

### Etapa 2 — Implementação

Depois da análise:

1. criar estrutura do projeto;
2. configurar Flask;
3. configurar SQLAlchemy;
4. criar modelos;
5. criar banco;
6. implementar seed;
7. criar CRUDs;
8. criar dashboard;
9. criar filtros;
10. criar exportação CSV;
11. criar exportação JSON;
12. criar frontend;
13. implementar JavaScript necessário;
14. criar testes;
15. criar README.

### Etapa 3 — Validação

Depois de implementar:

1. executar a aplicação;
2. executar os testes;
3. corrigir erros;
4. verificar todos os CRUDs;
5. verificar persistência no SQLite;
6. verificar filtros;
7. verificar exportação CSV;
8. verificar exportação JSON;
9. verificar caracteres acentuados;
10. verificar responsividade;
11. verificar seed idempotente.

**Não considere o projeto concluído enquanto os testes e a execução básica não estiverem funcionando.**

---

# 38. Entrega final

Ao finalizar, apresente:

1. stack escolhida;
2. justificativa do banco de dados;
3. arquitetura;
4. estrutura final dos diretórios;
5. arquivos criados;
6. instruções de instalação;
7. instruções de execução;
8. instruções de testes;
9. funcionamento do CRUD;
10. funcionamento da exportação CSV;
11. funcionamento da exportação JSON;
12. estratégia de backup do SQLite;
13. limitações conhecidas;
14. sugestões de evolução futura.

**IMPORTANTE:**

O objetivo não é criar uma demonstração ou mockup.

O objetivo é entregar uma **aplicação CRUD completa, funcional e executável**, com frontend, backend, banco de dados SQLite, persistência real, filtros, seed inicial, dashboard, testes automatizados e exportação dos atendimentos em CSV e JSON.

Sempre que houver uma decisão técnica que possa aumentar desnecessariamente a complexidade, prefira a solução **mais simples, gratuita, confiável e fácil de manter**.
