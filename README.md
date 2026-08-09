<!-- Cabeçalho -->

<img src="./assets/banner/panorama_capa.png" alt="Capa Panorama da População Indígena Brasileira" width="100%">

<h2 align="center">
<em>Uma investigação baseada em dados sobre a evolução espacial e demográfica da população indígena ao longo de 12 anos.</em>
</h2>

## Sobre o Projeto

Este repositório reúne um conjunto de estudos sobre a população indígena brasileira a partir dos dados dos Censos Demográficos de **2010** e **2022**, publicados pelo **Instituto Brasileiro de Geografia e Estatística (IBGE)**.

O projeto investiga a evolução da população indígena sob diferentes perspectivas, utilizando técnicas de **Análise Exploratória de Dados (EDA)**, **Data Storytelling** e visualização de dados para transformar informações estatísticas em narrativas analíticas acessíveis.

---

## Motivação

A escolha deste tema decorre da relevância social e demográfica da população indígena brasileira, bem como da disponibilidade dos dados publicados pelo Censo Demográfico de 2022. A divulgação dessa nova base pelo IBGE oferece a oportunidade de investigar as transformações ocorridas ao longo de doze anos, permitindo analisar mudanças na distribuição espacial, na urbanização e na ocupação de Terras Indígenas. Além de sua importância para a formulação de políticas públicas, o conjunto de dados apresenta características adequadas para a aplicação de técnicas de análise exploratória, visualização de dados e data storytelling.

---

# Objetivos

O projeto busca responder questões como:

- O crescimento da população indígena entre 2010 e 2022 foi realmente significativo?
- Esse crescimento ocorreu igualmente em áreas urbanas e rurais?
- Onde a população indígena está concentrada: dentro ou fora das Terras Indígenas?
- Como essa distribuição varia entre estados e regiões brasileiras?
- Quais padrões espaciais podem ser observados a partir dos dados do Censo?

---

# Estrutura do Projeto

```text

├── assets/
├── data/
│   ├── external/
│   ├── geo/
│   ├── processed/
│   └── raw/
├── notebooks/
│   ├── 01-01_preprocessing_data_base.ipynb
│   ├── 01-02_demographic_analysis.ipynb
│   ├── 02-01_preprocessing_geo_ibge.ipynb
│   └── 02-02_spatial_analysis.ipynb
├── outputs/
│   ├── figures/
│   │   ├── graphic/
│   │   └── map/
│   └── tables/
├── src/
│   ├── geospatial/
│   └── visualization/
└── README.md
```

---

# Tecnologias

- Python
- Pandas
- NumPy
- Matplotlib
- Seaborn
- Jupyter Notebook

---

# Fonte dos Dados

Instituto Brasileiro de Geografia e Estatística (IBGE)

**Pessoas indígenas por localização e situação do domicílio, segundo as Grandes Regiões e Unidades da Federação – Brasil – 2010/2022**

https://www.ibge.gov.br/estatisticas/sociais/populacao/22827-censo-demografico-2022.html

**Malha Municipal Digital e Áreas Territoriais 2025**

https://www.ibge.gov.br/geociencias/organizacao-do-territorio/malhas-territoriais/15774-malhas.html

---

# Próximos Estudos

- Dashboard interativo.
- Integração com outras bases públicas (IBGE, FUNAI, INPE, entre outras).

---

# Autor

**Lucas Dias Noronha**

LinkedIn:

https://www.linkedin.com/in/lucasdiasnoronha/

GitHub:

https://github.com/LUCASDNORONHA/exploracao-dados-indigenas-2010-2022
