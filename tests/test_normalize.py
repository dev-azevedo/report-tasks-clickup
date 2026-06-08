import numpy as np
import pytest

from src.domain.normalize import (
    NAO_PLANEJADO,
    OUTROS,
    PLANEJADO,
    normalizar_planejamento,
)


@pytest.mark.parametrize(
    "entrada,esperado",
    [
        ("Planejado", PLANEJADO),
        ("planejada", PLANEJADO),
        ("Atividade Planejada", PLANEJADO),
        ("Não Planejado", NAO_PLANEJADO),
        ("Nao planejado", NAO_PLANEJADO),
        ("não planejada", NAO_PLANEJADO),
        ("Outra coisa", OUTROS),
        ("", OUTROS),
    ],
)
def test_normalizacao_categorias(entrada, esperado):
    assert normalizar_planejamento(entrada) == esperado


def test_nan_vira_outros():
    # NaN é mapeado de forma única para 'Outros' (resolve inconsistência antiga).
    assert normalizar_planejamento(np.nan) == OUTROS
    assert normalizar_planejamento(None) == OUTROS
