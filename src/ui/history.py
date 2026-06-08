"""Tela de histórico: tarefas armazenadas e tendência de indicadores."""

from __future__ import annotations

import sqlite3
from datetime import datetime

import pandas as pd
import streamlit as st

from ..data import repository
from ..domain.period import nome_mes


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

    # Listagem de tarefas por competência.
    st.markdown("### 📋 Tarefas Armazenadas")
    period = st.selectbox(
        "Competência",
        periodos,
        format_func=nome_mes,
    )
    tarefas = repository.listar_tarefas(conn, period)
    st.caption(f"{len(tarefas)} tarefas em {nome_mes(period)}")
    st.dataframe(tarefas, use_container_width=True, height=400)

    csv = tarefas.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Exportar histórico (CSV)",
        data=csv,
        file_name=f"historico_{period}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
    )
