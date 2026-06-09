"""Componentes de card KPI. Formatação dos indicadores numéricos vive aqui."""

from __future__ import annotations

import streamlit as st

from ..domain.indicators import Indicadores, TopCategoria


def _card(titulo: str, conteudo: str) -> str:
    return f"""
    <div style="background-color: #f0f2f6; padding: 30px; border-radius: 15px; text-align: center;">
        <h3 style="color: #1a3a52; margin-bottom: 10px;">{titulo}</h3>
        <p style="font-size: 18px; color: #666; margin: 0;">{conteudo}</p>
    </div>
    """


def _fmt(top: TopCategoria) -> str:
    if top.nome == "N/A":
        return "N/A"
    return f"{top.nome}: {top.perc:.2f}%"


def render_cards(indicadores: Indicadores, periodo_label: str) -> None:
    """Renderiza os cards de KPI a partir dos indicadores numéricos."""
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(_card("Atividades", f"Total: {indicadores.total}"), unsafe_allow_html=True)
    with col2:
        st.markdown(_card("Centro de Custo", _fmt(indicadores.centro_custo)), unsafe_allow_html=True)
    with col3:
        st.markdown(_card("Produto", _fmt(indicadores.produto)), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col4, col5, col6 = st.columns(3)
    planejadas = f"Planejadas: {indicadores.planejadas_qtd} ({indicadores.planejadas_perc:.2f}%)"
    with col4:
        st.markdown(_card("Atividades Planejadas", planejadas), unsafe_allow_html=True)
    with col5:
        st.markdown(_card("Atividades por Tipo", _fmt(indicadores.tipo)), unsafe_allow_html=True)
    with col6:
        media = f"Média: {indicadores.media_por_dev:.2f}"
        st.markdown(_card("Atividades por Desenvolvedor", media), unsafe_allow_html=True)

    st.markdown(
        f"""<p style="text-align: left; color: #888; margin-top: 20px; font-size: 16px;">
        {periodo_label}</p>""",
        unsafe_allow_html=True,
    )
