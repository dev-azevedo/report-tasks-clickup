"""Leitura do CSV do ClickUp com parsing de datas."""

import pandas as pd

from .. import config


def carregar_csv(arquivo) -> pd.DataFrame:
    """Lê o CSV e converte as colunas de data para datetime.

    ``arquivo`` pode ser um caminho ou um objeto file-like (ex.: o retorno de
    ``st.file_uploader``).
    """
    df = pd.read_csv(arquivo)
    for col in config.DATE_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df
