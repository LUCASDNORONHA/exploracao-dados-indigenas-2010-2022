import pandas as pd
import pytest

from dashboard.charts.spatial import criar_mapa_estadual, criar_ranking_estadual
from dashboard.spatial import calcular_indicador_estadual, preparar_recorte_espacial


@pytest.fixture
def fato() -> pd.DataFrame:
    linhas = []
    valores = {
        ("11", 2010): [0, 10, 20, 0],
        ("11", 2022): [0, 20, 60, 10],
        ("12", 2010): [0, 20, 10, 10],
        ("12", 2022): [10, 30, 20, 20],
    }
    for (uf, ano), pops in valores.items():
        i = 0
        for localizacao in (1, 2):
            for domicilio in (1, 2):
                linhas.append({
                    "uf_id": uf,
                    "ano": ano,
                    "localizacao_id": localizacao,
                    "domicilio_id": domicilio,
                    "populacao_indigena": pops[i],
                })
                i += 1
    return pd.DataFrame(linhas)


@pytest.fixture
def geografia() -> pd.DataFrame:
    return pd.DataFrame({
        "uf_id": ["11", "12"],
        "sigla_uf": ["RO", "AC"],
        "uf": ["Rondônia", "Acre"],
        "regiao": ["Norte", "Norte"],
    })


@pytest.fixture
def geojson() -> dict:
    return {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "properties": {"uf_id": "11"}, "geometry": {"type": "Polygon", "coordinates": [[[0,0],[1,0],[1,1],[0,0]]]}},
            {"type": "Feature", "properties": {"uf_id": "12"}, "geometry": {"type": "Polygon", "coordinates": [[[1,0],[2,0],[2,1],[1,0]]]}},
        ],
    }


def test_populacao_estadual_e_ranking(fato, geografia):
    serie = calcular_indicador_estadual(fato, geografia, "População indígena")
    recorte = preparar_recorte_espacial(serie, "2022", "População indígena")
    assert recorte.iloc[0]["uf"] == "Rondônia"
    assert recorte.iloc[0]["valor"] == 90
    assert recorte.iloc[0]["posicao"] == 1


def test_variacao_populacional_eh_absoluta(fato, geografia):
    serie = calcular_indicador_estadual(fato, geografia, "População indígena")
    recorte = preparar_recorte_espacial(serie, "Variação 2010–2022", "População indígena")
    rondonia = recorte.set_index("uf").loc["Rondônia"]
    assert rondonia["valor_2010"] == 30
    assert rondonia["valor_2022"] == 90
    assert rondonia["valor"] == 60


def test_parcela_urbana_preserva_denominador(fato, geografia):
    serie = calcular_indicador_estadual(fato, geografia, "Parcela urbana", domicilio_ids=(1,))
    valor = serie.query("uf == 'Rondônia' and ano == 2022").iloc[0]["valor"]
    assert valor == pytest.approx(60 / 90)


def test_figuras_compartilham_o_mesmo_recorte(fato, geografia, geojson):
    serie = calcular_indicador_estadual(fato, geografia, "População indígena")
    recorte = preparar_recorte_espacial(serie, "2022", "População indígena")
    mapa = criar_mapa_estadual(recorte, geojson, "População indígena", "Mapa")
    ranking = criar_ranking_estadual(recorte, "População indígena", "Ranking")
    assert set(mapa.data[0].locations) == {"11", "12"}
    assert set(ranking.data[0].y) == {"Rondônia (RO)", "Acre (AC)"}
    assert mapa.data[0].featureidkey == "properties.uf_id"


def test_refinamento_visual_do_mapa_e_ranking(fato, geografia, geojson):
    serie = calcular_indicador_estadual(fato, geografia, "População indígena")
    recorte = preparar_recorte_espacial(serie, "2022", "População indígena")
    mapa = criar_mapa_estadual(recorte, geojson, "População indígena", "Mapa")
    ranking = criar_ranking_estadual(recorte, "População indígena", "Ranking")

    assert mapa.layout.height == 700
    assert mapa.data[0].colorbar.x == pytest.approx(0.02)
    assert tuple(mapa.layout.geo.domain.x) == (0.13, 1.0)
    assert ranking.layout.height == 700
    assert ranking.layout.xaxis.tickmode == "array"
    assert all("k" not in str(rotulo) for rotulo in ranking.layout.xaxis.ticktext)
