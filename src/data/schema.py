"""Validação de schema do CSV importado."""

import pandas as pd

from .. import config


class SchemaError(ValueError):
    """Erro de schema: colunas obrigatórias ausentes no CSV."""


def validar_colunas(df: pd.DataFrame) -> None:
    """Valida a presença das colunas obrigatórias.

    Levanta :class:`SchemaError` com mensagem clara listando as ausentes, em vez
    da falha silenciosa / ``KeyError`` do código antigo.
    """
    ausentes = [c for c in config.COLUNAS_OBRIGATORIAS if c not in df.columns]
    if ausentes:
        raise SchemaError(
            "Colunas obrigatórias ausentes no CSV: " + ", ".join(ausentes)
        )
