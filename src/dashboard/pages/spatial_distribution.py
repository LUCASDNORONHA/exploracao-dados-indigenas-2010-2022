"""Página de distribuição espacial."""

from dashboard.pages._placeholder import renderizar_pagina_planejada


def render() -> None:
    """Apresenta o escopo da futura exploração espacial."""

    renderizar_pagina_planejada(
        titulo="Distribuição espacial",
        pergunta=(
            "Onde está a população indígena e como sua distribuição " "se alterou?"
        ),
        conteudos=[
            "mapa coroplético estadual com indicador selecionável",
            "comparação entre 2010, 2022 e variação intercensitária",
            "ranking estadual associado ao mapa",
            "tooltips com valor, posição e contexto regional",
        ],
    )
