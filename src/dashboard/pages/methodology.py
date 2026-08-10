"""Página de metodologia e dados."""

from dashboard.pages._placeholder import renderizar_pagina_planejada


def render() -> None:
    """Apresenta o escopo da futura documentação incorporada."""

    renderizar_pagina_planejada(
        titulo="Metodologia e dados",
        pergunta="Como os indicadores foram construídos e validados?",
        conteudos=[
            "fonte e recorte dos dados",
            "definição formal dos indicadores",
            "diferenças metodológicas entre os Censos",
            "limitações de interpretação",
            "arquivos processados disponíveis para download",
        ],
    )
