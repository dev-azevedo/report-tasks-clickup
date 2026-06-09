"""Composição das seções da página principal."""

from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from .. import config
from ..charts.base import fig_para_png
from ..charts.builders import grafico_barras_horizontal, graficos_principais
from ..charts.evolution import graficos_evolucao
from ..data.repository import MonthlyMetrics
from ..domain.indicators import Indicadores, metricas_por_colaborador
from ..domain.period import nome_mes
from . import cards


def secao_indicadores(indicadores: Indicadores, period: str) -> None:
    st.markdown("---")
    st.markdown("## 🎯 Impacto dos Indicadores")
    cards.render_cards(indicadores, nome_mes(period))


def secao_resumo(df: pd.DataFrame) -> None:
    st.markdown("---")
    st.subheader(f"📊 Resultados: {len(df)} tarefas encontradas")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total de Tarefas", len(df))
    if config.COL_STATUS in df.columns:
        prod = len(df[df[config.COL_STATUS].str.contains("Produção", case=False, na=False)])
        c2.metric("Produção", prod)
    if config.COL_PRIORITY in df.columns:
        high = len(df[df[config.COL_PRIORITY].str.contains("urgent|high", case=False, na=False)])
        c3.metric("Alta Prioridade", high)
    if config.COL_ASSIGNEE in df.columns:
        c4.metric("Responsáveis", df[config.COL_ASSIGNEE].nunique())


def secao_contagens(df: pd.DataFrame) -> None:
    st.markdown("### 📂 Informações Relevantes")

    def contagem(coluna, titulo):
        if coluna in df.columns:
            tabela = df[coluna].value_counts().reset_index()
            tabela.columns = [coluna, "Quantidade"]
            st.markdown(f"#### {titulo}")
            st.dataframe(tabela, use_container_width=True, height=200)

    colA, colB = st.columns(2)
    with colA:
        contagem(config.COL_CENTRO_CUSTO, "Atividades por Centro de Custo")
        contagem(config.COL_PLANEJAMENTO, "Atividades por Planejamento")
    with colB:
        contagem(config.COL_PRODUTO, "Atividades por Produto")
        contagem(config.COL_TIPO, "Atividades por Tipo")


def secao_colaboradores(df: pd.DataFrame) -> None:
    st.markdown("---")
    st.markdown("## 👥 Colaboradores")
    st.caption(
        "Métricas por responsável para apoiar feedbacks e 1:1: volume de entregas, "
        "disciplina de planejamento, carga de alta prioridade e itens em produção."
    )
    metricas = metricas_por_colaborador(df)
    if metricas.empty:
        st.info("Sem coluna de responsável para gerar métricas por colaborador.")
        return
    st.dataframe(metricas, use_container_width=True, hide_index=True)

    fig = grafico_barras_horizontal(df, config.COL_ASSIGNEE, "Tarefas por Colaborador")
    if fig:
        _render_grafico("Tarefas por Colaborador", fig, key="dl_colab_0")


def _nome_arquivo(titulo: str) -> str:
    seguro = "".join(c if c.isalnum() else "_" for c in titulo).strip("_")
    return seguro or "grafico"


def _render_grafico(titulo, fig, key: str) -> None:
    """Renderiza a figura e oferece botão de download PNG (para apresentações)."""
    st.pyplot(fig)
    st.caption(titulo)
    st.download_button(
        "📥 Baixar PNG",
        data=fig_para_png(fig),
        file_name=f"{_nome_arquivo(titulo)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
        mime="image/png",
        key=key,
    )


def secao_graficos_principais(df: pd.DataFrame) -> None:
    st.markdown("---")
    with st.expander("📊 Gráficos Principais", expanded=False):
        graficos = graficos_principais(df)
        if not graficos:
            st.info("Sem colunas suficientes para gerar gráficos.")
            return
        cols = st.columns(2)
        for idx, (titulo, fig) in enumerate(graficos):
            with cols[idx % 2]:
                _render_grafico(titulo, fig, key=f"dl_principal_{idx}")


def secao_evolucao(metrics: list[MonthlyMetrics]) -> None:
    st.markdown("---")
    with st.expander("📈 Evolução Mensal", expanded=False):
        if len(metrics) < 2:
            st.info(
                "A evolução é montada automaticamente a partir dos meses já importados. "
                "Importe ao menos 2 competências diferentes para ver os gráficos comparativos."
            )
            return
        st.caption(
            "Meses anteriores carregados automaticamente do histórico (SQLite) — "
            "sem digitação manual."
        )
        graficos = graficos_evolucao(metrics)
        cols = st.columns(2)
        for idx, (titulo, fig) in enumerate(graficos):
            with cols[idx % 2]:
                _render_grafico(titulo, fig, key=f"dl_evolucao_{idx}")
