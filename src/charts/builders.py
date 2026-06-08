"""Builders dos gráficos principais. Retornam ``Figure`` (render via st.pyplot).

A ``gerar_grafico_pizza`` do código antigo (nunca chamada) foi removida.
"""

from __future__ import annotations

import pandas as pd

from .. import config
from ..domain.normalize import NAO_PLANEJADO, PLANEJADO, normalizar_planejamento
from .base import limpar_spines, nova_figura


def grafico_barras(df: pd.DataFrame, coluna: str, titulo: str):
    """Barras verticais a partir de ``value_counts()`` da coluna."""
    if coluna not in df.columns:
        return None
    contagem = df[coluna].value_counts().sort_values(ascending=False)
    if contagem.empty:
        return None

    fig, ax = nova_figura()
    bars = ax.bar(range(len(contagem)), contagem.values, color=config.COR_PRIMARIA, width=0.6)
    for bar, valor in zip(bars, contagem.values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.5,
            str(valor),
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
        )
    ax.set_xticks(range(len(contagem)))
    ax.set_xticklabels(contagem.index, rotation=45, ha="right")
    ax.set_title(titulo, pad=20)
    ax.set_ylim(0, max(contagem.values) * 1.15)
    ax.set_yticks([])
    limpar_spines(ax)
    ax.grid(axis="y", alpha=0.3, linestyle="--")
    fig.tight_layout()
    return fig


def grafico_barras_horizontal(df: pd.DataFrame, coluna: str, titulo: str):
    """Barras horizontais a partir de ``value_counts()`` da coluna."""
    if coluna not in df.columns:
        return None
    contagem = df[coluna].value_counts().sort_values(ascending=True)
    if contagem.empty:
        return None

    fig, ax = nova_figura()
    bars = ax.barh(range(len(contagem)), contagem.values, color=config.COR_PRIMARIA, height=0.6)
    for bar, valor in zip(bars, contagem.values):
        ax.text(
            bar.get_width() + max(contagem.values) * 0.02,
            bar.get_y() + bar.get_height() / 2,
            str(valor),
            ha="left",
            va="center",
            fontsize=10,
            fontweight="bold",
        )
    ax.set_yticks(range(len(contagem)))
    ax.set_yticklabels(contagem.index)
    ax.set_title(titulo, pad=20)
    ax.set_xlim(0, max(contagem.values) * 1.15)
    ax.set_xticks([])
    limpar_spines(ax)
    ax.grid(axis="x", alpha=0.3, linestyle="--")
    fig.tight_layout()
    return fig


def grafico_comparativo(df: pd.DataFrame, coluna: str, titulo: str):
    """Barras Planejado × Não Planejado usando a normalização única."""
    if coluna not in df.columns:
        return None
    normalizado = df[coluna].apply(normalizar_planejamento)
    contagem = normalizado.value_counts().reindex(
        [PLANEJADO, NAO_PLANEJADO], fill_value=0
    )
    total = contagem.sum()
    if total == 0:
        return None

    cores = [config.COR_PRIMARIA, config.COR_SECUNDARIA]
    fig, ax = nova_figura()
    bars = ax.bar(range(len(contagem)), contagem.values, color=cores, width=0.5)
    for bar, valor in zip(bars, contagem.values):
        perc = (valor / total) * 100 if total > 0 else 0
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max(contagem.values) * 0.02,
            f"{valor}\n({perc:.1f}%)",
            ha="center",
            va="bottom",
            fontsize=12,
            fontweight="bold",
        )
    ax.set_xticks(range(len(contagem)))
    ax.set_xticklabels([PLANEJADO, NAO_PLANEJADO], fontsize=13, fontweight="bold")
    ax.set_title(titulo, pad=20)
    ax.set_ylim(0, max(contagem.values) * 1.25)
    ax.set_yticks([])
    limpar_spines(ax)
    ax.grid(axis="y", alpha=0.3, linestyle="--")
    fig.tight_layout()
    return fig


def graficos_principais(df: pd.DataFrame) -> list[tuple[str, object]]:
    """Monta os gráficos principais. Retorna lista de ``(titulo, fig)``."""
    resultado = []
    for coluna, titulo in [
        (config.COL_CENTRO_CUSTO, "Centro de Custo"),
        (config.COL_PRODUTO, "Produto"),
    ]:
        fig = grafico_barras(df, coluna, titulo)
        if fig:
            resultado.append((titulo, fig))

    fig = grafico_comparativo(df, config.COL_PLANEJAMENTO, "Planejadas")
    if fig:
        resultado.append(("Planejamento", fig))

    fig = grafico_barras_horizontal(df, config.COL_TIPO, "Distribuição por Tipo")
    if fig:
        resultado.append(("Tipo", fig))

    return resultado
