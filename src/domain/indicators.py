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


def metricas_por_colaborador(df: pd.DataFrame) -> pd.DataFrame:
    """Métricas por Assignee p/ feedback: volume, % planejado, alta prioridade, produção.

    Retorna DataFrame ordenado por Total desc. Vazio se não houver coluna de Assignee.
    """
    if config.COL_ASSIGNEE not in df.columns:
        return pd.DataFrame()

    linhas = []
    for colaborador, grupo in df.dropna(subset=[config.COL_ASSIGNEE]).groupby(
        config.COL_ASSIGNEE
    ):
        total = len(grupo)

        planejado_perc = 0.0
        if config.COL_PLANEJAMENTO in grupo.columns:
            normalizado = grupo[config.COL_PLANEJAMENTO].apply(normalizar_planejamento)
            contagem = normalizado.value_counts()
            plan = int(contagem.get(PLANEJADO, 0))
            nao_plan = int(contagem.get(NAO_PLANEJADO, 0))
            denom = plan + nao_plan
            planejado_perc = (plan / denom * 100) if denom > 0 else 0.0

        alta = 0
        if config.COL_PRIORITY in grupo.columns:
            alta = int(
                grupo[config.COL_PRIORITY]
                .str.contains("urgent|high", case=False, na=False)
                .sum()
            )

        producao = 0
        if config.COL_STATUS in grupo.columns:
            producao = int(
                grupo[config.COL_STATUS]
                .str.contains("Produção", case=False, na=False)
                .sum()
            )

        linhas.append(
            {
                "Colaborador": str(colaborador),
                "Total": total,
                "Planejado (%)": round(planejado_perc, 1),
                "Alta Prioridade": alta,
                "Produção": producao,
            }
        )

    return (
        pd.DataFrame(linhas)
        .sort_values("Total", ascending=False)
        .reset_index(drop=True)
    )


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
