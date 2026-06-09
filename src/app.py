"""Orquestração fina da aplicação Streamlit.

Substitui o `main.py` monolítico. Cada etapa (ler / validar / persistir / render)
tem tratamento de erro próprio, em vez do `try/except Exception` único do código
antigo.
"""

from __future__ import annotations

import streamlit as st

from . import config
from .charts import base  # configura rcParams e backend Agg
from .data import repository
from .data.db import get_conn, init_db
from .data.loader import carregar_csv
from .data.schema import SchemaError, validar_colunas
from .domain.indicators import calcular_indicadores
from .domain.period import competencia_atual, competencia_de, nome_mes
from .ui import history, pages, sidebar


def _persistir_importacao(conn, file_name, df, period) -> None:
    """Persiste tasks + snapshot de métricas do lote (uma vez por upload)."""
    indicadores_lote = calcular_indicadores(df)
    import_id = repository.salvar_importacao(conn, file_name, period, df)
    repository.salvar_tarefas(conn, import_id, period, df)
    repository.upsert_metrics(conn, period, indicadores_lote)


def main() -> None:
    st.set_page_config(
        page_title="Filtro de Tarefas",
        page_icon="📋",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    conn = get_conn()
    init_db(conn)

    st.title("📋 Filtro de Tarefas - By ClickUp - Tributo Justo")
    st.markdown("---")

    # --- Seleção de competência no topo ---
    OPCAO_UPLOAD = "📤 Importar novo CSV"
    periodos = repository.listar_periodos(conn)
    opcoes = [OPCAO_UPLOAD] + periodos
    escolha = st.selectbox(
        "Competência",
        opcoes,
        format_func=lambda o: o if o == OPCAO_UPLOAD else nome_mes(o),
        help="Escolha uma competência já importada para regerar os gráficos, "
        "ou importe um novo CSV.",
    )

    if escolha != OPCAO_UPLOAD:
        # Competência armazenada: reconstrói os dados e regera os gráficos.
        df = repository.reconstruir_df(conn, escolha)
        st.success(f"✅ Competência {nome_mes(escolha)} carregada — {len(df)} tarefas.")
        _render_dados(conn, df, escolha)
        return

    uploaded = st.file_uploader("Escolha o arquivo CSV", type=["csv"])

    if uploaded is None:
        st.info("👆 Por favor, faça o upload de um arquivo CSV para começar.")
        history.render_historico(conn)
        _rodape()
        return

    # --- Leitura ---
    try:
        df = carregar_csv(uploaded)
    except Exception as e:  # erro de parsing do CSV
        st.error(f"❌ Não foi possível ler o CSV: {e}")
        return

    # --- Validação de schema ---
    try:
        validar_colunas(df)
    except SchemaError as e:
        st.error(f"❌ {e}")
        return

    st.success(f"✅ Arquivo carregado com sucesso! Total de {len(df)} tarefas.")

    # --- Competência do lote (derivada de Date Created) ---
    period = competencia_de(df.get(config.COL_COMPETENCIA)) if config.COL_COMPETENCIA in df.columns else None
    if period is None:
        period = competencia_atual()

    # --- Persistência (uma vez por upload) ---
    if st.session_state.get("ultimo_upload") != uploaded.name:
        try:
            _persistir_importacao(conn, uploaded.name, df, period)
            st.session_state.ultimo_upload = uploaded.name
            st.success(f"💾 Importação salva ({period}). Tarefas e indicadores no histórico.")
        except Exception as e:
            st.warning(f"⚠️ Dados exibidos, mas falhou ao persistir no banco: {e}")

    _render_dados(conn, df, period)


def _render_dados(conn, df, period) -> None:
    """Renderiza filtros + todas as seções a partir de um DataFrame e competência."""
    df_filtrado = sidebar.render_filtros(df)
    indicadores = calcular_indicadores(df_filtrado)

    pages.secao_indicadores(indicadores, period)
    pages.secao_resumo(df_filtrado)
    pages.secao_contagens(df_filtrado)
    pages.secao_colaboradores(df_filtrado)
    pages.secao_graficos_principais(df_filtrado)

    metrics = repository.obter_metrics_ultimos_meses(conn, n=3)
    pages.secao_evolucao(metrics)

    history.render_historico(conn)
    _rodape()


def _rodape() -> None:
    with st.expander("ℹ️ Como usar"):
        st.markdown(
            """
            1. Faça upload do CSV exportado do ClickUp (tarefas e indicadores são
               salvos automaticamente no histórico).
            2. Use a barra lateral para aplicar filtros.
            3. Veja os indicadores, gráficos e contagens.
            4. A **Evolução Mensal** compara automaticamente os meses já importados
               (sem digitação manual).
            5. Consulte o **Histórico** para listar tarefas de competências anteriores.
            6. Exporte as tarefas filtradas em CSV.
            """
        )
    st.markdown("---")
    st.markdown(
        "### 💻 Desenvolvido por [Jhonatan Azevedo](https://linkedin.com/in/dev-azevedo)"
    )


if __name__ == "__main__":
    main()
