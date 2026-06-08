# Filtro de Tarefas — ClickUp / Tributo Justo

Aplicação Streamlit que importa um CSV exportado do ClickUp e produz indicadores,
gráficos, filtros, tabela exportável e **evolução mensal automática** a partir de
um histórico persistido em **SQLite**.

## Arquitetura

Refatorado de um `main.py` monolítico para camadas (ver `docs/REFATORACAO.md` e
`docs/FUNCIONALIDADES.md`):

```
src/
  config.py            # nomes de coluna, paleta, meses, caminho do banco
  data/                # loader, schema, filters, db, repository (SQLite)
  domain/              # normalize, indicators (numéricos), period
  charts/              # base, builders, evolution (figuras em memória)
  ui/                  # sidebar, cards, pages, history
  app.py               # orquestração Streamlit
tests/                 # pytest (normalize, indicators, filters, repository)
data/app.db            # banco SQLite (gitignored)
```

Principais mudanças da refatoração:
- Indicadores são **numéricos tipados** (sem parsing reverso de strings).
- Normalização de Planejamento **única e consistente**.
- Gráficos **renderizados em memória** (`st.pyplot`), sem salvar PNG em disco.
- Persistência em **SQLite**: tarefas e snapshots mensais; evolução mensal sem
  digitação manual.
- Tratamento de erro por etapa (leitura / validação / persistência).

## Como executar

```bash
uv sync
streamlit run main.py
```

Faça upload do CSV exportado do ClickUp. A competência (mês) é derivada de
`Date Created`; reimportar o mesmo mês **substitui** as tarefas daquele período.

## Testes

```bash
uv run pytest -q
```
