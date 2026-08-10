"""Ponto de entrada da aplicação multipágina do Estudo 5."""

import streamlit as st

from dashboard.pages import (
    methodology,
    overview,
    regional_profile,
    spatial_distribution,
    state_profile,
)


def main() -> None:
    """Configura a moldura comum e executa a página selecionada."""

    st.set_page_config(
        page_title="Panorama da População Indígena",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            "About": (
                "Panorama da População Indígena Brasileira — " "Censos 2010 e 2022."
            )
        },
    )

    paginas = {
        "Panorama": [
            st.Page(
                overview.render,
                title="Visão geral",
                url_path="visao-geral",
                default=True,
            ),
            st.Page(
                spatial_distribution.render,
                title="Distribuição espacial",
                url_path="distribuicao-espacial",
            ),
            st.Page(
                regional_profile.render,
                title="Perfil regional",
                url_path="perfil-regional",
            ),
            st.Page(
                state_profile.render,
                title="Perfil estadual",
                url_path="perfil-estadual",
            ),
        ],
        "Projeto": [
            st.Page(
                methodology.render,
                title="Metodologia e dados",
                url_path="metodologia-e-dados",
            )
        ],
    }

    pagina = st.navigation(paginas, position="sidebar", expanded=True)

    with st.sidebar:
        st.divider()
        st.caption(
            "Panorama da População Indígena Brasileira — "
            "Censos Demográficos de 2010 e 2022."
        )

    pagina.run()


if __name__ == "__main__":
    main()
