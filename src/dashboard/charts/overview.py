"""Figuras Plotly da página de visão geral."""

from collections.abc import Mapping

import pandas as pd
import plotly.graph_objects as go

from dashboard.formatting import formatar_inteiro
from dashboard.theme import (
    AZUL_CLARO,
    AZUL_ESCURO,
    AZUL_INTERMEDIARIO,
    AZUL_MUITO_CLARO,
    ESTRUTURA,
    TEXTO_SECUNDARIO,
    aplicar_layout_padrao,
)


def criar_grafico_evolucao(
    serie: pd.DataFrame,
    titulo: str,
) -> go.Figure:
    """Compara os dois pontos censitários sem sugerir série anual."""

    dados = serie.sort_values("ano").copy()
    valores = dados["populacao_indigena"].astype(int)
    rotulos = [formatar_inteiro(valor) for valor in valores]
    figura = go.Figure(
        go.Bar(
            x=dados["ano"].astype(str),
            y=valores,
            marker={
                "color": [AZUL_CLARO, AZUL_ESCURO],
                "line": {"color": AZUL_ESCURO, "width": 0.5},
            },
            text=rotulos,
            textposition="outside",
            cliponaxis=False,
            customdata=[[rotulo] for rotulo in rotulos],
            hovertemplate=(
                "<b>Censo %{x}</b><br>" "%{customdata[0]} indígenas<extra></extra>"
            ),
        )
    )
    aplicar_layout_padrao(figura, titulo, altura=420)
    figura.update_layout(showlegend=False, bargap=0.52)
    figura.update_xaxes(
        title=None,
        showgrid=False,
        tickfont={"size": 13, "color": TEXTO_SECUNDARIO},
    )
    figura.update_yaxes(
        title=None,
        rangemode="tozero",
        range=[0, max(valores.max() * 1.18, 1)],
        gridcolor=ESTRUTURA,
        zeroline=False,
        tickformat=",.0f",
    )

    return figura


def criar_grafico_composicao(
    composicao: pd.DataFrame,
    titulo: str,
    cores: Mapping[str, str] | None = None,
) -> go.Figure:
    """Cria barras horizontais de 100% para uma composição categórica."""

    paleta = dict(
        cores
        or {
            "Urbana": AZUL_ESCURO,
            "Rural": AZUL_CLARO,
            "Em TI": AZUL_ESCURO,
            "Fora de TI": AZUL_INTERMEDIARIO,
        }
    )
    figura = go.Figure()

    for categoria in composicao["categoria"].drop_duplicates():
        dados = composicao.loc[composicao["categoria"] == categoria].sort_values("ano")
        percentuais = dados["proporcao"] * 100
        textos = [
            f"{valor:.1f}%".replace(".", ",") if valor >= 7 else ""
            for valor in percentuais
        ]
        populacoes = [formatar_inteiro(valor) for valor in dados["populacao_indigena"]]

        figura.add_trace(
            go.Bar(
                name=str(categoria),
                x=percentuais,
                y=dados["ano"].astype(str),
                orientation="h",
                marker={
                    "color": paleta.get(str(categoria), AZUL_MUITO_CLARO),
                    "line": {"color": "#FFFFFF", "width": 1},
                },
                text=textos,
                textposition="inside",
                insidetextanchor="middle",
                customdata=list(zip(populacoes, textos, strict=True)),
                hovertemplate=(
                    "<b>%{y} — " + str(categoria) + "</b><br>%{customdata[0]} indígenas"
                    "<br>%{x:.1f}% do total<extra></extra>"
                ),
            )
        )

    aplicar_layout_padrao(figura, titulo, altura=360)
    figura.update_layout(
        barmode="stack",
        bargap=0.38,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "left",
            "x": 0,
            "font": {"color": TEXTO_SECUNDARIO},
        },
        uniformtext={"minsize": 11, "mode": "hide"},
    )
    figura.update_xaxes(
        title=None,
        range=[0, 100],
        tickvals=[0, 25, 50, 75, 100],
        ticktext=["0%", "25%", "50%", "75%", "100%"],
        gridcolor=ESTRUTURA,
        zeroline=False,
    )
    figura.update_yaxes(
        title=None,
        categoryorder="array",
        categoryarray=["2010", "2022"],
        tickfont={"size": 13, "color": TEXTO_SECUNDARIO},
    )

    return figura
