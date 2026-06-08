# Documentação Funcional — Filtro de Tarefas (ClickUp / Tributo Justo)

> Documento de referência das funcionalidades atuais do projeto. Serve de base para a
> refatoração em uma arquitetura mais robusta. Descreve **o que o sistema faz hoje**,
> **como faz**, e **onde estão os pontos frágeis** que a nova arquitetura deve resolver.

---

## 1. Visão geral

Aplicação web em **Streamlit** que recebe um CSV exportado do **ClickUp** e produz:

- Indicadores (KPIs) sobre as tarefas.
- Gráficos automáticos (barras, pizza, comparativo, horizontal).
- Filtros interativos (período, status, prioridade, responsável, centro de custo etc.).
- Tabela filtrável + exportação CSV.
- Um formulário de **evolução mensal** que gera 5 gráficos comparando 3 meses.

Todo o sistema vive hoje em **um único arquivo**: `main.py` (~818 linhas), sem camadas,
sem testes, sem separação entre lógica de dados, geração de gráficos e UI.

### Stack atual

| Componente | Versão | Papel |
|------------|--------|-------|
| Python | >= 3.13 | Runtime |
| Streamlit | >= 1.50 | UI web e estado de sessão |
| Pandas | >= 2.3.3 | Leitura e manipulação do CSV |
| Matplotlib | >= 3.10.7 | Geração de gráficos (salvos como PNG) |
| python-dateutil | (transitiva) | Cálculo de meses (`relativedelta`) |

Execução: `streamlit run main.py`.

---

## 2. Modelo de dados (CSV do ClickUp)

O código depende de nomes de coluna **fixos e em texto literal**. Colunas esperadas:

### Colunas de data
Convertidas para `datetime` com `pd.to_datetime(..., errors='coerce')`:

- `Due Date`
- `Start Date`
- `Date Created`
- `Date Updated`
- `Date Closed`
- `Date Done`

### Colunas de filtro / dimensão
- `Status`
- `Priority`
- `Assignee`
- `Task Type`
- `Task Name` (usada na busca textual)
- `Centro de Custo (drop down)`
- `Planejamento (drop down)`
- `Produto (drop down)`
- `Tipo (drop down)`

> ⚠️ **Risco:** se uma coluna faltar ou mudar de nome, a feature dependente é silenciosamente
> ignorada (`if coluna in df.columns`) ou quebra (acesso direto como `df['Task Name']`,
> `df['Centro de Custo (drop down)']` dentro do formulário). Não há validação de schema.

---

## 3. Funcionalidades detalhadas

### 3.1 Configuração da página e estilo
- `st.set_page_config(...)`: título "Filtro de Tarefas", ícone 📋, layout wide, sidebar expandida.
- `plt.rcParams`: define tamanho de figura, fontes e estilo de título global para todos os gráficos.

### 3.2 Persistência de gráficos em disco
- `criar_pasta_graficos()`: garante a existência da pasta `graficos/`.
- Todos os gráficos são salvos como **PNG** com timestamp no nome (`{nome}_{YYYYMMDD_HHMMSS}.png`),
  em `dpi=300`, fundo branco.

> ⚠️ **Risco:** efeito colateral em disco a cada execução. A pasta cresce indefinidamente
> (sem limpeza). Em ambiente multiusuário/cloud (Streamlit Cloud) isso gera lixo e condições de corrida.

### 3.3 Geração de gráficos (funções)

| Função | Tipo de gráfico | Entrada | Observações |
|--------|-----------------|---------|-------------|
| `gerar_grafico_barras(df, coluna, titulo, nome_arquivo)` | Barras verticais | `value_counts()` | Rótulos no topo das barras |
| `gerar_grafico_pizza(df, coluna, titulo, nome_arquivo, top_n=5)` | Pizza | top N + "Outros" | Paleta fixa em tons de `#101C35`. **Não é chamada em lugar nenhum** (código morto) |
| `gerar_grafico_barras_horizontal(df, coluna, titulo, nome_arquivo)` | Barras horizontais | `value_counts()` | Usada para "Tipo" |
| `gerar_grafico_comparativo(df, coluna, titulo, nome_arquivo)` | Barras Planejado×Não Planejado | normalização de rótulo | Cores fixas; normaliza variações de texto |

**Padrão comum a todas:** retornam `None` se a coluna não existe; senão, salvam PNG e
retornam o caminho. Há **forte duplicação** entre elas (config de eixos, spines, salvamento).

#### Normalização de "Planejamento"
Função interna `normalizar(label)` (duplicada em `gerar_grafico_comparativo` **e** em
`calcular_indicadores`):
- `NaN` → `'Desconhecido'` (no gráfico) / `'Outros'` (no indicador) — **inconsistente**.
- contém `planej` e não contém `não/nao` → `'Planejado'`.
- contém `não/nao` → `'Não Planejado'`.
- resto → `'Outros'`.

### 3.4 Orquestração de gráficos principais
`gerar_todos_graficos(df)`:
- Barras verticais para `Centro de Custo (drop down)` e `Produto (drop down)`.
- Comparativo para `Planejamento (drop down)`.
- Barras horizontais para `Tipo (drop down)`.
- Retorna lista `[(titulo, caminho), ...]`.

Chamado **uma vez por upload** (controle via `st.session_state.ultimo_upload`).

### 3.5 Cálculo de indicadores (KPIs)
`calcular_indicadores(df)` retorna um dict com **strings já formatadas**:

| Chave | Conteúdo | Formato |
|-------|----------|---------|
| `total_atividades` | contagem de linhas | `int` |
| `centro_custo` | categoria mais frequente | `"Nome: 99.99%"` |
| `produto` | categoria mais frequente | `"Nome: 99.99%"` |
| `planejadas` | quantidade + % de planejadas | `"Planejadas: N (99.99%)"` |
| `tipo` | tipo mais frequente | `"Nome: 99.99%"` |

> ⚠️ **Risco grave:** os valores são **strings formatadas**, não dados. Mais adiante o código
> faz *parsing reverso* dessas strings (`.split(':')`, `.split('(')`, `.replace('%','')`) para
> recuperar números. Qualquer mudança de formato quebra a seção de evolução mensal.

### 3.6 Fluxo principal (após upload)

1. **Upload** via `st.file_uploader` (apenas `.csv`).
2. **Leitura** com `pd.read_csv` + conversão de datas.
3. **Geração automática** dos gráficos principais (uma vez por arquivo).
4. **Filtros na sidebar:**
   - **Período:** escolhe coluna de data e intervalo (padrão: últimos 30 dias). Aplica máscara.
   - `aplicar_filtro(label, coluna, default)`: `multiselect` por coluna; se nada além do default
     for escolhido, não filtra. Aplicado a: Status, Priority, Assignee, Task Type, Centro de Custo,
     Planejamento, Produto, Tipo.
   - **Busca textual** em `Task Name` (`str.contains`, case-insensitive).
5. **Indicadores** calculados **sobre o DataFrame já filtrado**.
6. **Cards de indicadores** (HTML inline via `unsafe_allow_html`): Atividades, Centro de Custo,
   Produto, Planejadas, Tipo. Mês/ano atual traduzido para PT manualmente.
7. **Métricas resumo** (`st.metric`): total, Produção (status contém "Produção"),
   Alta Prioridade (`urgent|high`), nº de responsáveis distintos.
8. **Contagens** por Centro de Custo, Planejamento, Produto, Tipo (`mostrar_contagem`).
9. **Configurar colunas visíveis** (`st.expander` + `multiselect`).
10. **Tabela** filtrada (`st.dataframe`).
11. **Exportar CSV** filtrado (`st.download_button`).
12. **Exibição dos gráficos principais** salvos em sessão.
13. **Evolução mensal** (ver 3.7).

### 3.7 Evolução mensal — formulário + 5 gráficos

- Calcula nomes de 3 meses (`mes_retrasado`, `mes_passado`, `mes_atual`) a partir do
  **último dia do mês anterior** (`hoje.replace(day=1) - timedelta(days=1)`), via `relativedelta`.
- Tradução de meses EN→PT feita por **encadeamento de `.replace()`** (frágil).
- **Parsing reverso** dos indicadores formatados para obter os valores do mês atual.
- `st.form` com 5 colunas (Total, Centro de Custo, Produto, Tipo, Planejadas), cada uma pedindo
  valores manuais para os 2 meses anteriores; o mês atual vem dos indicadores.
- Ao submeter, gera **5 gráficos** com tipos visuais diferentes: `line`, `bar`, `area`,
  `line_dashed`, `bar_horizontal`. Cada um salvo como PNG `Evolucao_*.png`.
- Gráficos com todos os valores = 0 são pulados.

> ⚠️ **Risco:** os `selectbox` de categoria (`cc_ret`, `prod_ret` etc.) acessam
> `df['Centro de Custo (drop down)']` **diretamente** — se a coluna não existir, o app quebra
> com `KeyError` dentro do `try` global, exibindo "❌ Erro ao processar o arquivo".

### 3.8 Tratamento de erro e ajuda
- Todo o fluxo está dentro de **um único `try/except Exception`** que apenas mostra
  `st.error(f"❌ Erro ao processar o arquivo: {e}")` — sem log, sem stack trace, sem distinção
  de causa.
- `st.expander("ℹ️ Como usar")`: instruções de uso.
- Rodapé com crédito ao desenvolvedor.

---

## 4. Estado de sessão (`st.session_state`)

| Chave | Uso |
|-------|-----|
| `ultimo_upload` | Nome do último arquivo, para não regerar gráficos |
| `graficos_principais` | Lista `(titulo, caminho)` dos PNGs gerados |
| Chaves de widgets (`tot_ret`, `cc_ret`, ...) | Valores do formulário de evolução |

---

## 5. Catálogo de problemas (alvos da refatoração)

### Arquitetura
- **Arquivo único monolítico** misturando UI, regras de negócio, acesso a dados e I/O de disco.
- **Sem separação de camadas** (data / domínio / apresentação).
- **Sem testes** automatizados; lógica de KPIs e normalização não é testável isoladamente.

### Dados
- **Schema implícito**, nomes de coluna mágicos espalhados em strings literais.
- **Sem validação** de presença/tipo de colunas; falhas silenciosas ou `KeyError`.
- **Indicadores como strings formatadas** + *parsing reverso* — fonte de bugs.
- **Lógica de normalização duplicada** e inconsistente (`Desconhecido` vs `Outros`).

### Gráficos / I/O
- **Geração de PNG em disco** como efeito colateral; pasta `graficos/` cresce sem limpeza.
- **Forte duplicação** entre as funções de gráfico (config de eixos/spines/salvamento).
- **`gerar_grafico_pizza` é código morto** (nunca chamada).
- Cores e estilo **hard-coded** repetidos (`#101C35`, paletas).

### UX / robustez
- **Um único `try/except`** engole todos os erros sem diagnóstico.
- **Tradução de meses manual** via `.replace()` encadeado (frágil; ignora locale).
- **HTML inline** com `unsafe_allow_html` para os cards (poderia ser componente reutilizável).
- Filtros aplicados por **mutação sequencial** do mesmo `df` — difícil de rastrear.

---

## 6. Arquitetura-alvo proposta (resumo)

Sugestão de decomposição para a refatoração (a detalhar em documento próprio):

```
src/
  config.py          # constantes: nomes de coluna, paleta, mapeamento de meses
  data/
    loader.py        # leitura CSV, parsing de datas
    schema.py        # validação de colunas esperadas (ex.: pydantic/pandera)
    filters.py       # filtros puros (período, dimensões, busca) -> DataFrame
  domain/
    indicators.py    # KPIs retornando dataclasses/dicts NUMÉRICOS (não strings)
    normalize.py     # normalização única de "Planejamento"
  charts/
    base.py          # estilo comum, salvamento, helper de eixos
    builders.py      # barras/pizza/horizontal/comparativo/evolução
  ui/
    sidebar.py       # widgets de filtro
    cards.py         # componentes de KPI
    pages.py         # composição da página
  app.py             # orquestração fina (Streamlit)
tests/
  test_indicators.py
  test_normalize.py
  test_filters.py
```

Princípios:
- **Separar dados puros da apresentação**: KPIs e filtros como funções puras testáveis.
- **Schema explícito e validado** na entrada; erros claros por causa.
- **Gráficos retornando figuras em memória** (`st.pyplot(fig)`), salvamento em disco opcional.
- **Indicadores numéricos tipados**; formatação só na camada de UI.
- **Configuração centralizada** (nomes de coluna, paleta, meses).
- **Cobertura de testes** para domínio (indicadores, normalização, filtros).

---

## 7. Como executar (estado atual)

```bash
# instala dependências (uv)
uv sync

# roda a aplicação
streamlit run main.py
```

Acesse a URL local exibida no terminal e faça upload do CSV exportado do ClickUp.
