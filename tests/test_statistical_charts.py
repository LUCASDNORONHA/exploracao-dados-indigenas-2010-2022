from importlib import import_module
from pathlib import Path

import matplotlib
import pandas as pd
import pytest

matplotlib.use("Agg")

PlotAnaliseEstatistica = import_module(
    "charts.statistical_analysis"
).PlotAnaliseEstatistica

ROOT = Path(__file__).resolve().parents[1]
CAMINHO_BASE = ROOT / "data" / "processed" / "table" / "df_statistical_analysis.csv"


@pytest.fixture(scope="module")
def base() -> pd.DataFrame:
    return pd.read_csv(CAMINHO_BASE)


def test_grafico_distribuicoes_e_criado(
    base: pd.DataFrame,
    tmp_path: Path,
) -> None:
    caminho = PlotAnaliseEstatistica(
        base,
        tmp_path,
    ).plot_distribuicoes_estaduais(exibir=False)

    assert caminho.exists()
    assert caminho.name == "grafico_distribuicoes_estatisticas_estaduais.png"
    assert caminho.stat().st_size > 100_000


def test_grafico_concentracao_e_criado(
    base: pd.DataFrame,
    tmp_path: Path,
) -> None:
    caminho = PlotAnaliseEstatistica(
        base,
        tmp_path,
    ).plot_concentracao_estadual(exibir=False)

    assert caminho.exists()
    assert caminho.name == "grafico_concentracao_estadual_2022.png"
    assert caminho.stat().st_size > 100_000


def test_grafico_valores_atipicos_e_criado(
    base: pd.DataFrame,
    tmp_path: Path,
) -> None:
    caminho = PlotAnaliseEstatistica(
        base,
        tmp_path,
    ).plot_valores_atipicos_estaduais(exibir=False)

    assert caminho.exists()
    assert caminho.name == "grafico_valores_atipicos_estaduais.png"
    assert caminho.stat().st_size > 100_000


def test_grafico_influencia_e_criado(
    base: pd.DataFrame,
    tmp_path: Path,
) -> None:
    caminho = PlotAnaliseEstatistica(
        base,
        tmp_path,
    ).plot_influencia_estadual(exibir=False)

    assert caminho.exists()
    assert caminho.name == "grafico_influencia_estadual_2022.png"
    assert caminho.stat().st_size > 100_000


def test_grafico_relacoes_estaduais_e_criado(
    base: pd.DataFrame,
    tmp_path: Path,
) -> None:
    caminho = PlotAnaliseEstatistica(
        base,
        tmp_path,
    ).plot_relacoes_estaduais_spearman(exibir=False)

    assert caminho.exists()
    assert caminho.name == "grafico_relacoes_estaduais_spearman.png"
    assert caminho.stat().st_size > 100_000


def test_grafico_estabilidade_do_ranking_e_criado(
    base: pd.DataFrame,
    tmp_path: Path,
) -> None:
    caminho = PlotAnaliseEstatistica(
        base,
        tmp_path,
    ).plot_estabilidade_ranking_populacional(exibir=False)

    assert caminho.exists()
    assert caminho.name == ("grafico_estabilidade_ranking_populacional_2010_2022.png")
    assert caminho.stat().st_size > 100_000


def test_grafico_pca_e_criado(
    base: pd.DataFrame,
    tmp_path: Path,
) -> None:
    caminho = PlotAnaliseEstatistica(
        base,
        tmp_path,
    ).plot_pca_perfis_estaduais(exibir=False)

    assert caminho.exists()
    assert caminho.name == "grafico_pca_perfis_estaduais.png"
    assert caminho.stat().st_size > 100_000


def test_grafico_validacao_dos_agrupamentos_e_criado(
    base: pd.DataFrame,
    tmp_path: Path,
) -> None:
    caminho = PlotAnaliseEstatistica(
        base,
        tmp_path,
    ).plot_validacao_agrupamentos_estaduais(exibir=False)

    assert caminho.exists()
    assert caminho.name == "grafico_validacao_agrupamentos_estaduais.png"
    assert caminho.stat().st_size > 100_000
