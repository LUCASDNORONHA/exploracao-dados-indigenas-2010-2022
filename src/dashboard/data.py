"""Carregamento e validação da camada compartilhada do dashboard."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar

import pandas as pd

RAIZ_PROJETO = Path(__file__).resolve().parents[2]
DIRETORIO_DASHBOARD_PADRAO = RAIZ_PROJETO / "data" / "processed" / "dashboard"


@dataclass(frozen=True)
class DadosDashboard:
    """Conjunto de dados necessário às páginas da aplicação."""

    fact_population: pd.DataFrame
    dim_geography: pd.DataFrame
    dim_year: pd.DataFrame
    dim_location: pd.DataFrame
    dim_domicile: pd.DataFrame
    states_geojson: dict[str, Any]
    regions_geojson: dict[str, Any]

    ANOS: ClassVar[set[int]] = {2010, 2022}
    CHAVE_FATO: ClassVar[list[str]] = [
        "uf_id",
        "ano",
        "localizacao_id",
        "domicilio_id",
    ]


ARQUIVOS_OBRIGATORIOS = {
    "fact_population": "fact_population.parquet",
    "dim_geography": "dim_geography.parquet",
    "dim_year": "dim_year.csv",
    "dim_location": "dim_location.csv",
    "dim_domicile": "dim_domicile.csv",
    "states_geojson": "states_web.geojson",
    "regions_geojson": "regions_web.geojson",
}


def _validar_arquivos(diretorio: Path) -> dict[str, Path]:
    """Resolve os artefatos e informa conjuntamente eventuais ausências."""

    caminhos = {
        nome: diretorio / arquivo for nome, arquivo in ARQUIVOS_OBRIGATORIOS.items()
    }
    ausentes = [caminho for caminho in caminhos.values() if not caminho.exists()]

    if ausentes:
        lista = "\n".join(f"- {caminho}" for caminho in ausentes)
        raise FileNotFoundError(
            "A camada do dashboard está incompleta. Arquivos ausentes:\n"
            f"{lista}\n"
            "Reconstrua-a com os módulos dashboard_data e "
            "dashboard_geospatial."
        )

    return caminhos


def _ler_geojson(caminho: Path) -> dict[str, Any]:
    """Lê um GeoJSON como estrutura nativa, adequada ao Plotly."""

    return json.loads(caminho.read_text(encoding="utf-8"))


def _validar_tabela_fato(fato: pd.DataFrame) -> None:
    """Verifica as invariantes essenciais da granularidade atômica."""

    colunas = {
        *DadosDashboard.CHAVE_FATO,
        "populacao_indigena",
    }
    ausentes = sorted(colunas - set(fato.columns))

    if ausentes:
        raise ValueError(f"Colunas ausentes em fact_population: {ausentes}")

    problemas = {
        "linhas": len(fato),
        "duplicacoes": int(fato.duplicated(DadosDashboard.CHAVE_FATO).sum()),
        "nulos": int(fato[list(colunas)].isna().sum().sum()),
        "populacoes_negativas": int((fato["populacao_indigena"] < 0).sum()),
        "ufs": int(fato["uf_id"].nunique()),
        "anos": set(fato["ano"].astype(int).unique()),
    }

    valida = (
        problemas["linhas"] == 216
        and problemas["duplicacoes"] == 0
        and problemas["nulos"] == 0
        and problemas["populacoes_negativas"] == 0
        and problemas["ufs"] == 27
        and problemas["anos"] == DadosDashboard.ANOS
    )

    if not valida:
        raise ValueError(f"fact_population viola o contrato: {problemas}")


def _ids_geojson(
    geojson: dict[str, Any],
    propriedade: str,
) -> set[str]:
    """Extrai identificadores de todas as feições de um GeoJSON."""

    feicoes = geojson.get("features")

    if not isinstance(feicoes, list):
        raise TypeError("GeoJSON sem uma coleção válida de feições.")

    ids: set[str] = set()

    for feicao in feicoes:
        propriedades = feicao.get("properties", {})
        valor = propriedades.get(propriedade)

        if valor is None:
            raise ValueError(f"Feição GeoJSON sem a propriedade '{propriedade}'.")

        ids.add(str(valor))

    return ids


def _validar_dimensoes_e_geometrias(dados: DadosDashboard) -> None:
    """Confere cardinalidades e correspondência das chaves geográficas."""

    cardinalidades = {
        "ufs": len(dados.dim_geography),
        "regioes": dados.dim_geography["regiao_id"].nunique(),
        "anos": len(dados.dim_year),
        "localizacoes": len(dados.dim_location),
        "domicilios": len(dados.dim_domicile),
    }
    esperadas = {
        "ufs": 27,
        "regioes": 5,
        "anos": 2,
        "localizacoes": 2,
        "domicilios": 2,
    }

    if cardinalidades != esperadas:
        raise ValueError(
            "As dimensões violam as cardinalidades do contrato: " f"{cardinalidades}"
        )

    ids_ufs_dimensao = set(dados.dim_geography["uf_id"].astype("string").str.zfill(2))
    ids_regioes_dimensao = set(dados.dim_geography["regiao_id"].astype(str))
    ids_ufs_mapa = {
        identificador.zfill(2)
        for identificador in _ids_geojson(dados.states_geojson, "uf_id")
    }
    ids_regioes_mapa = _ids_geojson(dados.regions_geojson, "regiao_id")

    if ids_ufs_mapa != ids_ufs_dimensao:
        raise ValueError("As chaves estaduais do GeoJSON divergem da dimensão.")

    if ids_regioes_mapa != ids_regioes_dimensao:
        raise ValueError("As chaves regionais do GeoJSON divergem da dimensão.")


def carregar_dados_dashboard(
    diretorio: str | Path = DIRETORIO_DASHBOARD_PADRAO,
) -> DadosDashboard:
    """Carrega e valida todos os artefatos consumidos pela aplicação."""

    caminhos = _validar_arquivos(Path(diretorio))

    dados = DadosDashboard(
        fact_population=pd.read_parquet(caminhos["fact_population"]),
        dim_geography=pd.read_parquet(caminhos["dim_geography"]),
        dim_year=pd.read_csv(caminhos["dim_year"]),
        dim_location=pd.read_csv(caminhos["dim_location"]),
        dim_domicile=pd.read_csv(caminhos["dim_domicile"]),
        states_geojson=_ler_geojson(caminhos["states_geojson"]),
        regions_geojson=_ler_geojson(caminhos["regions_geojson"]),
    )

    _validar_tabela_fato(dados.fact_population)
    _validar_dimensoes_e_geometrias(dados)

    return dados
