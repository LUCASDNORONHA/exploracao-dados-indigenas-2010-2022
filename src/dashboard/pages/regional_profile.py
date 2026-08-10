"""Página de perfil regional."""

from dashboard.pages._placeholder import renderizar_pagina_planejada


def render() -> None:
    """Apresenta o escopo da futura comparação regional."""

    renderizar_pagina_planejada(
        titulo="Perfil regional",
        pergunta="Como as cinco Grandes Regiões diferem entre si?",
        conteudos=[
            "participação no total nacional",
            "crescimento absoluto e relativo",
            "composição urbano-rural",
            "presença em Terras Indígenas",
            "comparação direta entre as cinco regiões",
        ],
    )
