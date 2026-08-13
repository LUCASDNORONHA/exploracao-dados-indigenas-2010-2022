"""Página de perfil regional."""

from __future__ import annotations

import streamlit as st

from dashboard.charts.regional import (
    criar_comparacao_regional,
    criar_composicao_regional,
    criar_ranking_crescimento,
)
from dashboard.formatting import formatar_percentual
from dashboard.regional import (
    calcular_composicao_regional,
    calcular_crescimento_regional,
    calcular_perfil_regional,
)
from dashboard.runtime import obter_dados_dashboard


def render() -> None:
    """Apresenta a comparação das cinco Grandes Regiões brasileiras."""

    dados = obter_dados_dashboard()
    fato = dados.fact_population
    geografia = dados.dim_geography

    perfil = calcular_perfil_regional(fato, geografia)
    crescimento = calcular_crescimento_regional(perfil)
    urbano_rural = calcular_composicao_regional(fato, geografia, "domicilio", 2022)
    terras_indigenas = calcular_composicao_regional(fato, geografia, "localizacao", 2022)

    lider_2022 = (
        perfil.loc[perfil["ano"] == 2022]
        .sort_values("populacao_indigena", ascending=False)
        .iloc[0]
    )
    maior_crescimento = crescimento.iloc[0]

    st.title(
        f"{lider_2022['regiao']} concentra a maior população indígena entre "
        "as Grandes Regiões em 2022"
    )
    st.caption(
        "A comparação regional reúne participação nacional, crescimento entre os "
        "Censos e diferenças de composição territorial e domiciliar."
    )

    coluna_1, coluna_2 = st.columns(2)
    coluna_1.metric(
        "Maior participação em 2022",
        str(lider_2022["regiao"]),
        formatar_percentual(float(lider_2022["participacao_brasil"])),
    )
    coluna_2.metric(
        "Maior crescimento relativo",
        str(maior_crescimento["regiao"]),
        formatar_percentual(float(maior_crescimento["crescimento_relativo"]), sinal=True),
    )

    st.plotly_chart(
        criar_comparacao_regional(
            perfil,
            "A distribuição regional mudou entre os dois Censos",
        ),
        use_container_width=True,
        config={"displayModeBar": False},
    )

    st.plotly_chart(
        criar_ranking_crescimento(
            crescimento,
            "O crescimento ocorreu em intensidades distintas entre as regiões",
        ),
        use_container_width=True,
        config={"displayModeBar": False},
    )

    coluna_urbano, coluna_ti = st.columns(2, gap="large")
    with coluna_urbano:
        st.plotly_chart(
            criar_composicao_regional(
                urbano_rural,
                "Composição urbano-rural em 2022",
            ),
            use_container_width=True,
            config={"displayModeBar": False},
        )
    with coluna_ti:
        st.plotly_chart(
            criar_composicao_regional(
                terras_indigenas,
                "Presença em Terras Indígenas em 2022",
            ),
            use_container_width=True,
            config={"displayModeBar": False},
        )

    with st.expander("Consultar tabela regional"):
        tabela = crescimento[
            ["regiao", 2010, 2022, "crescimento_absoluto", "crescimento_relativo"]
        ].copy()
        tabela.columns = [
            "Região",
            "População 2010",
            "População 2022",
            "Crescimento absoluto",
            "Crescimento relativo",
        ]
        st.dataframe(
            tabela,
            hide_index=True,
            use_container_width=True,
            column_config={
                "População 2010": st.column_config.NumberColumn(format="%d"),
                "População 2022": st.column_config.NumberColumn(format="%d"),
                "Crescimento absoluto": st.column_config.NumberColumn(format="%d"),
                "Crescimento relativo": st.column_config.NumberColumn(format="%.1f%%"),
            },
        )
