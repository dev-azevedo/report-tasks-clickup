"""Widgets de filtro da sidebar. Aplica os filtros puros de ``data/filters``."""

from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from .. import config
from ..data import filters


def _filtro_dimensao(df: pd.DataFrame, label: str, coluna: str) -> pd.DataFrame:
    if coluna not in df.columns:
        return df
    opcoes = sorted(df[coluna].dropna().unique().tolist())
    selecionados = st.sidebar.multiselect(label, opcoes)
    return filters.filtrar_dimensao(df, coluna, selecionados)


def render_filtros(df: pd.DataFrame) -> pd.DataFrame:
    """Renderiza os filtros e retorna o DataFrame filtrado."""
    st.sidebar.header("🔍 Filtros")

    st.sidebar.subheader("Período")
    coluna_data = st.sidebar.selectbox(
        "Filtrar por data de:", ["Selecione..."] + config.DATE_COLUMNS, index=0
    )
    if coluna_data != "Selecione...":
        c1, c2 = st.sidebar.columns(2)
        fim_default = datetime.now().date()
        inicio_default = fim_default - timedelta(days=30)
        inicio = c1.date_input("Data inicial", value=inicio_default)
        fim = c2.date_input("Data final", value=fim_default)
        df = filters.filtrar_periodo(df, coluna_data, inicio, fim)

    df = _filtro_dimensao(df, "Status", config.COL_STATUS)
    df = _filtro_dimensao(df, "Prioridade", config.COL_PRIORITY)
    df = _filtro_dimensao(df, "Responsável", config.COL_ASSIGNEE)
    df = _filtro_dimensao(df, "Tipo de Tarefa", config.COL_TASK_TYPE)
    df = _filtro_dimensao(df, "Centro de Custo", config.COL_CENTRO_CUSTO)
    df = _filtro_dimensao(df, "Planejamento", config.COL_PLANEJAMENTO)
    df = _filtro_dimensao(df, "Produto", config.COL_PRODUTO)
    df = _filtro_dimensao(df, "Tipo", config.COL_TIPO)

    st.sidebar.subheader("🔎 Busca")
    texto = st.sidebar.text_input("Buscar no nome da tarefa")
    df = filters.buscar_nome(df, texto)

    return df
