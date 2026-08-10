"""Testes da página de metodologia e dados."""

from pathlib import Path
import sys
import types

# Stub mínimo: os testes exercitam apenas metadados e funções puras do módulo.
sys.modules.setdefault("streamlit", types.ModuleType("streamlit"))

from dashboard.pages import methodology


def test_catalogo_de_downloads_contem_camadas_compartilhadas():
    caminhos = set(methodology.ARQUIVOS_DOWNLOAD.values())
    assert "data/processed/dashboard/fact_population.parquet" in caminhos
    assert "data/processed/dashboard/fact_population.csv" in caminhos
    assert "data/processed/dashboard/dim_geography.parquet" in caminhos
    assert "data/processed/dashboard/states_web.geojson" in caminhos


def test_mime_type_dos_artefatos():
    assert methodology._mime_type(Path("dados.csv")) == "text/csv"
    assert methodology._mime_type(Path("dados.parquet")) == "application/octet-stream"
    assert methodology._mime_type(Path("estados.geojson")) == "application/geo+json"


def test_versao_e_data_estao_definidas():
    assert methodology.VERSAO_APLICACAO
    assert methodology.DATA_ATUALIZACAO
