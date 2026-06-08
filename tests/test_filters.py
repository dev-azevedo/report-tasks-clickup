from datetime import date

import pandas as pd

from src import config
from src.data.filters import buscar_nome, filtrar_dimensao, filtrar_periodo


def _df():
    return pd.DataFrame(
        {
            config.COL_TASK_NAME: ["Corrigir bug", "Nova feature", "Refatorar"],
            config.COL_STATUS: ["Aberto", "Produção", "Aberto"],
            "Date Created": pd.to_datetime(
                ["2026-01-10", "2026-02-15", "2026-03-20"]
            ),
        }
    )


def test_filtrar_periodo():
    out = filtrar_periodo(_df(), "Date Created", date(2026, 2, 1), date(2026, 2, 28))
    assert len(out) == 1
    assert out.iloc[0][config.COL_TASK_NAME] == "Nova feature"


def test_filtrar_dimensao():
    out = filtrar_dimensao(_df(), config.COL_STATUS, ["Aberto"])
    assert len(out) == 2


def test_filtrar_dimensao_vazio_nao_filtra():
    df = _df()
    assert len(filtrar_dimensao(df, config.COL_STATUS, [])) == 3


def test_buscar_nome_case_insensitive():
    out = buscar_nome(_df(), "bug")
    assert len(out) == 1
    assert out.iloc[0][config.COL_TASK_NAME] == "Corrigir bug"


def test_buscar_nome_vazio_nao_filtra():
    assert len(buscar_nome(_df(), "")) == 3


def test_filtros_nao_mutam_original():
    df = _df()
    filtrar_dimensao(df, config.COL_STATUS, ["Aberto"])
    assert len(df) == 3
