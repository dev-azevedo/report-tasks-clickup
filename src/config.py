"""Configuração centralizada: nomes de coluna, paleta, meses e caminho do banco.

Remove os literais mágicos espalhados pelo código antigo (`main.py`), onde nomes
de coluna como ``"Centro de Custo (drop down)"`` apareciam repetidos em dezenas
de pontos.
"""

from pathlib import Path

# --- Caminho do banco SQLite ---
# Raiz do projeto = pasta que contém `src/`.
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "app.db"

# --- Nomes de coluna do CSV do ClickUp ---
COL_TASK_NAME = "Task Name"
COL_STATUS = "Status"
COL_ASSIGNEE = "Assignee"
COL_PRIORITY = "Priority"
COL_TASK_TYPE = "Task Type"
COL_CENTRO_CUSTO = "Centro de Custo (drop down)"
COL_PLANEJAMENTO = "Planejamento (drop down)"
COL_PRODUTO = "Produto (drop down)"
COL_TIPO = "Tipo (drop down)"

# Colunas de data convertidas para datetime na leitura.
DATE_COLUMNS = [
    "Due Date",
    "Start Date",
    "Date Created",
    "Date Updated",
    "Date Closed",
    "Date Done",
]

# Coluna usada para derivar a competência (period YYYY-MM) de cada tarefa.
COL_COMPETENCIA = "Date Created"

# Colunas mínimas exigidas para o app funcionar (validação de schema).
COLUNAS_OBRIGATORIAS = [COL_TASK_NAME]

# Colunas de dimensão usadas em filtros, contagens e gráficos.
DIMENSOES = [COL_CENTRO_CUSTO, COL_PLANEJAMENTO, COL_PRODUTO, COL_TIPO]

# Meta de % de atividades planejadas (linha de referência nos gráficos).
META_PLANEJADO = 70.0

# --- Paleta ---
COR_PRIMARIA = "#101C35"
COR_SECUNDARIA = "#777777"
PALETA_TONS = ["#101C35", "#1a2a47", "#243859", "#2e466b", "#38547d", "#42628f"]

# --- Meses em português ---
MESES_PT = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Março",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro",
}

MESES_ABREV = {
    1: "Jan",
    2: "Fev",
    3: "Mar",
    4: "Abr",
    5: "Mai",
    6: "Jun",
    7: "Jul",
    8: "Ago",
    9: "Set",
    10: "Out",
    11: "Nov",
    12: "Dez",
}
