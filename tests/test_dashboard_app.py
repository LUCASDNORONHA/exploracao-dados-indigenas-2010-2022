from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from dashboard.charts.overview import (
    criar_grafico_composicao,
    criar_grafico_evolucao,
)
from dashboard.data import DadosDashboard, carregar_dados_dashboard
from dashboard.metrics import (
    calcular_indicadores_visao_geral,
    composicao_domiciliar_por_ano,
    composicao_territorial_por_ano,
    serie_populacao_por_ano,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def dados() -> DadosDashboard:
    """Carrega uma única vez a camada validada usada pela aplicação."""

    return carregar_dados_dashboard()


def test_carregador_respeita_contrato_compartilhado(
    dados: DadosDashboard,
) -> None:
    assert len(dados.fact_population) == 216
    assert len(dados.dim_geography) == 27
    assert len(dados.states_geojson["features"]) == 27
    assert len(dados.regions_geojson["features"]) == 5


def test_indicadores_nacionais_permanecem_estaveis(
    dados: DadosDashboard,
) -> None:
    indicadores = calcular_indicadores_visao_geral(dados.fact_population)

    assert indicadores.populacao_2010 == 896_917
    assert indicadores.populacao_2022 == 1_694_836
    assert indicadores.crescimento_absoluto == 797_919
    assert indicadores.crescimento_relativo == pytest.approx(797_919 / 896_917)
    assert indicadores.proporcao_urbana_2022 == pytest.approx(914_746 / 1_694_836)
    assert indicadores.proporcao_ti_2022 == pytest.approx(622_844 / 1_694_836)


def test_composicoes_somam_cem_por_cento_em_cada_ano(
    dados: DadosDashboard,
) -> None:
    domicilio = composicao_domiciliar_por_ano(dados.fact_population)
    territorio = composicao_territorial_por_ano(dados.fact_population)

    assert domicilio.groupby("ano")["proporcao"].sum().tolist() == pytest.approx(
        [1.0, 1.0]
    )
    assert territorio.groupby("ano")["proporcao"].sum().tolist() == pytest.approx(
        [1.0, 1.0]
    )


def test_figuras_possuem_estrutura_analitica_esperada(
    dados: DadosDashboard,
) -> None:
    serie = serie_populacao_por_ano(dados.fact_population)
    domicilio = composicao_domiciliar_por_ano(dados.fact_population)

    evolucao = criar_grafico_evolucao(serie, "Título")
    composicao = criar_grafico_composicao(domicilio, "Título")

    assert len(evolucao.data) == 1
    assert list(evolucao.data[0].x) == ["2010", "2022"]
    assert len(composicao.data) == 2
    assert composicao.layout.barmode == "stack"


def test_aplicacao_inicia_sem_excecoes() -> None:
    aplicacao = AppTest.from_file(
        ROOT / "streamlit_app.py",
        default_timeout=10,
    ).run()

    assert not aplicacao.exception
    assert len(aplicacao.metric) == 4
    assert len(aplicacao.selectbox) == 2
    assert aplicacao.selectbox[0].value == "Todas as localizações"
    assert aplicacao.selectbox[1].value == "Urbana e rural"

    aplicacao.selectbox(key="filtro_localizacao_visao_geral").select(
        "Em Terras Indígenas"
    )
    aplicacao.selectbox(key="filtro_domicilio_visao_geral").select("Rural")
    aplicacao.run()

    assert not aplicacao.exception
    assert aplicacao.metric[0].value == "552.858"
    assert aplicacao.metric[0].delta == "+12,5%"
