"""Página inicial de visão geral do panorama nacional."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd
import streamlit as st

from dashboard.charts.overview import (
    criar_grafico_composicao,
    criar_grafico_evolucao,
)
from dashboard.formatting import (
    formatar_inteiro,
    formatar_percentual,
    formatar_pontos_percentuais,
)
from dashboard.metrics import (
    DOMICILIOS,
    LOCALIZACOES,
    IndicadoresVisaoGeral,
    calcular_indicadores_visao_geral,
    composicao_domiciliar_por_ano,
    composicao_territorial_por_ano,
    filtrar_fato,
    serie_populacao_por_ano,
)
from dashboard.runtime import obter_dados_dashboard
from dashboard.theme import (
    AZUL_CLARO,
    AZUL_ESCURO,
    AZUL_INTERMEDIARIO,
    CONFIGURACAO_PLOTLY,
)

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


def _contexto_filtros(
    rotulo_localizacao: str,
    rotulo_domicilio: str,
) -> str:
    """Constrói uma descrição legível do recorte selecionado."""

    localizacao = {
        "Todas as localizações": "",
        "Em Terras Indígenas": "em Terras Indígenas",
        "Fora de Terras Indígenas": "fora de Terras Indígenas",
    }[rotulo_localizacao]
    domicilio = {
        "Urbana e rural": "",
        "Urbana": "em domicílios urbanos",
        "Rural": "em domicílios rurais",
    }[rotulo_domicilio]
    complementos = " e ".join(trecho for trecho in [localizacao, domicilio] if trecho)

    return complementos or "no Brasil"


def _titulo_principal(
    indicadores: IndicadoresVisaoGeral,
    contexto: str,
) -> str:
    """Produz um título factual que acompanha a seleção atual."""

    variacao = indicadores.crescimento_relativo

    if variacao is None:
        return f"A população indígena {contexto} não possui base comparável"

    verbo = "cresceu" if variacao >= 0 else "diminuiu"

    return (
        f"A população indígena {contexto} {verbo} "
        f"{formatar_percentual(abs(variacao))} entre os Censos"
    )


def _titulo_variacao(
    variacao: float,
    indicador: str,
) -> str:
    """Transforma uma diferença proporcional em título analítico."""

    if variacao > 0:
        movimento = "aumentou"
    elif variacao < 0:
        movimento = "diminuiu"
    else:
        return f"{indicador} permaneceu estável"

    return f"{indicador} {movimento} " f"{formatar_pontos_percentuais(variacao)}"


def _variacao_categoria(
    composicao: pd.DataFrame,
    categoria: str,
) -> float:
    """Obtém a mudança 2010–2022 de uma categoria da composição."""

    valores = (
        composicao.loc[composicao["categoria"] == categoria]
        .set_index("ano")["proporcao"]
        .reindex([2010, 2022], fill_value=0)
    )

    return float(valores.loc[2022] - valores.loc[2010])


def _renderizar_kpis(indicadores: IndicadoresVisaoGeral) -> None:
    """Apresenta os quatro indicadores centrais em cartões."""

    colunas = st.columns(4)

    colunas[0].metric(
        "População indígena em 2022",
        formatar_inteiro(indicadores.populacao_2022),
        delta=formatar_percentual(
            indicadores.crescimento_relativo,
            sinal=True,
        ),
        delta_description="Variação relativa em comparação com 2010.",
        help="O total respeita os dois filtros selecionados.",
        border=True,
    )
    colunas[1].metric(
        "Crescimento absoluto",
        formatar_inteiro(indicadores.crescimento_absoluto, sinal=True),
        help="Diferença entre as populações observadas em 2022 e 2010.",
        border=True,
    )
    colunas[2].metric(
        "Parcela urbana em 2022",
        formatar_percentual(indicadores.proporcao_urbana_2022),
        help=(
            "Mantém Urbana e Rural no denominador e respeita o filtro "
            "de localização territorial."
        ),
        border=True,
    )
    colunas[3].metric(
        "Parcela em TI em 2022",
        formatar_percentual(indicadores.proporcao_ti_2022),
        help=(
            "Mantém TI e Fora de TI no denominador e respeita o filtro "
            "de situação do domicílio."
        ),
        border=True,
    )


def _selecionar_filtros() -> tuple[str, str]:
    """Renderiza e devolve os filtros da página."""

    with st.sidebar:
        st.subheader("Filtros da visão geral")
        localizacao = st.selectbox(
            "Localização territorial",
            options=list(FILTROS_LOCALIZACAO),
            key="filtro_localizacao_visao_geral",
            help="Seleciona a população em TI, fora de TI ou ambas.",
        )
        domicilio = st.selectbox(
            "Situação do domicílio",
            options=list(FILTROS_DOMICILIO),
            key="filtro_domicilio_visao_geral",
            help="Seleciona domicílios urbanos, rurais ou ambos.",
        )
        st.caption(
            "Os totais cruzam ambos os filtros. Cada composição preserva "
            "as duas categorias da dimensão que está sendo comparada."
        )

    return str(localizacao), str(domicilio)


def _ids_filtro(
    rotulo: str,
    opcoes: dict[str, tuple[int, ...]],
) -> Iterable[int]:
    """Resolve um rótulo de interface para as chaves da dimensão."""

    return opcoes[rotulo]


def render() -> None:
    """Renderiza a síntese nacional e suas interações."""

    try:
        dados = obter_dados_dashboard()
    except (FileNotFoundError, TypeError, ValueError) as erro:
        st.error("Não foi possível carregar a camada analítica do dashboard.")
        st.code(str(erro), language="text")
        st.code(
            "uv run python -m preprocessing.dashboard_data\n"
            "uv run python -m preprocessing.dashboard_geospatial",
            language="bash",
        )
        st.stop()

    rotulo_localizacao, rotulo_domicilio = _selecionar_filtros()
    localizacao_ids = _ids_filtro(
        rotulo_localizacao,
        FILTROS_LOCALIZACAO,
    )
    domicilio_ids = _ids_filtro(
        rotulo_domicilio,
        FILTROS_DOMICILIO,
    )

    fato = dados.fact_population
    indicadores = calcular_indicadores_visao_geral(
        fato,
        localizacao_ids,
        domicilio_ids,
    )
    contexto = _contexto_filtros(rotulo_localizacao, rotulo_domicilio)

    st.title(_titulo_principal(indicadores, contexto))
    st.caption(
        "Comparação de dois pontos censitários. Os valores intermediários "
        "não constituem uma série anual observada."
    )
    _renderizar_kpis(indicadores)

    fato_filtrado = filtrar_fato(fato, localizacao_ids, domicilio_ids)
    serie = serie_populacao_por_ano(fato_filtrado)
    figura_evolucao = criar_grafico_evolucao(
        serie,
        "Dois retratos censitários mostram a dimensão da mudança",
    )
    st.plotly_chart(
        figura_evolucao,
        theme=None,
        config=CONFIGURACAO_PLOTLY,
        key="evolucao_visao_geral",
    )

    composicao_domiciliar = composicao_domiciliar_por_ano(
        fato,
        localizacao_ids,
    )
    composicao_territorial = composicao_territorial_por_ano(
        fato,
        domicilio_ids,
    )
    variacao_urbana = _variacao_categoria(composicao_domiciliar, "Urbana")
    variacao_ti = _variacao_categoria(composicao_territorial, "Em TI")

    coluna_domicilio, coluna_territorio = st.columns(2)

    with coluna_domicilio:
        figura_domicilio = criar_grafico_composicao(
            composicao_domiciliar,
            _titulo_variacao(variacao_urbana, "A parcela urbana"),
            cores={"Urbana": AZUL_ESCURO, "Rural": AZUL_CLARO},
        )
        st.plotly_chart(
            figura_domicilio,
            theme=None,
            config=CONFIGURACAO_PLOTLY,
            key="composicao_domiciliar_visao_geral",
        )
        st.caption(
            "Composição urbana-rural dentro da localização territorial " "selecionada."
        )

    with coluna_territorio:
        figura_territorio = criar_grafico_composicao(
            composicao_territorial,
            _titulo_variacao(variacao_ti, "A parcela em TI"),
            cores={
                "Em TI": AZUL_ESCURO,
                "Fora de TI": AZUL_INTERMEDIARIO,
            },
        )
        st.plotly_chart(
            figura_territorio,
            theme=None,
            config=CONFIGURACAO_PLOTLY,
            key="composicao_territorial_visao_geral",
        )
        st.caption(
            "Composição TI–fora de TI dentro da situação do domicílio " "selecionada."
        )
