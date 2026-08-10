from pathlib import Path

import geopandas as gpd
import pandas as pd
import pytest

from preprocessing.dashboard_geospatial import PrepararGeometriasDashboard

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def camada_geoespacial(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[
    PrepararGeometriasDashboard,
    dict[str, int | float | bool],
    dict[str, Path],
]:
    """Gera uma única camada temporária para os testes contratuais."""

    preparador = PrepararGeometriasDashboard.criar_com_caminhos_padrao(ROOT)
    preparador.diretorio_saida = tmp_path_factory.mktemp("dashboard_geo")
    relatorio, caminhos = preparador.executar()

    return preparador, relatorio, caminhos


def test_entrada_e_cardinalidades_territoriais_sao_validas(
    camada_geoespacial: tuple[
        PrepararGeometriasDashboard,
        dict[str, int | float | bool],
        dict[str, Path],
    ],
) -> None:
    _, relatorio, _ = camada_geoespacial

    assert relatorio["entrada_valida"] is True
    assert relatorio["ufs_entrada"] == 27
    assert relatorio["ufs_saida"] == 27
    assert relatorio["regioes_entrada"] == 5
    assert relatorio["regioes_saida"] == 5


def test_simplificacao_atende_limites_de_reducao_e_area(
    camada_geoespacial: tuple[
        PrepararGeometriasDashboard,
        dict[str, int | float | bool],
        dict[str, Path],
    ],
) -> None:
    preparador, relatorio, _ = camada_geoespacial

    assert relatorio["resultados_validos"] is True
    assert (
        relatorio["reducao_coordenadas_pct"]
        >= preparador.REDUCAO_MINIMA_COORDENADAS_PCT
    )
    assert (
        relatorio["erro_maximo_area_estadual_pct"]
        <= preparador.ERRO_MAXIMO_AREA_ESTADUAL_PCT
    )
    assert (
        relatorio["erro_maximo_area_regional_pct"]
        <= preparador.ERRO_MAXIMO_AREA_REGIONAL_PCT
    )


def test_coberturas_e_crs_web_permanecem_validos(
    camada_geoespacial: tuple[
        PrepararGeometriasDashboard,
        dict[str, int | float | bool],
        dict[str, Path],
    ],
) -> None:
    _, relatorio, _ = camada_geoespacial

    assert relatorio["cobertura_estadual_valida"] is True
    assert relatorio["cobertura_regional_valida"] is True
    assert relatorio["crs_web_valido"] is True


def test_geojson_persistidos_sao_leves_e_integros(
    camada_geoespacial: tuple[
        PrepararGeometriasDashboard,
        dict[str, int | float | bool],
        dict[str, Path],
    ],
) -> None:
    preparador, relatorio, caminhos = camada_geoespacial

    assert relatorio["arquivos_geojson_validos"] is True
    assert all(caminho.exists() for caminho in caminhos.values())
    assert relatorio["tamanho_states_web_mb"] <= preparador.TAMANHO_MAXIMO_ARQUIVO_MB
    assert relatorio["tamanho_regions_web_mb"] <= preparador.TAMANHO_MAXIMO_ARQUIVO_MB

    estados = gpd.read_file(caminhos["states_web"])
    regioes = gpd.read_file(caminhos["regions_web"])

    assert estados.crs is not None
    assert regioes.crs is not None
    assert estados.crs.to_epsg() == preparador.CRS_WEB
    assert regioes.crs.to_epsg() == preparador.CRS_WEB
    assert set(estados.geometry.geom_type).issubset(
        preparador.TIPOS_GEOMETRIA_PERMITIDOS
    )
    assert set(regioes.geometry.geom_type).issubset(
        preparador.TIPOS_GEOMETRIA_PERMITIDOS
    )


def test_chaves_geograficas_coincidem_com_dimensao_canonica(
    camada_geoespacial: tuple[
        PrepararGeometriasDashboard,
        dict[str, int | float | bool],
        dict[str, Path],
    ],
) -> None:
    preparador, _, caminhos = camada_geoespacial
    dimensao = pd.read_parquet(preparador.caminho_dim_geography)
    estados = gpd.read_file(caminhos["states_web"])
    regioes = gpd.read_file(caminhos["regions_web"])

    ids_ufs_esperados = set(dimensao["uf_id"].astype("string").str.zfill(2))
    ids_regioes_esperados = set(dimensao["regiao_id"].astype(int))

    assert set(estados["uf_id"].astype("string").str.zfill(2)) == (ids_ufs_esperados)
    assert set(regioes["regiao_id"].astype(int)) == ids_regioes_esperados
