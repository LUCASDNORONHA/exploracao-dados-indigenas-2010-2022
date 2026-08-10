"""Testes da camada estadual do dashboard."""

import pandas as pd
import pytest

from dashboard.charts.state import (
    criar_comparacao_referencias,
    criar_composicao_uf,
    criar_evolucao_uf,
)
from dashboard.state import (
    calcular_composicao_uf,
    calcular_indicadores_uf,
    calcular_perfil_estadual,
    calcular_referencias_2022,
)


@pytest.fixture
def geografia():
    return pd.DataFrame(
        {
            "uf_id": ["11", "12", "21"],
            "uf": ["Rondônia", "Acre", "Maranhão"],
            "sigla_uf": ["RO", "AC", "MA"],
            "regiao_id": [1, 1, 2],
            "regiao": ["Norte", "Norte", "Nordeste"],
            "ordem_regiao": [1, 1, 2],
        }
    )


@pytest.fixture
def fato():
    linhas = []
    valores = {
        (11, 2010): [10, 20, 30, 40],
        (12, 2010): [5, 15, 20, 10],
        (21, 2010): [10, 10, 20, 20],
        (11, 2022): [20, 40, 60, 80],
        (12, 2022): [10, 30, 40, 20],
        (21, 2022): [20, 20, 30, 30],
    }
    combinacoes = [(1, 1), (1, 2), (2, 1), (2, 2)]
    for (uf_id, ano), populacoes in valores.items():
        for (localizacao, domicilio), populacao in zip(combinacoes, populacoes, strict=True):
            linhas.append(
                {
                    "uf_id": uf_id,
                    "ano": ano,
                    "localizacao_id": localizacao,
                    "domicilio_id": domicilio,
                    "populacao_indigena": populacao,
                }
            )
    return pd.DataFrame(linhas)


def test_perfil_estadual_agrega_granularidade(fato, geografia):
    perfil = calcular_perfil_estadual(fato, geografia)
    assert len(perfil) == 6
    assert perfil.loc[(perfil["uf_id"] == "11") & (perfil["ano"] == 2022), "populacao_indigena"].iloc[0] == 200


def test_indicadores_uf_calculam_crescimento_e_ranking(fato, geografia):
    perfil = calcular_perfil_estadual(fato, geografia)
    indicadores = calcular_indicadores_uf(perfil, 11)
    assert indicadores["populacao_2010"] == 100
    assert indicadores["populacao_2022"] == 200
    assert indicadores["crescimento_relativo"] == pytest.approx(1.0)
    assert indicadores["ranking_brasil"] == 1
    assert indicadores["ranking_regiao"] == 1


def test_composicao_estadual_fecha_cem_por_cento(fato):
    composicao = calcular_composicao_uf(fato, 11, "domicilio")
    assert composicao.groupby("ano")["proporcao"].sum().tolist() == pytest.approx([1, 1])


def test_referencias_incluem_uf_regiao_e_brasil(fato, geografia):
    perfil = calcular_perfil_estadual(fato, geografia)
    referencias = calcular_referencias_2022(perfil, 11)
    assert len(referencias) == 3
    assert referencias.iloc[0]["referencia"] == "Rondônia (RO)"
    assert referencias.iloc[0]["populacao_indigena"] == 200


def test_dimensao_invalida_gera_erro(fato):
    with pytest.raises(ValueError):
        calcular_composicao_uf(fato, 11, "invalida")


def test_graficos_estaduais_sao_construidos(fato, geografia):
    perfil = calcular_perfil_estadual(fato, geografia)
    serie = perfil.loc[perfil["uf_id"] == "11"]
    referencias = calcular_referencias_2022(perfil, 11)
    composicao = calcular_composicao_uf(fato, 11, "localizacao")

    evolucao = criar_evolucao_uf(serie, "Evolução")
    comparacao = criar_comparacao_referencias(referencias, "Referências")
    composicao_fig = criar_composicao_uf(composicao, "Composição")

    assert len(evolucao.data) == 1
    assert len(comparacao.data) == 1
    assert len(composicao_fig.data) == 2
    assert evolucao.layout.height == 390
