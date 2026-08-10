"""Visualizações da página de perfil estadual."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from dashboard.formatting import formatar_inteiro
from dashboard.theme import (
    AZUL_CLARO,
    AZUL_ESCURO,
    AZUL_INTERMEDIARIO,
    ESTRUTURA,
    TEXTO_SECUNDARIO,
    aplicar_layout_padrao,
)


def criar_evolucao_uf(dados: pd.DataFrame, titulo: str) -> go.Figure:
    """Compara a população estadual nos Censos de 2010 e 2022."""

    dados = dados.sort_values("ano")
    rotulos = [formatar_inteiro(v) for v in dados["populacao_indigena"]]
    figura = go.Figure(
        go.Bar(
            x=dados["ano"].astype(str),
            y=dados["populacao_indigena"],
            marker_color=[AZUL_CLARO, AZUL_ESCURO],
            text=rotulos,
            textposition="outside",
            cliponaxis=False,
            customdata=[[r] for r in rotulos],
            hovertemplate="<b>Censo %{x}</b><br>%{customdata[0]} indígenas<extra></extra>",
        )
    )
    aplicar_layout_padrao(figura, titulo, altura=390)
    figura.update_layout(showlegend=False, bargap=0.5)
    figura.update_xaxes(title=None, showgrid=False)
    figura.update_yaxes(title=None, gridcolor=ESTRUTURA, zeroline=False)
    return figura


def criar_comparacao_referencias(dados: pd.DataFrame, titulo: str) -> go.Figure:
    """Compara a UF às médias regional e nacional."""

    rotulos = [formatar_inteiro(v) for v in dados["populacao_indigena"]]
    figura = go.Figure(
        go.Bar(
            x=dados["populacao_indigena"],
            y=dados["referencia"],
            orientation="h",
            marker_color=[AZUL_ESCURO, AZUL_INTERMEDIARIO, AZUL_CLARO],
            text=rotulos,
            textposition="outside",
            cliponaxis=False,
            customdata=[[r] for r in rotulos],
            hovertemplate="<b>%{y}</b><br>%{customdata[0]} indígenas<extra></extra>",
        )
    )
    aplicar_layout_padrao(figura, titulo, altura=390)
    figura.update_layout(showlegend=False, margin={"l": 10, "r": 70, "t": 70, "b": 35})
    figura.update_xaxes(title=None, gridcolor=ESTRUTURA, zeroline=False)
    figura.update_yaxes(title=None, automargin=True)
    return figura


def criar_composicao_uf(
    composicao: pd.DataFrame,
    titulo: str,
    cores: dict[str, str] | None = None,
) -> go.Figure:
    """Mostra a mudança da composição estadual entre os dois censos."""

    paleta = cores or {
        "Urbana": AZUL_ESCURO,
        "Rural": AZUL_CLARO,
        "Em TI": AZUL_ESCURO,
        "Fora de TI": AZUL_INTERMEDIARIO,
    }
    figura = go.Figure()

    for categoria in composicao["categoria"].drop_duplicates():
        dados = composicao.loc[composicao["categoria"] == categoria].sort_values("ano")
        valores = dados["proporcao"] * 100
        textos = [f"{v:.1f}%".replace(".", ",") if v >= 7 else "" for v in valores]
        figura.add_trace(
            go.Bar(
                name=str(categoria),
                x=valores,
                y=dados["ano"].astype(str),
                orientation="h",
                marker_color=paleta[str(categoria)],
                text=textos,
                textposition="inside",
                insidetextanchor="middle",
                hovertemplate="<b>%{y} — " + str(categoria) + "</b><br>%{x:.1f}% do total estadual<extra></extra>",
            )
        )

    aplicar_layout_padrao(figura, titulo, altura=350)
    figura.update_layout(
        barmode="stack",
        legend={"orientation": "h", "y": 1.02, "x": 0},
        uniformtext={"minsize": 10, "mode": "hide"},
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
        tickfont={"color": TEXTO_SECUNDARIO},
    )
    return figura
