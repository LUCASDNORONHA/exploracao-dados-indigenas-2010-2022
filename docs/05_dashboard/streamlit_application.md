# Aplicação Streamlit — Estudo 5

**Versão:** 1.0  
**Data:** 9 de agosto de 2026  
**Estado:** infraestrutura multipágina e página de visão geral implementadas

## 1. Finalidade

Este documento descreve a arquitetura, a execução e as regras de interação
da aplicação exploratória do Estudo 5. A aplicação consome exclusivamente a
camada processada em `data/processed/dashboard/`; nenhum notebook participa de
sua execução.

## 2. Arquitetura

```text
.
├── .streamlit/
│   └── config.toml
├── streamlit_app.py
├── src/dashboard/
│   ├── data.py
│   ├── formatting.py
│   ├── metrics.py
│   ├── runtime.py
│   ├── theme.py
│   ├── charts/
│   │   └── overview.py
│   └── pages/
│       ├── overview.py
│       ├── spatial_distribution.py
│       ├── regional_profile.py
│       ├── state_profile.py
│       └── methodology.py
└── tests/
    └── test_dashboard_app.py
```

### 2.1 Responsabilidades

| Componente | Responsabilidade |
|---|---|
| `streamlit_app.py` | configuração global e navegação multipágina |
| `data.py` | leitura e validação dos artefatos compartilhados |
| `runtime.py` | cache de dados específico do Streamlit |
| `metrics.py` | filtros, agregações, proporções e indicadores testáveis |
| `formatting.py` | formatação numérica em português do Brasil |
| `theme.py` | paleta e configuração visual do Plotly |
| `charts/` | construção das figuras interativas |
| `pages/` | composição dos elementos de cada página |

A navegação utiliza `st.Page` e `st.navigation`, mecanismo recomendado pelo
Streamlit para aplicações multipágina que exigem maior controle de estrutura.
O carregamento é armazenado com `st.cache_data`, enquanto métricas e gráficos
permanecem em funções independentes da sessão da interface.

## 3. Estado das páginas

| Página | Estado |
|---|---|
| Visão geral | implementada e testada |
| Distribuição espacial | estrutura preparada |
| Perfil regional | estrutura preparada |
| Perfil estadual | estrutura preparada |
| Metodologia e dados | estrutura preparada |

As páginas ainda não implementadas mostram explicitamente o conteúdo
aprovado. Elas não apresentam valores provisórios nem simulam conclusão.

## 4. Página de visão geral

A página responde à pergunta:

> O que mudou na população indígena brasileira entre os Censos de 2010 e
> 2022?

### 4.1 Indicadores

- população indígena em 2022;
- crescimento absoluto;
- crescimento relativo;
- parcela urbana em 2022;
- parcela em Terras Indígenas em 2022.

### 4.2 Visualizações

1. barras para comparar os dois pontos censitários, evitando sugerir uma série
   anual inexistente;
2. barras horizontais de 100% para a composição urbana-rural;
3. barras horizontais de 100% para a composição TI–fora de TI.

### 4.3 Semântica dos filtros

Os filtros disponíveis são:

- localização territorial: todas, em TI ou fora de TI;
- situação do domicílio: urbana e rural, somente urbana ou somente rural.

Os totais, a evolução e o crescimento cruzam ambos os filtros. Os indicadores
de composição preservam as duas categorias da dimensão que medem:

- a parcela urbana e a composição urbana-rural respeitam a localização
  territorial selecionada, mas preservam Urbana e Rural no denominador;
- a parcela em TI e a composição TI–fora de TI respeitam a situação do
  domicílio selecionada, mas preservam TI e Fora de TI no denominador.

Essa regra impede que a escolha de uma única categoria transforme um indicador
de composição em um resultado tautológico de 0% ou 100%.

## 5. Execução

Em um ambiente já sincronizado:

```bash
uv run streamlit run streamlit_app.py
```

Em uma reconstrução integral, execute antes:

```bash
uv sync --all-groups
uv run python -m preprocessing.dashboard_data
uv run python -m preprocessing.dashboard_geospatial
uv run streamlit run streamlit_app.py
```

## 6. Validação

```bash
uv run pytest tests/test_dashboard_app.py -q
uv run pytest -q
```

Os cinco testes específicos da aplicação verificam:

- carregamento de 216 registros, 27 UFs e cinco regiões;
- estabilidade dos indicadores nacionais;
- soma de 100% nas composições de cada ano;
- estrutura das figuras Plotly;
- inicialização da aplicação e recálculo após interação com os filtros.

## 7. Próximo incremento

Implementar a página de distribuição espacial, integrando:

- `states_web.geojson`;
- indicadores estaduais calculados a partir da tabela fato;
- mapa coroplético;
- ranking associado;
- seleção de ano ou variação;
- tooltips com UF, região, valor e posição.

## 8. Referências técnicas

- [Aplicações multipágina com `st.Page` e `st.navigation`](https://docs.streamlit.io/develop/concepts/multipage-apps/page-and-navigation)
- [Cache de dados com `st.cache_data`](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.cache_data)
- [Figuras Plotly no Streamlit](https://docs.streamlit.io/develop/api-reference/charts/st.plotly_chart)
