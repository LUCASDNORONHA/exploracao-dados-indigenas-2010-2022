"""Identidade visual compartilhada pelas figuras interativas."""

from typing import Final

import plotly.graph_objects as go

AZUL_MUITO_CLARO: Final = "#DCEAF2"
AZUL_CLARO: Final = "#8FB7CF"
AZUL_INTERMEDIARIO: Final = "#39708E"
AZUL_ESCURO: Final = "#173F5F"
TEXTO_PRINCIPAL: Final = "#263238"
TEXTO_SECUNDARIO: Final = "#607D8B"
ESTRUTURA: Final = "#D9E1E5"
NEGATIVO: Final = "#B5483A"
FUNDO: Final = "#FFFFFF"

CONFIGURACAO_PLOTLY: Final[dict[str, object]] = {
    "displaylogo": False,
    "responsive": True,
    "modeBarButtonsToRemove": ["select2d", "lasso2d"],
}


def aplicar_layout_padrao(
    figura: go.Figure,
    titulo: str,
    altura: int = 390,
) -> go.Figure:
    """Aplica o padrão visual do projeto a uma figura Plotly."""

    figura.update_layout(
        title={
            "text": titulo,
            "x": 0,
            "xanchor": "left",
            "font": {"size": 19, "color": TEXTO_PRINCIPAL},
        },
        height=altura,
        paper_bgcolor=FUNDO,
        plot_bgcolor=FUNDO,
        font={"family": "Arial, sans-serif", "color": TEXTO_PRINCIPAL},
        margin={"l": 20, "r": 20, "t": 75, "b": 30},
        hoverlabel={
            "bgcolor": FUNDO,
            "bordercolor": ESTRUTURA,
            "font": {"color": TEXTO_PRINCIPAL},
        },
        separators=",.",
    )

    return figura
