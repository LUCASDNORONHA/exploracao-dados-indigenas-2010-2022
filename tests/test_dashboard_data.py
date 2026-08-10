from pathlib import Path

import pandas as pd
import pytest

from preprocessing.dashboard_data import PrepararDadosDashboard

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def preparador() -> PrepararDadosDashboard:
    """Cria a camada em memória uma única vez para os testes contratuais."""

    instancia = PrepararDadosDashboard.criar_com_caminhos_padrao(ROOT)
    instancia.carregar_bases()
    instancia.criar_dimensoes()
    instancia.criar_tabela_fato()

    return instancia


def test_dimensoes_respeitam_cardinalidades(
    preparador: PrepararDadosDashboard,
) -> None:
    resultado = preparador.validar_dimensoes()

    assert resultado["dimensoes_validas"] is True
    assert resultado["ufs"] == 27
    assert resultado["regioes"] == 5
    assert resultado["anos"] == 2
    assert resultado["localizacoes"] == 2
    assert resultado["domicilios"] == 2


def test_tabela_fato_possui_granularidade_atomica(
    preparador: PrepararDadosDashboard,
) -> None:
    resultado = preparador.validar_tabela_fato()

    assert resultado["fato_valida"] is True
    assert resultado["linhas_fato"] == 216
    assert resultado["duplicacoes_chave"] == 0
    assert resultado["ufs_combinacoes_incompletas"] == 0


def test_agregacoes_coincidem_com_referencias_processadas(
    preparador: PrepararDadosDashboard,
) -> None:
    resultado_estadual = preparador.validar_totais_estaduais()
    resultado_agregado = preparador.validar_referencias_agregadas()

    assert resultado_estadual["totais_estaduais_validos"] is True
    assert resultado_estadual["comparacoes_estaduais"] == 270
    assert resultado_agregado["referencias_agregadas_validas"] is True
    assert resultado_agregado["comparacoes_nacionais"] == 8
    assert resultado_agregado["comparacoes_regionais"] == 40


def test_indicadores_nacionais_centrais_permanecem_estaveis(
    preparador: PrepararDadosDashboard,
) -> None:
    fato = preparador.fact_population

    assert fato is not None

    total_2022 = fato.loc[
        fato["ano"] == 2022,
        "populacao_indigena",
    ].sum()
    urbano_2022 = fato.loc[
        (fato["ano"] == 2022) & (fato["domicilio_id"] == 1),
        "populacao_indigena",
    ].sum()
    ti_2022 = fato.loc[
        (fato["ano"] == 2022) & (fato["localizacao_id"] == 1),
        "populacao_indigena",
    ].sum()

    assert int(total_2022) == 1_694_836
    assert int(urbano_2022) == 914_746
    assert int(ti_2022) == 622_844


def test_exportacao_preserva_conteudo(
    tmp_path: Path,
) -> None:
    instancia = PrepararDadosDashboard.criar_com_caminhos_padrao(ROOT)
    instancia.diretorio_saida = tmp_path

    relatorio, caminhos = instancia.executar()

    assert relatorio["fato_valida"] is True
    assert all(caminho.exists() for caminho in caminhos.values())

    fato_csv = pd.read_csv(caminhos["fact_population_csv"])
    fato_parquet = pd.read_parquet(caminhos["fact_population_parquet"])

    colunas_ordenacao = PrepararDadosDashboard.CHAVE_FATO
    fato_csv = fato_csv.sort_values(colunas_ordenacao).reset_index(drop=True)
    fato_parquet = fato_parquet.sort_values(colunas_ordenacao).reset_index(drop=True)

    pd.testing.assert_series_equal(
        fato_csv["populacao_indigena"],
        fato_parquet["populacao_indigena"],
        check_dtype=False,
    )
