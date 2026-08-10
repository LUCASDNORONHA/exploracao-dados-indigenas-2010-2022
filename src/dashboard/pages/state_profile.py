"""Página de perfil estadual."""

from dashboard.pages._placeholder import renderizar_pagina_planejada


def render() -> None:
    """Apresenta o escopo do futuro detalhamento por UF."""

    renderizar_pagina_planejada(
        titulo="Perfil estadual",
        pergunta=("Como cada UF se posiciona em relação à sua região e ao Brasil?"),
        conteudos=[
            "seletor de Unidade da Federação",
            "perfil demográfico estadual",
            "posição em rankings selecionados",
            "comparação com a região e o Brasil",
            "presença em TI e mudança da urbanização",
        ],
    )
