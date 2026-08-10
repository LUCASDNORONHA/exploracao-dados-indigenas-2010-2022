"""Página de metodologia e dados."""

from __future__ import annotations

from pathlib import Path

import streamlit as st


VERSAO_APLICACAO = "0.1.0"
DATA_ATUALIZACAO = "10 de agosto de 2026"

ARQUIVOS_DOWNLOAD = {
    "Tabela fato — Parquet": "data/processed/dashboard/fact_population.parquet",
    "Tabela fato — CSV": "data/processed/dashboard/fact_population.csv",
    "Dimensão geográfica — Parquet": "data/processed/dashboard/dim_geography.parquet",
    "Dimensão geográfica — CSV": "data/processed/dashboard/dim_geography.csv",
    "Dimensão de anos — CSV": "data/processed/dashboard/dim_year.csv",
    "Dimensão de localização — CSV": "data/processed/dashboard/dim_location.csv",
    "Dimensão de domicílio — CSV": "data/processed/dashboard/dim_domicile.csv",
    "Malha estadual simplificada — GeoJSON": "data/processed/dashboard/states_web.geojson",
    "Malha regional simplificada — GeoJSON": "data/processed/dashboard/regions_web.geojson",
}


def _raiz_projeto() -> Path:
    """Retorna a raiz do repositório a partir deste módulo."""

    return Path(__file__).resolve().parents[3]


def _mime_type(caminho: Path) -> str:
    """Retorna o MIME adequado aos artefatos distribuídos pela aplicação."""

    sufixos = {
        ".csv": "text/csv",
        ".parquet": "application/octet-stream",
        ".geojson": "application/geo+json",
    }
    return sufixos.get(caminho.suffix.lower(), "application/octet-stream")


def _renderizar_downloads() -> None:
    """Exibe somente os artefatos processados existentes no ambiente."""

    raiz = _raiz_projeto()
    disponiveis = 0

    for rotulo, relativo in ARQUIVOS_DOWNLOAD.items():
        caminho = raiz / relativo
        if not caminho.exists():
            continue

        disponiveis += 1
        st.download_button(
            label=f"Baixar {rotulo}",
            data=caminho.read_bytes(),
            file_name=caminho.name,
            mime=_mime_type(caminho),
            use_container_width=True,
        )

    if disponiveis == 0:
        st.info("Os arquivos processados não estão disponíveis neste ambiente.")


def render() -> None:
    """Documenta fontes, definições, limitações e artefatos do dashboard."""

    st.title("Metodologia e dados")
    st.caption(
        "Como os indicadores foram construídos, validados e disponibilizados "
        "para exploração no dashboard."
    )

    st.subheader("Fonte e recorte dos dados")
    st.markdown(
        """
A fonte demográfica é o **Instituto Brasileiro de Geografia e Estatística
(IBGE)**, a partir da tabela *Pessoas indígenas por localização e situação
do domicílio, segundo as Grandes Regiões e Unidades da Federação — Brasil —
2010/2022*.

A unidade analítica do dashboard é a combinação de **UF, ano censitário,
localização territorial e situação do domicílio**. A tabela fato não contém
linhas de total: Brasil, Grandes Regiões e UFs são obtidos por agregação dos
registros atômicos.

A camada geográfica utiliza a malha territorial do IBGE preparada pelo
pipeline do projeto e simplificada para uso interativo na aplicação.
"""
    )

    st.subheader("Definição dos principais indicadores")
    st.markdown(
        """
| Indicador | Definição |
|---|---|
| **População indígena** | Soma de `populacao_indigena` no contexto de filtro atual. |
| **Crescimento absoluto** | População 2022 − População 2010. |
| **Crescimento relativo** | (População 2022 − População 2010) / População 2010. |
| **Proporção urbana** | Urbana / (Urbana + Rural). |
| **Proporção em TI** | Em TI / (Em TI + Fora de TI). |
| **Participação no Brasil** | População da geografia / População do Brasil. |
| **Participação na região** | População da UF / População de sua Grande Região. |

Quando a população de 2010 é igual a zero, o crescimento relativo é tratado
como valor nulo, evitando resultados infinitos.
"""
    )

    st.subheader("Comparabilidade entre os Censos")
    st.warning(
        """
Os resultados de 2010 e 2022 não devem ser interpretados como uma série
temporal perfeitamente homogênea. Mudanças metodológicas, operacionais e de
identificação da população indígena entre os Censos podem afetar a
comparabilidade direta. Por isso, o crescimento observado representa uma
mudança entre dois levantamentos censitários e não deve ser atribuído
automaticamente apenas ao crescimento vegetativo da população.
"""
    )

    st.subheader("Limitações de interpretação")
    st.markdown(
        """
- O dashboard descreve os dados censitários; ele não estabelece relações de causalidade.
- Os dois pontos temporais disponíveis, 2010 e 2022, não permitem inferir a trajetória ocorrida entre os Censos.
- Rankings estaduais devem ser lidos em conjunto com valores absolutos e proporções.
- A simplificação das geometrias é destinada à visualização e não substitui malhas oficiais em análises cartográficas de precisão.
- Totais e proporções apresentados pela aplicação são calculados a partir da camada atômica processada pelo pipeline.
"""
    )

    st.subheader("Arquivos processados")
    st.caption(
        "Os mesmos artefatos tabulares alimentam a aplicação Streamlit e foram "
        "planejados como fonte compartilhada para o relatório Power BI."
    )
    _renderizar_downloads()

    st.divider()
    coluna_versao, coluna_data = st.columns(2)
    coluna_versao.metric("Versão da aplicação", VERSAO_APLICACAO)
    coluna_data.metric("Última atualização", DATA_ATUALIZACAO)

    with st.expander("Estrutura da camada analítica"):
        st.code(
            """fact_population
├── uf_id
├── ano
├── localizacao_id
├── domicilio_id
└── populacao_indigena

dim_geography
├── uf_id
├── sigla_uf
├── uf
├── regiao_id
└── regiao""",
            language="text",
        )
