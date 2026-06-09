"""Tela de histórico: tarefas armazenadas e tendência de indicadores."""

from __future__ import annotations

import sqlite3

import pandas as pd
import streamlit as st

from ..data import repository


def _serie_metrics(metrics) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Competência": [m.period for m in metrics],
            "Total": [m.total_atividades for m in metrics],
            "Planejadas (%)": [round(m.planejadas_perc, 1) for m in metrics],
            "Centro de Custo (top)": [m.cc_top_nome for m in metrics],
            "Produto (top)": [m.produto_top_nome for m in metrics],
            "Tipo (top)": [m.tipo_top_nome for m in metrics],
        }
    )


def render_historico(conn: sqlite3.Connection) -> None:
    """Renderiza a seção de histórico (tarefas + métricas) a partir do SQLite."""
    st.markdown("---")
    st.markdown("## 🗂️ Histórico")

    periodos = repository.listar_periodos(conn)
    if not periodos:
        st.info("Nenhuma competência armazenada ainda. Importe um CSV para começar.")
        return

    # Série histórica de indicadores.
    metrics = repository.obter_metrics_ultimos_meses(conn, n=12)
    if metrics:
        st.markdown("### 📈 Tendência de Indicadores")
        serie = _serie_metrics(metrics)
        st.dataframe(serie, use_container_width=True, hide_index=True)
        st.line_chart(serie.set_index("Competência")[["Total"]])
