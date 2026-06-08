"""Cálculo de competência (period ``YYYY-MM``) e nomes de meses em PT.

Substitui a tradução de meses por `.replace()` encadeado do código antigo, que
dependia do locale do sistema e era frágil.
"""

from __future__ import annotations

from datetime import date

import pandas as pd
from dateutil.relativedelta import relativedelta

from .. import config


def competencia_atual(hoje: date | None = None) -> str:
    """Retorna a competência do mês corrente como ``YYYY-MM``."""
    hoje = hoje or date.today()
    return f"{hoje.year:04d}-{hoje.month:02d}"


def competencia_de(serie_data: pd.Series) -> str | None:
    """Deriva a competência dominante de uma série de datas (``Date Created``).

    Usa a moda das competências presentes. Retorna ``None`` se não houver datas
    válidas.
    """
    datas = pd.to_datetime(serie_data, errors="coerce").dropna()
    if datas.empty:
        return None
    periods = datas.dt.strftime("%Y-%m")
    return periods.mode().iloc[0]


def nome_mes(period: str) -> str:
    """Converte ``YYYY-MM`` em ``"Mês / YYYY"`` (mês por extenso em PT)."""
    ano, mes = period.split("-")
    return f"{config.MESES_PT[int(mes)]} / {ano}"


def abrev_mes(period: str) -> str:
    """Converte ``YYYY-MM`` na abreviação do mês em PT (ex.: ``"Jun"``)."""
    _, mes = period.split("-")
    return config.MESES_ABREV[int(mes)]


def ultimos_n_meses(n: int, base: date | None = None) -> list[str]:
    """Lista as ``n`` competências mais recentes até ``base`` (default: hoje).

    Ordem cronológica crescente. Ex.: ``ultimos_n_meses(3)`` →
    ``['2026-04', '2026-05', '2026-06']``.
    """
    base = base or date.today()
    periods = []
    for i in range(n - 1, -1, -1):
        d = base - relativedelta(months=i)
        periods.append(f"{d.year:04d}-{d.month:02d}")
    return periods
