"""Página de perfil estadual."""

from __future__ import annotations

import streamlit as st

from dashboard.charts.state import (
    criar_comparacao_referencias,
    criar_composicao_uf,
    criar_evolucao_uf,
)
from dashboard.formatting import formatar_inteiro, formatar_percentual
from dashboard.runtime import obter_dados_dashboard
from dashboard.state import (
    calcular_composicao_uf,
    calcular_indicadores_uf,
    calcular_perfil_estadual,
    calcular_referencias_2022,
)


def render() -> None:
    """Apresenta o detalhamento comparativo de uma Unidade da Federação."""

    dados = obter_dados_dashboard()
    fato = dados.fact_population
    geografia = dados.dim_geography
    perfil = calcular_perfil_estadual(fato, geografia)

    opcoes = (
        perfil[["uf_id", "uf", "sigla_uf", "regiao"]]
        .drop_duplicates()
        .sort_values("uf")
        .reset_index(drop=True)
    )
    rotulos = {
        str(linha.uf_id): f"{linha.uf} ({linha.sigla_uf})"
        for linha in opcoes.itertuples()
    }

    st.sidebar.header("Filtros")
    uf_id = st.sidebar.selectbox(
        "Unidade da Federação",
        options=list(rotulos),
        format_func=rotulos.get,
        key="perfil_estadual_uf",
    )

    indicadores = calcular_indicadores_uf(perfil, uf_id)
    composicao_domicilio = calcular_composicao_uf(fato, uf_id, "domicilio")
    composicao_ti = calcular_composicao_uf(fato, uf_id, "localizacao")
    referencias = calcular_referencias_2022(perfil, uf_id)
    serie_uf = perfil.loc[perfil["uf_id"] == uf_id]

    st.title(
        f"{indicadores['uf']} ocupa a {indicadores['ranking_brasil']}ª posição "
        "nacional em população indígena"
    )
    st.caption(
        f"Perfil estadual de {indicadores['uf']} ({indicadores['sigla_uf']}), "
        f"integrante da região {indicadores['regiao']}, com comparação aos Censos "
        "de 2010 e 2022."
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("População em 2022", formatar_inteiro(indicadores["populacao_2022"]))
    c2.metric(
        "Crescimento 2010–2022",
        formatar_percentual(indicadores["crescimento_relativo"], sinal=True),
        formatar_inteiro(indicadores["crescimento_absoluto"], sinal=True),
    )
    c3.metric(
        "Participação no Brasil",
        formatar_percentual(indicadores["participacao_brasil"]),
        f"{indicadores['ranking_brasil']}ª posição",
    )
    c4.metric(
        f"Participação no {indicadores['regiao']}",
        formatar_percentual(indicadores["participacao_regiao"]),
        f"{indicadores['ranking_regiao']}ª posição regional",
    )

    esquerda, direita = st.columns(2, gap="large")
    with esquerda:
        st.plotly_chart(
            criar_evolucao_uf(
                serie_uf,
                f"{indicadores['uf']} entre os dois Censos",
            ),
            use_container_width=True,
            config={"displayModeBar": False},
        )
    with direita:
        st.plotly_chart(
            criar_comparacao_referencias(
                referencias,
                "População estadual frente às médias de referência em 2022",
            ),
            use_container_width=True,
            config={"displayModeBar": False},
        )

    domicilio, ti = st.columns(2, gap="large")
    with domicilio:
        st.plotly_chart(
            criar_composicao_uf(
                composicao_domicilio,
                "Mudança da composição urbano-rural",
            ),
            use_container_width=True,
            config={"displayModeBar": False},
        )
    with ti:
        st.plotly_chart(
            criar_composicao_uf(
                composicao_ti,
                "Mudança da presença em Terras Indígenas",
            ),
            use_container_width=True,
            config={"displayModeBar": False},
        )

    with st.expander("Consultar resumo estadual"):
        st.dataframe(
            serie_uf[["ano", "populacao_indigena"]].rename(
                columns={"ano": "Ano", "populacao_indigena": "População indígena"}
            ),
            hide_index=True,
            use_container_width=True,
        )
