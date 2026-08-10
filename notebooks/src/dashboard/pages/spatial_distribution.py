"""Página de distribuição espacial da população indígena."""

from __future__ import annotations

import streamlit as st

from dashboard.charts.spatial import criar_mapa_estadual, criar_ranking_estadual
from dashboard.metrics import DOMICILIOS, LOCALIZACOES
from dashboard.runtime import obter_dados_dashboard
from dashboard.spatial import (
    INDICADORES_ESPACIAIS,
    RECORTES_TEMPORAIS,
    calcular_indicador_estadual,
    preparar_recorte_espacial,
)
from dashboard.theme import CONFIGURACAO_PLOTLY

FILTROS_LOCALIZACAO = {
    "Todas as localizações": LOCALIZACOES,
    "Em Terras Indígenas": (1,),
    "Fora de Terras Indígenas": (2,),
}
FILTROS_DOMICILIO = {
    "Urbana e rural": DOMICILIOS,
    "Urbana": (1,),
    "Rural": (2,),
}


def _selecionar_filtros() -> tuple[str, str, str, str]:
    with st.sidebar:
        st.subheader("Filtros da distribuição espacial")
        indicador = st.selectbox(
            "Indicador",
            options=list(INDICADORES_ESPACIAIS),
            key="indicador_distribuicao_espacial",
        )
        recorte = st.selectbox(
            "Período",
            options=list(RECORTES_TEMPORAIS),
            index=1,
            key="periodo_distribuicao_espacial",
        )
        localizacao = st.selectbox(
            "Localização territorial",
            options=list(FILTROS_LOCALIZACAO),
            key="localizacao_distribuicao_espacial",
        )
        domicilio = st.selectbox(
            "Situação do domicílio",
            options=list(FILTROS_DOMICILIO),
            key="domicilio_distribuicao_espacial",
        )
        st.caption(
            "Mapa e ranking usam exatamente o mesmo recorte. Nos indicadores "
            "de composição, a dimensão analisada preserva seu denominador completo."
        )
    return str(indicador), str(recorte), str(localizacao), str(domicilio)


def _titulo(indicador: str, recorte: str, lider: str) -> str:
    if recorte == "Variação 2010–2022":
        return f"{lider} apresenta a maior {indicador.lower()} na variação intercensitária"
    return f"{lider} lidera as UFs em {indicador.lower()} no Censo de {recorte}"


def render() -> None:
    """Renderiza mapa e ranking estaduais sincronizados."""
    try:
        dados = obter_dados_dashboard()
    except (FileNotFoundError, TypeError, ValueError) as erro:
        st.error("Não foi possível carregar a camada analítica do dashboard.")
        st.code(str(erro), language="text")
        st.stop()

    indicador, recorte, localizacao, domicilio = _selecionar_filtros()
    serie = calcular_indicador_estadual(
        dados.fact_population,
        dados.dim_geography,
        indicador,
        FILTROS_LOCALIZACAO[localizacao],
        FILTROS_DOMICILIO[domicilio],
    )
    espacial = preparar_recorte_espacial(serie, recorte, indicador)
    lider = str(espacial.iloc[0]["uf"])

    st.title(_titulo(indicador, recorte, lider))
    st.caption(
        "A posição no ranking é calculada para as 27 UFs no recorte selecionado. "
        "Passe o cursor sobre o mapa para consultar UF, região, valor e posição."
    )

    coluna_mapa, coluna_ranking = st.columns([1.75, 1.25], gap="large")
    variacao = recorte == "Variação 2010–2022"
    with coluna_mapa:
        st.plotly_chart(
            criar_mapa_estadual(
                espacial,
                dados.states_geojson,
                indicador,
                f"Distribuição estadual — {recorte}",
                variacao=variacao,
            ),
            theme=None,
            config=CONFIGURACAO_PLOTLY,
            key="mapa_distribuicao_espacial",
        )
    with coluna_ranking:
        st.plotly_chart(
            criar_ranking_estadual(
                espacial,
                indicador,
                "Dez maiores valores estaduais",
            ),
            theme=None,
            config=CONFIGURACAO_PLOTLY,
            key="ranking_distribuicao_espacial",
        )

    with st.expander("Consultar ranking completo"):
        tabela = espacial[["posicao", "uf", "sigla_uf", "regiao", "valor"]].copy()
        tabela.columns = ["Posição", "UF", "Sigla", "Região", "Valor"]
        st.dataframe(tabela, hide_index=True, use_container_width=True)
