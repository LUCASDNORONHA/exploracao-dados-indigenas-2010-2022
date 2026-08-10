"""Recursos de execução específicos do Streamlit."""

import streamlit as st

from dashboard.data import DadosDashboard, carregar_dados_dashboard


@st.cache_data(show_spinner=False)
def obter_dados_dashboard() -> DadosDashboard:
    """Carrega uma cópia cacheada e validada da camada analítica."""

    return carregar_dados_dashboard()
