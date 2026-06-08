"""CRUD da persistência: imports, tasks e monthly_metrics.

Todas as funções recebem a conexão explicitamente para facilitar testes com
banco em memória (``":memory:"``).
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime

import pandas as pd

from .. import config
from ..domain.indicators import Indicadores
from ..domain.normalize import normalizar_planejamento


@dataclass
class MonthlyMetrics:
    """Snapshot dos indicadores de uma competência (linha de monthly_metrics)."""

    period: str
    total_atividades: int
    planejadas_qtd: int
    nao_planejadas_qtd: int
    planejadas_perc: float
    cc_top_nome: str
    cc_top_perc: float
    produto_top_nome: str
    produto_top_perc: float
    tipo_top_nome: str
    tipo_top_perc: float


def _agora_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _iso_ou_none(valor):
    """Converte um valor de data para ISO string, ou None se ausente/inválido."""
    if valor is None or pd.isna(valor):
        return None
    if isinstance(valor, str):
        return valor
    return pd.Timestamp(valor).isoformat()


def salvar_importacao(
    conn: sqlite3.Connection, file_name: str, period: str, df: pd.DataFrame
) -> int:
    """Registra um upload em ``imports`` e retorna o ``import_id`` gerado."""
    cur = conn.execute(
        "INSERT INTO imports (file_name, period, imported_at, row_count) "
        "VALUES (?, ?, ?, ?)",
        (file_name, period, _agora_iso(), len(df)),
    )
    conn.commit()
    return int(cur.lastrowid)


def salvar_tarefas(
    conn: sqlite3.Connection, import_id: int, period: str, df: pd.DataFrame
) -> int:
    """Persiste as tarefas do ``period``, **substituindo** as já existentes.

    Conforme decidido: reimportar um mês apaga as tasks daquele period antes de
    inserir as novas, evitando duplicação. Retorna o nº de linhas inseridas.
    """
    conn.execute("DELETE FROM tasks WHERE period = ?", (period,))

    def get(row, coluna):
        valor = row.get(coluna)
        if valor is None or pd.isna(valor):
            return None
        return str(valor)

    registros = []
    for _, row in df.iterrows():
        planejamento = (
            normalizar_planejamento(row.get(config.COL_PLANEJAMENTO))
            if config.COL_PLANEJAMENTO in df.columns
            else None
        )
        raw = {k: (None if pd.isna(v) else str(v)) for k, v in row.items()}
        registros.append(
            (
                import_id,
                period,
                get(row, config.COL_TASK_NAME),
                get(row, config.COL_STATUS),
                get(row, config.COL_ASSIGNEE),
                get(row, config.COL_PRIORITY),
                get(row, config.COL_TASK_TYPE),
                get(row, config.COL_CENTRO_CUSTO),
                planejamento,
                get(row, config.COL_PRODUTO),
                get(row, config.COL_TIPO),
                _iso_ou_none(row.get("Due Date")),
                _iso_ou_none(row.get("Start Date")),
                _iso_ou_none(row.get("Date Created")),
                _iso_ou_none(row.get("Date Done")),
                json.dumps(raw, ensure_ascii=False),
            )
        )

    conn.executemany(
        "INSERT INTO tasks (import_id, period, task_name, status, assignee, "
        "priority, task_type, centro_custo, planejamento, produto, tipo, "
        "due_date, start_date, date_created, date_done, raw_json) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        registros,
    )
    conn.commit()
    return len(registros)


def upsert_metrics(
    conn: sqlite3.Connection, period: str, indicadores: Indicadores
) -> None:
    """Insere ou atualiza o snapshot de indicadores da competência (UNIQUE period)."""
    conn.execute(
        """
        INSERT INTO monthly_metrics (
            period, total_atividades, planejadas_qtd, nao_planejadas_qtd,
            planejadas_perc, cc_top_nome, cc_top_perc, produto_top_nome,
            produto_top_perc, tipo_top_nome, tipo_top_perc, computed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(period) DO UPDATE SET
            total_atividades   = excluded.total_atividades,
            planejadas_qtd     = excluded.planejadas_qtd,
            nao_planejadas_qtd = excluded.nao_planejadas_qtd,
            planejadas_perc    = excluded.planejadas_perc,
            cc_top_nome      = excluded.cc_top_nome,
            cc_top_perc      = excluded.cc_top_perc,
            produto_top_nome = excluded.produto_top_nome,
            produto_top_perc = excluded.produto_top_perc,
            tipo_top_nome    = excluded.tipo_top_nome,
            tipo_top_perc    = excluded.tipo_top_perc,
            computed_at      = excluded.computed_at
        """,
        (
            period,
            indicadores.total,
            indicadores.planejadas_qtd,
            indicadores.nao_planejadas_qtd,
            indicadores.planejadas_perc,
            indicadores.centro_custo.nome,
            indicadores.centro_custo.perc,
            indicadores.produto.nome,
            indicadores.produto.perc,
            indicadores.tipo.nome,
            indicadores.tipo.perc,
            _agora_iso(),
        ),
    )
    conn.commit()


def obter_metrics_ultimos_meses(
    conn: sqlite3.Connection, n: int = 3
) -> list[MonthlyMetrics]:
    """Retorna até ``n`` snapshots mais recentes, em ordem cronológica crescente."""
    rows = conn.execute(
        "SELECT * FROM monthly_metrics ORDER BY period DESC LIMIT ?", (n,)
    ).fetchall()
    metrics = [
        MonthlyMetrics(
            period=r["period"],
            total_atividades=r["total_atividades"],
            planejadas_qtd=r["planejadas_qtd"],
            nao_planejadas_qtd=r["nao_planejadas_qtd"] or 0,
            planejadas_perc=r["planejadas_perc"],
            cc_top_nome=r["cc_top_nome"],
            cc_top_perc=r["cc_top_perc"],
            produto_top_nome=r["produto_top_nome"],
            produto_top_perc=r["produto_top_perc"],
            tipo_top_nome=r["tipo_top_nome"],
            tipo_top_perc=r["tipo_top_perc"],
        )
        for r in rows
    ]
    metrics.reverse()
    return metrics


def listar_periodos(conn: sqlite3.Connection) -> list[str]:
    """Lista as competências com tarefas armazenadas, mais recentes primeiro."""
    rows = conn.execute(
        "SELECT DISTINCT period FROM tasks ORDER BY period DESC"
    ).fetchall()
    return [r["period"] for r in rows]


def reconstruir_df(conn: sqlite3.Connection, period: str) -> pd.DataFrame:
    """Reconstrói o DataFrame original (colunas do CSV) a partir de ``raw_json``.

    Permite re-renderizar gráficos/indicadores de uma competência já importada
    sem reupload do CSV. As colunas de data são reconvertidas para datetime.
    """
    rows = conn.execute(
        "SELECT raw_json FROM tasks WHERE period = ? ORDER BY id", (period,)
    ).fetchall()
    registros = [json.loads(r["raw_json"]) for r in rows]
    df = pd.DataFrame(registros)
    for col in config.DATE_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def listar_tarefas(
    conn: sqlite3.Connection, period: str | None = None
) -> pd.DataFrame:
    """Retorna as tarefas armazenadas, opcionalmente filtradas por ``period``."""
    if period:
        return pd.read_sql_query(
            "SELECT * FROM tasks WHERE period = ? ORDER BY id", conn, params=(period,)
        )
    return pd.read_sql_query("SELECT * FROM tasks ORDER BY id", conn)
