"""Cálculo de KPIs como dados NUMÉRICOS tipados.

O código antigo retornava strings já formatadas (``"Nome: 99.99%"``) e depois
fazia *parsing reverso* (`.split(':')`, `.replace('%','')`) para recuperar os
números — maior fonte de bugs. Aqui os indicadores são numéricos; a formatação é
responsabilidade exclusiva da camada de UI.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .. import config
from .normalize import PLANEJADO, NAO_PLANEJADO, normalizar_planejamento


@dataclass
class TopCategoria:
    """Categoria mais frequente de uma dimensão e seu percentual (0-100)."""

    nome: str
    perc: float


@dataclass
class Indicadores:
    """KPIs numéricos do conjunto de tarefas (já filtrado)."""

    total: int
    planejadas_qtd: int
    nao_planejadas_qtd: int
    planejadas_perc: float
    media_por_dev: float
    centro_custo: TopCategoria
    produto: TopCategoria
    tipo: TopCategoria


def _top_categoria(df: pd.DataFrame, coluna: str) -> TopCategoria:
    """Categoria mais frequente de ``coluna`` e seu % sobre os valores não-nulos."""
    if coluna not in df.columns:
        return TopCategoria("N/A", 0.0)
    contagem = df[coluna].dropna().value_counts()
    if contagem.empty:
        return TopCategoria("N/A", 0.0)
    nome = str(contagem.index[0])
    perc = (contagem.iloc[0] / contagem.sum()) * 100
    return TopCategoria(nome, float(perc))


def calcular_indicadores(df: pd.DataFrame) -> Indicadores:
    """Calcula os KPIs principais a partir de um DataFrame de tarefas."""
    planejadas_qtd = 0
    nao_planejadas_qtd = 0
    planejadas_perc = 0.0
    if config.COL_PLANEJAMENTO in df.columns:
        normalizado = df[config.COL_PLANEJAMENTO].apply(normalizar_planejamento)
        contagem = normalizado.value_counts()
        planejadas_qtd = int(contagem.get(PLANEJADO, 0))
        nao_planejadas_qtd = int(contagem.get(NAO_PLANEJADO, 0))
        denom = planejadas_qtd + nao_planejadas_qtd
        planejadas_perc = (planejadas_qtd / denom * 100) if denom > 0 else 0.0

    media_por_dev = 0.0
    if config.COL_ASSIGNEE in df.columns:
        devs_qtd = df[config.COL_ASSIGNEE].dropna().nunique()
        media_por_dev = (len(df) / devs_qtd) if devs_qtd > 0 else 0.0

    return Indicadores(
        total=len(df),
        planejadas_qtd=planejadas_qtd,
        nao_planejadas_qtd=nao_planejadas_qtd,
        planejadas_perc=planejadas_perc,
        media_por_dev=media_por_dev,
        centro_custo=_top_categoria(df, config.COL_CENTRO_CUSTO),
        produto=_top_categoria(df, config.COL_PRODUTO),
        tipo=_top_categoria(df, config.COL_TIPO),
    )
