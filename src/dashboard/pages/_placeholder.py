"""Estrutura provisória para páginas ainda não implementadas."""

from collections.abc import Sequence

import streamlit as st


def renderizar_pagina_planejada(
    titulo: str,
    pergunta: str,
    conteudos: Sequence[str],
) -> None:
    """Expõe o escopo aprovado sem simular uma página concluída."""

    st.title(titulo)
    st.caption(pergunta)
    st.info(
        "A navegação e a infraestrutura desta página estão preparadas. "
        "Sua implementação analítica ocorrerá no próximo incremento."
    )
    st.subheader("Conteúdo aprovado")
    st.markdown("\n".join(f"- {item}" for item in conteudos))
