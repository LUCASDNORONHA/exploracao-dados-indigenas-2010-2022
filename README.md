<!-- Cabeçalho -->
<br />
<p align="center">
  <a href="https://github.com/LUCASDNORONHA/exploracao-dados-indigenas-2010-2022">
    <img src="assets/IESB_Logo.png" alt="Logo" width="150" height="150">
  </a>
</p>

<h1 align="center">
Panorama da População Indígena Brasileira (2010–2022)
</h1>

<p align="center">
Análise exploratória e explicativa baseada nos Censos Demográficos de 2010 e 2022 do IBGE.
</p>

---

## Sobre o Projeto

Este repositório reúne um conjunto de estudos sobre a população indígena brasileira a partir dos dados dos Censos Demográficos de **2010** e **2022**, publicados pelo **Instituto Brasileiro de Geografia e Estatística (IBGE)**.

O projeto investiga a evolução da população indígena sob diferentes perspectivas, utilizando técnicas de **Análise Exploratória de Dados (EDA)**, **Data Storytelling** e visualização de dados para transformar informações estatísticas em narrativas analíticas acessíveis.

Embora tenha sido inicialmente desenvolvido como um trabalho da disciplina **Introdução à Ciência de Dados**, do curso de **Bacharelado em Ciência de Dados e Inteligência Artificial** do **IESB**, o projeto foi posteriormente expandido e evoluiu para um estudo independente, incorporando novas análises, melhorias na arquitetura do código e futuras integrações com dashboards e análises espaciais.

---

## Motivação

A escolha deste tema decorre da relevância social e demográfica da população indígena brasileira, bem como da disponibilidade dos dados publicados pelo Censo Demográfico de 2022. A divulgação dessa nova base pelo IBGE oferece a oportunidade de investigar as transformações ocorridas ao longo de doze anos, permitindo analisar mudanças na distribuição espacial, na urbanização e na ocupação de Terras Indígenas. Além de sua importância para a formulação de políticas públicas, o conjunto de dados apresenta características adequadas para a aplicação de técnicas de análise exploratória, visualização de dados e data storytelling.

...

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
.
├── assets/
├── data/
├── notebooks/
│   ├── 01_preprocessing.ipynb
│   ├── 02_demographic_analysis.ipynb
│   ├── 03_spatial_analysis.ipynb
│   ├── 04_interactive_dashboard.ipynb
│   └── 05_statistical_analysis.ipynb
├── reports/
├── src/
│   ├── analise_dados/
│   └── visualization/
└── README.md
```

---

# Estudos Desenvolvidos

## 1. Pré-processamento dos Dados

- Limpeza dos dados do Censo.
- Padronização das variáveis.
- Criação das bases nacionais, regionais e estaduais.
- Organização da estrutura utilizada nas análises posteriores.

---

## 2. Análise Demográfica

Investiga:

- crescimento da população indígena;
- distribuição urbano × rural;
- população residente em Terras Indígenas;
- população residente fora das Terras Indígenas.

Utiliza princípios de **Data Storytelling** para responder perguntas orientadas pelos dados.

---

## 3. Análise Espacial *(em desenvolvimento)*

Objetivos:

- mapas coropléticos;
- distribuição por estados;
- distribuição por regiões;
- crescimento absoluto;
- crescimento percentual.

---

## 4. Dashboard Interativo *(planejado)*

Construção de um dashboard em Streamlit contendo:

- KPIs;
- filtros por estado e região;
- mapas;
- gráficos interativos.

---

## 5. Análise Estatística *(planejada)*

Exploração estatística da base por meio de:

- estatística descritiva;
- correlação;
- análise de distribuições;
- identificação de padrões.

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

---

# Origem do Projeto

Este projeto teve origem como trabalho da disciplina **Introdução à Ciência de Dados**, do curso de **Bacharelado em Ciência de Dados e Inteligência Artificial** do **IESB**, ministrada pelo professor **Alexandre Vaz Roriz** no primeiro semestre de 2025.

Após a conclusão da disciplina, o projeto passou a ser desenvolvido de forma independente como parte do portfólio profissional do autor, recebendo novas análises, melhorias na organização do código e expansão do escopo original.

---

# Próximos Estudos

- Análise espacial da população indígena.
- Comparação entre estados brasileiros.
- Comparação entre regiões.
- Dashboard interativo.
- Integração com outras bases públicas (IBGE, FUNAI, INPE, entre outras).

---

# Autor

**Lucas Dias Noronha**

LinkedIn:

https://www.linkedin.com/in/lucasdiasnoronha/

GitHub:

https://github.com/LUCASDNORONHA/exploracao-dados-indigenas-2010-2022
