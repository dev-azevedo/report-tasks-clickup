import pandas as pd
import pytest

from src import config
from src.data import db, repository
from src.domain.indicators import calcular_indicadores


@pytest.fixture
def conn():
    c = db.get_conn(":memory:")
    db.init_db(c)
    yield c
    c.close()


def _df(centro="TI"):
    return pd.DataFrame(
        {
            config.COL_TASK_NAME: ["a", "b"],
            config.COL_CENTRO_CUSTO: [centro, centro],
            config.COL_PLANEJAMENTO: ["Planejado", "Não Planejado"],
            "Date Created": pd.to_datetime(["2026-05-01", "2026-05-02"]),
        }
    )


def test_salvar_importacao_e_tarefas(conn):
    df = _df()
    import_id = repository.salvar_importacao(conn, "f.csv", "2026-05", df)
    assert import_id == 1
    n = repository.salvar_tarefas(conn, import_id, "2026-05", df)
    assert n == 2
    armazenadas = repository.listar_tarefas(conn, "2026-05")
    assert len(armazenadas) == 2
    assert armazenadas.iloc[0]["centro_custo"] == "TI"


def test_reimport_substitui_periodo(conn):
    df1 = _df("TI")
    imp1 = repository.salvar_importacao(conn, "f1.csv", "2026-05", df1)
    repository.salvar_tarefas(conn, imp1, "2026-05", df1)

    # Reimporta o mesmo período: substitui, não acumula.
    df2 = _df("RH")
    imp2 = repository.salvar_importacao(conn, "f2.csv", "2026-05", df2)
    repository.salvar_tarefas(conn, imp2, "2026-05", df2)

    armazenadas = repository.listar_tarefas(conn, "2026-05")
    assert len(armazenadas) == 2
    assert set(armazenadas["centro_custo"]) == {"RH"}


def test_upsert_metrics_atualiza(conn):
    ind = calcular_indicadores(_df())
    repository.upsert_metrics(conn, "2026-05", ind)
    repository.upsert_metrics(conn, "2026-05", ind)  # idempotente
    metrics = repository.obter_metrics_ultimos_meses(conn, 3)
    assert len(metrics) == 1
    assert metrics[0].period == "2026-05"
    assert metrics[0].planejadas_qtd == 1


def test_obter_metrics_ordem_crescente(conn):
    for period in ["2026-03", "2026-05", "2026-04"]:
        repository.upsert_metrics(conn, period, calcular_indicadores(_df()))
    metrics = repository.obter_metrics_ultimos_meses(conn, 3)
    assert [m.period for m in metrics] == ["2026-03", "2026-04", "2026-05"]
