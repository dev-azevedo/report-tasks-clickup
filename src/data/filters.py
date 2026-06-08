"""Filtros puros sobre DataFrame.

Cada função recebe e retorna um DataFrame, sem mutar o original (fim da mutação
sequencial do mesmo `df` do código antigo). Composáveis e testáveis isoladamente.
"""

from __future__ import annotations

from datetime import date

import pandas as pd

from .. import config


def filtrar_periodo(
    df: pd.DataFrame, coluna: str, inicio: date, fim: date
) -> pd.DataFrame:
    """Mantém linhas cuja data em ``coluna`` esteja no intervalo [inicio, fim]."""
    if coluna not in df.columns:
        return df
    datas = pd.to_datetime(df[coluna], errors="coerce").dt.date
    mask = (datas >= inicio) & (datas <= fim)
    return df[mask]


def filtrar_dimensao(
    df: pd.DataFrame, coluna: str, selecionados: list[str]
) -> pd.DataFrame:
    """Mantém linhas cujo valor em ``coluna`` esteja em ``selecionados``.

    Lista vazia → sem filtro (retorna o DataFrame inalterado).
    """
    if not selecionados or coluna not in df.columns:
        return df
    return df[df[coluna].isin(selecionados)]


def buscar_nome(df: pd.DataFrame, texto: str) -> pd.DataFrame:
    """Filtra por substring (case-insensitive) no nome da tarefa."""
    if not texto or config.COL_TASK_NAME not in df.columns:
        return df
    mask = df[config.COL_TASK_NAME].str.contains(texto, case=False, na=False)
    return df[mask]
