"""Testes da camada regional do dashboard."""

import pandas as pd
import pytest

from dashboard.charts.regional import (
    criar_comparacao_regional,
    criar_composicao_regional,
    criar_ranking_crescimento,
)
from dashboard.regional import (
    calcular_composicao_regional,
    calcular_crescimento_regional,
    calcular_perfil_regional,
)


@pytest.fixture
def geografia():
    return pd.DataFrame(
        {
            "uf_id": [11, 12, 21],
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


def test_perfil_regional_agrega_ufs_e_fecha_participacao(fato, geografia):
    perfil = calcular_perfil_regional(fato, geografia)
    assert len(perfil) == 4
    assert perfil.groupby("ano")["participacao_brasil"].sum().tolist() == pytest.approx([1, 1])


def test_crescimento_regional(fato, geografia):
    perfil = calcular_perfil_regional(fato, geografia)
    crescimento = calcular_crescimento_regional(perfil)
    norte = crescimento.loc[crescimento["regiao"] == "Norte"].iloc[0]
    assert norte[2010] == 150
    assert norte[2022] == 300
    assert norte["crescimento_absoluto"] == 150
    assert norte["crescimento_relativo"] == pytest.approx(1.0)


def test_composicao_regional_fecha_cem_por_cento(fato, geografia):
    composicao = calcular_composicao_regional(fato, geografia, "domicilio", 2022)
    totais = composicao.groupby("regiao")["proporcao"].sum()
    assert totais.tolist() == pytest.approx([1, 1])


def test_dimensao_invalida_gera_erro(fato, geografia):
    with pytest.raises(ValueError):
        calcular_composicao_regional(fato, geografia, "invalida", 2022)


def test_graficos_regionais_sao_construidos(fato, geografia):
    perfil = calcular_perfil_regional(fato, geografia)
    crescimento = calcular_crescimento_regional(perfil)
    composicao = calcular_composicao_regional(fato, geografia, "localizacao", 2022)

    comparacao = criar_comparacao_regional(perfil, "Comparação")
    ranking = criar_ranking_crescimento(crescimento, "Crescimento")
    composicao_fig = criar_composicao_regional(composicao, "Composição")

    assert len(comparacao.data) == 2
    assert len(ranking.data) == 1
    assert len(composicao_fig.data) == 2
    assert comparacao.layout.height == 430
