import pandas as pd

from src import config
from src.domain.indicators import Indicadores, calcular_indicadores


def _df():
    return pd.DataFrame(
        {
            config.COL_TASK_NAME: ["a", "b", "c", "d"],
            config.COL_CENTRO_CUSTO: ["TI", "TI", "TI", "RH"],
            config.COL_PRODUTO: ["X", "X", "Y", "Y"],
            config.COL_TIPO: ["Bug", "Bug", "Bug", "Feature"],
            config.COL_PLANEJAMENTO: [
                "Planejado",
                "Planejado",
                "Não Planejado",
                None,
            ],
        }
    )


def test_total():
    ind = calcular_indicadores(_df())
    assert isinstance(ind, Indicadores)
    assert ind.total == 4


def test_top_categoria_e_percentual():
    ind = calcular_indicadores(_df())
    assert ind.centro_custo.nome == "TI"
    assert ind.centro_custo.perc == 75.0  # 3 de 4 não-nulos


def test_planejadas_perc_ignora_outros():
    ind = calcular_indicadores(_df())
    # 2 Planejado, 1 Não Planejado, 1 None(Outros) → 2/(2+1) = 66.67%
    assert ind.planejadas_qtd == 2
    assert round(ind.planejadas_perc, 2) == 66.67


def test_colunas_ausentes_nao_quebram():
    ind = calcular_indicadores(pd.DataFrame({config.COL_TASK_NAME: ["a"]}))
    assert ind.total == 1
    assert ind.centro_custo.nome == "N/A"
    assert ind.planejadas_qtd == 0
    assert ind.planejadas_perc == 0.0
