"""Visualizações da página de perfil regional."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from dashboard.formatting import formatar_inteiro, formatar_percentual
from dashboard.theme import (
    AZUL_CLARO,
    AZUL_ESCURO,
    AZUL_INTERMEDIARIO,
    ESTRUTURA,
    TEXTO_SECUNDARIO,
    aplicar_layout_padrao,
)


def criar_comparacao_regional(perfil: pd.DataFrame, titulo: str) -> go.Figure:
    """Compara a população das cinco regiões nos dois censos."""

    figura = go.Figure()
    cores = {2010: AZUL_CLARO, 2022: AZUL_ESCURO}

    for ano in (2010, 2022):
        dados = perfil.loc[perfil["ano"] == ano].sort_values("ordem_regiao")
        rotulos = [formatar_inteiro(v) for v in dados["populacao_indigena"]]
        figura.add_trace(
            go.Bar(
                name=str(ano),
                x=dados["regiao"],
                y=dados["populacao_indigena"],
                marker_color=cores[ano],
                customdata=[[r] for r in rotulos],
                hovertemplate="<b>%{x} — " + str(ano) + "</b><br>%{customdata[0]} indígenas<extra></extra>",
            )
        )

    aplicar_layout_padrao(figura, titulo, altura=430)
    figura.update_layout(barmode="group", bargap=0.25, bargroupgap=0.08)
    figura.update_xaxes(title=None, showgrid=False)
    figura.update_yaxes(title=None, gridcolor=ESTRUTURA, zeroline=False)
    return figura


def criar_ranking_crescimento(crescimento: pd.DataFrame, titulo: str) -> go.Figure:
    """Ordena as regiões pelo crescimento relativo entre os censos."""

    dados = crescimento.sort_values("crescimento_relativo")
    textos = [formatar_percentual(v, sinal=True) for v in dados["crescimento_relativo"]]

    figura = go.Figure(
        go.Bar(
            x=dados["crescimento_relativo"],
            y=dados["regiao"],
            orientation="h",
            marker_color=AZUL_ESCURO,
            text=textos,
            textposition="outside",
            cliponaxis=False,
            customdata=dados[["crescimento_absoluto"]].to_numpy(),
            hovertemplate="<b>%{y}</b><br>Crescimento: %{x:.1%}<br>Acréscimo absoluto: %{customdata[0]:,.0f}<extra></extra>",
        )
    )
    aplicar_layout_padrao(figura, titulo, altura=430)
    figura.update_layout(showlegend=False, margin={"l": 10, "r": 65, "t": 70, "b": 35})
    figura.update_xaxes(title=None, tickformat=".0%", gridcolor=ESTRUTURA, zeroline=False)
    figura.update_yaxes(title=None)
    return figura


def criar_composicao_regional(
    composicao: pd.DataFrame,
    titulo: str,
    cores: dict[str, str] | None = None,
) -> go.Figure:
    """Cria barras de 100% para comparar a composição das cinco regiões."""

    paleta = cores or {
        "Urbana": AZUL_ESCURO,
        "Rural": AZUL_CLARO,
        "Em TI": AZUL_ESCURO,
        "Fora de TI": AZUL_INTERMEDIARIO,
    }
    figura = go.Figure()

    for categoria in composicao["categoria"].drop_duplicates():
        dados = composicao.loc[composicao["categoria"] == categoria].sort_values("ordem_regiao")
        valores = dados["proporcao"] * 100
        textos = [f"{v:.1f}%".replace(".", ",") if v >= 7 else "" for v in valores]
        figura.add_trace(
            go.Bar(
                name=str(categoria),
                x=valores,
                y=dados["regiao"],
                orientation="h",
                marker_color=paleta[str(categoria)],
                text=textos,
                textposition="inside",
                insidetextanchor="middle",
                hovertemplate="<b>%{y} — " + str(categoria) + "</b><br>%{x:.1f}% do total regional<extra></extra>",
            )
        )

    aplicar_layout_padrao(figura, titulo, altura=410)
    figura.update_layout(
        barmode="stack",
        legend={"orientation": "h", "y": 1.10, "x": 0},
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
        categoryarray=list(reversed(
            composicao.sort_values("ordem_regiao")["regiao"].drop_duplicates().tolist()
        )),
        tickfont={"color": TEXTO_SECUNDARIO},
    )
    return figura
