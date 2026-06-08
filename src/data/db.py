"""Conexão SQLite e criação de schema.

Migrations simples via ``CREATE TABLE IF NOT EXISTS`` (sem versionamento ainda,
conforme decidido na refatoração).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from .. import config

_SCHEMA = """
CREATE TABLE IF NOT EXISTS imports (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name   TEXT,
    period      TEXT,
    imported_at TEXT,
    row_count   INTEGER
);

CREATE TABLE IF NOT EXISTS tasks (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    import_id     INTEGER REFERENCES imports(id),
    period        TEXT,
    task_name     TEXT,
    status        TEXT,
    assignee      TEXT,
    priority      TEXT,
    task_type     TEXT,
    centro_custo  TEXT,
    planejamento  TEXT,
    produto       TEXT,
    tipo          TEXT,
    due_date      TEXT,
    start_date    TEXT,
    date_created  TEXT,
    date_done     TEXT,
    raw_json      TEXT
);

CREATE TABLE IF NOT EXISTS monthly_metrics (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    period            TEXT UNIQUE,
    total_atividades  INTEGER,
    planejadas_qtd    INTEGER,
    nao_planejadas_qtd INTEGER,
    planejadas_perc   REAL,
    cc_top_nome       TEXT,
    cc_top_perc       REAL,
    produto_top_nome  TEXT,
    produto_top_perc  REAL,
    tipo_top_nome     TEXT,
    tipo_top_perc     REAL,
    computed_at       TEXT
);

CREATE INDEX IF NOT EXISTS idx_tasks_period ON tasks(period);
"""


def get_conn(db_path: str | Path | None = None) -> sqlite3.Connection:
    """Abre uma conexão SQLite. ``db_path`` default = ``config.DB_PATH``.

    Use ``":memory:"`` em testes. Habilita ``Row`` para acesso por nome.
    """
    if db_path is None:
        db_path = config.DB_PATH
    if db_path != ":memory:":
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    """Cria as tabelas se ainda não existirem e aplica migrations simples."""
    conn.executescript(_SCHEMA)
    _migrar(conn)
    conn.commit()


def _migrar(conn: sqlite3.Connection) -> None:
    """Migrations idempotentes para bancos criados antes de novas colunas."""
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(monthly_metrics)")}
    if "nao_planejadas_qtd" not in cols:
        conn.execute("ALTER TABLE monthly_metrics ADD COLUMN nao_planejadas_qtd INTEGER")
