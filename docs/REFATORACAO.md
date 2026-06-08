# Plano de Refatoração — Filtro de Tarefas (ClickUp / Tributo Justo)

> Roteiro em etapas para evoluir o `main.py` monolítico para uma arquitetura em camadas,
> **com persistência em SQLite**. Pré-requisito: ler [`FUNCIONALIDADES.md`](./FUNCIONALIDADES.md).

---

## 1. Objetivos

1. **Eliminar a digitação manual** dos meses anteriores no formulário de evolução.
   Os dados dos meses passados ficam salvos em **SQLite** e são carregados automaticamente
   para montar os gráficos comparativos.
2. **Armazenar os dados do mês atual** (tarefas importadas e/ou indicadores calculados) para
   poder **listar e consultar** depois, sem precisar reimportar o CSV.
3. **Separar camadas** (dados / domínio / gráficos / UI) para tornar a lógica testável.
4. Fazer tudo de forma **incremental**, mantendo o app funcionando a cada etapa.

---

## 2. Modelo de dados (SQLite)

Banco local `data/app.db` (arquivo único, versionável por migrations simples).

### Tabela `imports`
Registra cada upload de CSV.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | INTEGER PK | autoincrement |
| `file_name` | TEXT | nome do CSV importado |
| `period` | TEXT | competência `YYYY-MM` (mês de referência) |
| `imported_at` | TEXT (ISO) | data/hora da importação |
| `row_count` | INTEGER | nº de tarefas importadas |

### Tabela `tasks`
Tarefas brutas importadas (permite listar o mês atual depois).

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | INTEGER PK | autoincrement |
| `import_id` | INTEGER FK → imports.id | lote de importação |
| `period` | TEXT | `YYYY-MM` (desnormalizado p/ consulta rápida) |
| `task_name` | TEXT | `Task Name` |
| `status` | TEXT | `Status` |
| `assignee` | TEXT | `Assignee` |
| `priority` | TEXT | `Priority` |
| `task_type` | TEXT | `Task Type` |
| `centro_custo` | TEXT | `Centro de Custo (drop down)` |
| `planejamento` | TEXT | `Planejamento (drop down)` (valor normalizado) |
| `produto` | TEXT | `Produto (drop down)` |
| `tipo` | TEXT | `Tipo (drop down)` |
| `due_date` | TEXT | `Due Date` (ISO ou null) |
| `start_date` | TEXT | `Start Date` |
| `date_created` | TEXT | `Date Created` |
| `date_done` | TEXT | `Date Done` |
| `raw_json` | TEXT | linha original serializada (colunas extras) |

> Guardar `raw_json` evita perda de colunas não mapeadas e facilita evolução do schema.

### Tabela `monthly_metrics`
Snapshot dos indicadores por competência — **alimenta os gráficos comparativos automaticamente**.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | INTEGER PK | autoincrement |
| `period` | TEXT UNIQUE | `YYYY-MM` |
| `total_atividades` | INTEGER | total de tarefas |
| `planejadas_qtd` | INTEGER | qtd planejadas |
| `planejadas_perc` | REAL | % planejadas |
| `cc_top_nome` | TEXT | centro de custo mais frequente |
| `cc_top_perc` | REAL | % do top centro de custo |
| `produto_top_nome` | TEXT | produto mais frequente |
| `produto_top_perc` | REAL | % do top produto |
| `tipo_top_nome` | TEXT | tipo mais frequente |
| `tipo_top_perc` | REAL | % do top tipo |
| `computed_at` | TEXT (ISO) | quando foi calculado |

> `UNIQUE(period)` + **upsert**: reimportar o mesmo mês atualiza o snapshot em vez de duplicar.

### (Opcional) Tabela `monthly_category_breakdown`
Distribuição completa por dimensão/categoria/mês (para gráficos mais ricos no futuro).

| Coluna | Tipo |
|--------|------|
| `period` | TEXT |
| `dimension` | TEXT (`centro_custo`/`produto`/`tipo`/`planejamento`) |
| `category` | TEXT |
| `count` | INTEGER |
| `perc` | REAL |

---

## 3. Estrutura de pastas alvo

```
src/
  config.py            # nomes de coluna, paleta, mapeamento de meses, caminho do db
  data/
    db.py              # conexão SQLite, migrations, helpers (get_conn, init_db)
    repository.py      # CRUD: save_import, save_tasks, upsert_metrics, get_last_n_metrics, list_tasks
    loader.py          # leitura CSV + parsing de datas
    schema.py          # validação de colunas esperadas
    filters.py         # filtros puros sobre DataFrame
  domain/
    normalize.py       # normalização única de "Planejamento"
    indicators.py      # KPIs NUMÉRICOS (dataclass), sem formatação
    period.py          # cálculo de competência YYYY-MM e nomes de meses (locale-aware)
  charts/
    base.py            # estilo comum, salvar/retornar figura
    builders.py        # barras/pizza/horizontal/comparativo
    evolution.py       # gráficos de evolução a partir de monthly_metrics
  ui/
    sidebar.py
    cards.py
    history.py         # tela de listagem do histórico (tasks / metrics)
    pages.py
  app.py               # orquestração Streamlit
tests/
  test_normalize.py
  test_indicators.py
  test_filters.py
  test_repository.py
data/
  app.db               # (gitignored)
```

---

## 4. Etapas incrementais

Cada etapa é entregável e deixa o app funcionando. Sugestão: 1 commit (ou PR) por etapa.

### Etapa 0 — Preparação
- [ ] Criar pasta `docs/` (feito) e `src/`, `tests/`, `data/`.
- [ ] Adicionar `data/app.db` e `graficos/` ao `.gitignore`.
- [ ] Fixar dependências: `pandas`, `streamlit`, `matplotlib`. (SQLite é stdlib — `sqlite3`.)
- [ ] Opcional: adicionar `pytest` e `ruff` como deps de dev.

### Etapa 1 — Extrair configuração e domínio puro
- [ ] `config.py`: mover todos os nomes de coluna literais e a paleta para constantes.
- [ ] `domain/normalize.py`: **uma** função `normalizar_planejamento(label)` (resolver a
      inconsistência `Desconhecido` vs `Outros`).
- [ ] `domain/indicators.py`: `calcular_indicadores(df) -> Indicadores` (dataclass com campos
      **numéricos**: `total`, `planejadas_qtd`, `planejadas_perc`, `cc_top` (nome, perc) etc.).
      **Sem strings formatadas.** Formatação vira responsabilidade da UI.
- [ ] `domain/period.py`: `competencia_atual()`, `nome_mes(period)`, `ultimos_n_meses(n)`.
- [ ] Testes: `test_normalize.py`, `test_indicators.py`.

> Isso já remove o **parsing reverso** de strings (maior fonte de bugs hoje).

### Etapa 2 — Camada de dados (CSV)
- [ ] `data/loader.py`: `carregar_csv(file) -> DataFrame` com parsing de datas.
- [ ] `data/schema.py`: `validar_colunas(df)` → erro claro listando colunas ausentes.
- [ ] `data/filters.py`: funções puras (`filtrar_periodo`, `filtrar_dimensao`, `buscar_nome`),
      cada uma recebendo e retornando DataFrame (fim da mutação sequencial).
- [ ] Testes: `test_filters.py`.

### Etapa 3 — Persistência SQLite (núcleo da feature pedida)
- [ ] `data/db.py`: `init_db()` cria as tabelas se não existirem.
- [ ] `data/repository.py`:
  - `salvar_importacao(file_name, period, df) -> import_id`
  - `salvar_tarefas(import_id, period, df)`
  - `upsert_metrics(period, indicadores)` (insere ou atualiza o snapshot do mês)
  - `obter_metrics_ultimos_meses(n=3) -> list[MonthlyMetrics]`
  - `listar_tarefas(period=None, filtros=...) -> DataFrame`
- [ ] No upload: após calcular indicadores, **persistir** tasks + upsert do snapshot do mês.
- [ ] Testes: `test_repository.py` (usar banco em memória `:memory:`).

### Etapa 4 — Evolução automática (elimina digitação manual)
- [ ] `charts/evolution.py`: ler `obter_metrics_ultimos_meses(3)` e montar os 5 gráficos
      comparativos **sem formulário**.
- [ ] Substituir o `st.form` de digitação manual por:
  - preenchimento automático dos meses anteriores a partir do SQLite;
  - fallback opcional: se um mês não existe no banco, permitir input manual (transição suave).
- [ ] Manter a opção de salvar PNG, mas **renderizar com `st.pyplot(fig)`** (sem depender de disco).

### Etapa 5 — Tela de histórico / listagem
- [ ] `ui/history.py`: aba/seção para **listar tarefas armazenadas** por competência,
      com filtros e exportação CSV (reuso da camada `filters`).
- [ ] Mostrar série histórica dos `monthly_metrics` (tabela + gráfico de tendência).

### Etapa 6 — Refatorar gráficos e UI
- [ ] `charts/base.py`: extrair estilo/spines/salvamento comuns (remover duplicação).
- [ ] `charts/builders.py`: barras/horizontal/comparativo usando a base. Remover
      `gerar_grafico_pizza` (código morto) ou integrá-la se for usada.
- [ ] `ui/cards.py`: componente de card KPI (encapsular o HTML inline).
- [ ] `ui/sidebar.py`, `ui/pages.py`, `app.py`: orquestração fina.

### Etapa 7 — Robustez e finalização
- [ ] Trocar o `try/except Exception` único por tratamento por etapa, com mensagens claras e log.
- [ ] Substituir tradução de meses por `.replace()` encadeado por mapa único / `locale`.
- [ ] Rotina opcional de limpeza da pasta `graficos/` (ou parar de salvar em disco).
- [ ] README com instruções atualizadas.
- [ ] Garantir suíte de testes passando.

---

## 5. Fluxo após refatoração (resumo)

```
Upload CSV
  → loader.carregar_csv → schema.validar_colunas
  → domain.indicators.calcular_indicadores (numérico)
  → repository.salvar_tarefas + repository.upsert_metrics(period)   [SQLite]
  → UI: cards, métricas, contagens, tabela, export

Evolução mensal
  → repository.obter_metrics_ultimos_meses(3)   [SQLite, sem digitação]
  → charts.evolution → st.pyplot

Histórico
  → repository.listar_tarefas(period) / metrics  → tabela + export
```

---

## 6. Decisões em aberto (definir antes de codar)

1. **Competência do mês:** derivar de qual coluna de data (`Date Created`? `Date Done`?) ou
   o usuário escolhe no upload? Isso define o `period` de cada tarefa.
2. **Reimportar mês existente:** sobrescrever tarefas daquele período ou acumular? (Recomendado:
   substituir as tarefas do `period` e fazer upsert das métricas.)
3. **Granularidade do histórico:** guardar só `monthly_metrics`, ou também todas as `tasks`?
   (Pedido inclui listar dados do mês atual → guardar `tasks`.)
4. **Migrations:** schema fixo com `CREATE TABLE IF NOT EXISTS` é suficiente no início; adotar
   versionamento (ex.: tabela `schema_version`) quando o schema evoluir.

> Sugestão de respostas-padrão: competência por `Date Created`; reimport substitui o período;
> guardar `tasks` + `monthly_metrics`; migrations simples por enquanto.
