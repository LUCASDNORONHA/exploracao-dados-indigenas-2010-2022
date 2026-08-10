"""Visualizações da página de distribuição espacial."""

from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.graph_objects as go

from dashboard.theme import (
    AZUL_CLARO,
    AZUL_ESCURO,
    AZUL_MUITO_CLARO,
    ESTRUTURA,
    NEGATIVO,
    TEXTO_SECUNDARIO,
    aplicar_layout_padrao,
)


def _escala(indicador: str, variacao: bool) -> list[list[object]]:
    """Retorna a escala cromática adequada ao tipo de leitura."""
    if variacao:
        return [[0.0, NEGATIVO], [0.5, "#F7F7F7"], [1.0, AZUL_ESCURO]]
    return [[0.0, AZUL_MUITO_CLARO], [0.55, AZUL_CLARO], [1.0, AZUL_ESCURO]]


def _formato_valor(indicador: str) -> str:
    return ".1%" if indicador != "População indígena" else ",.0f"


def _formatar_populacao(valor: float) -> str:
    """Produz rótulo compacto em português para valores populacionais."""
    absoluto = abs(valor)
    if absoluto >= 1_000_000:
        texto = f"{valor / 1_000_000:.1f} mi"
    elif absoluto >= 1_000:
        texto = f"{valor / 1_000:.0f} mil"
    else:
        texto = f"{valor:.0f}"
    return texto.replace(".", ",")


def _formatar_valor(valor: float, indicador: str) -> str:
    if indicador == "População indígena":
        return _formatar_populacao(valor)
    return f"{valor * 100:.1f}%".replace(".", ",")


def _configurar_eixo_valores(
    figura: go.Figure,
    dados: pd.Series,
    indicador: str,
) -> None:
    """Padroniza o eixo numérico sem abreviações anglófonas como k e M."""
    if indicador != "População indígena":
        figura.update_xaxes(tickformat=".0%")
        return

    maximo = float(dados.max()) if len(dados) else 0.0
    if maximo <= 0:
        return

    passos = 4
    intervalo = maximo / passos
    valores = [intervalo * indice for indice in range(passos + 1)]
    figura.update_xaxes(
        tickmode="array",
        tickvals=valores,
        ticktext=[_formatar_populacao(valor) for valor in valores],
    )


def criar_mapa_estadual(
    dados: pd.DataFrame,
    geojson: dict[str, Any],
    indicador: str,
    titulo: str,
    variacao: bool = False,
) -> go.Figure:
    """Cria mapa coroplético estadual associado às chaves IBGE das UFs."""
    formato = _formato_valor(indicador)
    customdata = dados[["uf", "sigla_uf", "regiao", "posicao"]].to_numpy()
    zmax = float(dados["valor"].abs().max()) if variacao and len(dados) else None

    figura = go.Figure(
        go.Choropleth(
            geojson=geojson,
            locations=dados["uf_id"],
            z=dados["valor"],
            featureidkey="properties.uf_id",
            colorscale=_escala(indicador, variacao),
            zmin=-zmax if variacao and zmax is not None else None,
            zmax=zmax if variacao else None,
            zmid=0 if variacao else None,
            customdata=customdata,
            marker_line_color="#FFFFFF",
            marker_line_width=0.9,
            colorbar={
                "title": {"text": "Variação" if variacao else indicador, "side": "top"},
                "x": 0.02,
                "xanchor": "left",
                "y": 0.50,
                "len": 0.66,
                "thickness": 14,
                "outlinewidth": 0,
                "tickfont": {"color": TEXTO_SECUNDARIO},
                "tickformat": ".0%" if indicador != "População indígena" else None,
            },
            hovertemplate=(
                "<b>%{customdata[0]} (%{customdata[1]})</b><br>"
                "Região: %{customdata[2]}<br>"
                f"Valor: %{{z:{formato}}}<br>"
                "Posição nacional: %{customdata[3]}ª<extra></extra>"
            ),
        )
    )
    figura.update_geos(
        fitbounds="locations",
        visible=False,
        projection_type="mercator",
        domain={"x": [0.13, 1.0], "y": [0.0, 1.0]},
    )
    aplicar_layout_padrao(figura, titulo, altura=700)
    figura.update_layout(margin={"l": 0, "r": 0, "t": 65, "b": 0})
    return figura


def criar_ranking_estadual(
    dados: pd.DataFrame,
    indicador: str,
    titulo: str,
    quantidade: int = 10,
) -> go.Figure:
    """Cria ranking horizontal com as UFs de maior valor no recorte."""
    ranking = dados.nlargest(quantidade, "valor").sort_values("valor").copy()
    formato = _formato_valor(indicador)
    ranking["rotulo_uf"] = ranking["uf"] + " (" + ranking["sigla_uf"] + ")"

    figura = go.Figure(
        go.Bar(
            x=ranking["valor"],
            y=ranking["rotulo_uf"],
            orientation="h",
            marker_color=AZUL_ESCURO,
            customdata=ranking[["uf", "sigla_uf", "regiao", "posicao"]].to_numpy(),
            hovertemplate=(
                "<b>%{customdata[0]} (%{customdata[1]})</b><br>"
                "Região: %{customdata[2]}<br>"
                f"Valor: %{{x:{formato}}}<br>"
                "Posição nacional: %{customdata[3]}ª<extra></extra>"
            ),
        )
    )
    aplicar_layout_padrao(figura, titulo, altura=700)
    _configurar_eixo_valores(figura, ranking["valor"], indicador)
    figura.update_layout(
        showlegend=False,
        xaxis_title=None,
        yaxis_title=None,
        margin={"l": 8, "r": 8, "t": 75, "b": 35},
    )
    figura.update_xaxes(
        showgrid=True,
        gridcolor=ESTRUTURA,
        zeroline=False,
        tickfont={"color": TEXTO_SECUNDARIO},
    )
    figura.update_yaxes(showgrid=False, tickfont={"size": 11}, automargin=True)
    return figura
