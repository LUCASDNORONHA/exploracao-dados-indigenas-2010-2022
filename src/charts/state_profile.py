from pathlib import Path
from typing import ClassVar

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter, MultipleLocator


class PlotPerfilEstadual:
    """
    Constrói as visualizações do Estudo 4 — Perfil Estadual.

    A classe recebe a base das 27 Unidades da Federação e produz
    gráficos voltados às perguntas analíticas do estudo:

    1. concentração da população indígena dentro das regiões;
    2. peso regional da UF versus presença em Terras Indígenas;
    3. consistência estadual do padrão urbano-rural;
    4. crescimento absoluto versus crescimento relativo;
    5. mudança da proporção urbana entre 2010 e 2022.
    """

    ORDEM_REGIOES: ClassVar[list[str]] = [
        "Norte",
        "Nordeste",
        "Centro-Oeste",
        "Sudeste",
        "Sul",
    ]

    UF_REGIAO: ClassVar[dict[str, str]] = {
        "Rondônia": "Norte",
        "Acre": "Norte",
        "Amazonas": "Norte",
        "Roraima": "Norte",
        "Pará": "Norte",
        "Amapá": "Norte",
        "Tocantins": "Norte",
        "Maranhão": "Nordeste",
        "Piauí": "Nordeste",
        "Ceará": "Nordeste",
        "Rio Grande do Norte": "Nordeste",
        "Paraíba": "Nordeste",
        "Pernambuco": "Nordeste",
        "Alagoas": "Nordeste",
        "Sergipe": "Nordeste",
        "Bahia": "Nordeste",
        "Minas Gerais": "Sudeste",
        "Espírito Santo": "Sudeste",
        "Rio de Janeiro": "Sudeste",
        "São Paulo": "Sudeste",
        "Paraná": "Sul",
        "Santa Catarina": "Sul",
        "Rio Grande do Sul": "Sul",
        "Mato Grosso do Sul": "Centro-Oeste",
        "Mato Grosso": "Centro-Oeste",
        "Goiás": "Centro-Oeste",
        "Distrito Federal": "Centro-Oeste",
    }

    CORES_REGIOES: ClassVar[dict[str, str]] = {
        "Norte": "#173F5F",
        "Nordeste": "#2D5A80",
        "Centro-Oeste": "#39708E",
        "Sudeste": "#5E8EAA",
        "Sul": "#8FB7CF",
    }

    MARCADORES_REGIOES: ClassVar[dict[str, str]] = {
        "Norte": "o",
        "Nordeste": "s",
        "Centro-Oeste": "D",
        "Sudeste": "^",
        "Sul": "P",
    }

    def __init__(
        self,
        df: pd.DataFrame,
        diretorio_saida: str | Path,
    ) -> None:
        self.df = df.copy()
        self.diretorio_saida = Path(diretorio_saida)

        # Identidade visual já consolidada nos estudos anteriores.
        self.cor_clara = "#DCEAF2"
        self.cor_urbano = "#8FB7CF"
        self.cor_media = "#39708E"
        self.cor_escura = "#173F5F"
        self.cor_texto = "#263238"
        self.cor_secundaria = "#607D8B"
        self.cor_grade = "#D9E1E5"
        self.cor_fundo = "#FFFFFF"
        self.cor_caixa_clara = "#EAF3F8"
        self.cor_negativa = "#B5483A"
        self.cor_negativa_clara = "#C98579"

        self._preparar_e_validar_base()

    @staticmethod
    def _normalizar_regiao(regiao: str) -> str:
        """Padroniza variações usuais dos nomes das Grandes Regiões."""

        valor = str(regiao).strip()

        equivalencias = {
            "NORTE": "Norte",
            "NORDESTE": "Nordeste",
            "SUDESTE": "Sudeste",
            "SUL": "Sul",
            "CENTRO-OESTE": "Centro-Oeste",
            "Centro-oeste": "Centro-Oeste",
            "Centro Oeste": "Centro-Oeste",
            "Centro oeste": "Centro-Oeste",
        }

        return equivalencias.get(valor, valor)

    def _preparar_e_validar_base(self) -> None:
        """Prepara a dimensão regional e valida a unidade de análise."""

        if not isinstance(self.df, pd.DataFrame):
            raise TypeError("O objeto informado deve ser um DataFrame.")

        if self.df.empty:
            raise ValueError("A base estadual está vazia.")

        if "Localidade" not in self.df.columns:
            raise KeyError("A coluna 'Localidade' não existe na base estadual.")

        if self.df["Localidade"].duplicated().any():
            duplicadas = self.df.loc[
                self.df["Localidade"].duplicated(keep=False),
                "Localidade",
            ].tolist()

            raise ValueError(
                "A base possui Unidades da Federação duplicadas: "
                f"{sorted(set(duplicadas))}"
            )

        if "Região" not in self.df.columns:
            self.df["Região"] = self.df["Localidade"].map(self.UF_REGIAO)
        else:
            self.df["Região"] = self.df["Região"].map(self._normalizar_regiao)

        regioes_ausentes = self.df.loc[
            self.df["Região"].isna(),
            "Localidade",
        ].tolist()

        if regioes_ausentes:
            raise ValueError(
                "Não foi possível identificar a região das UFs: "
                f"{regioes_ausentes}"
            )

        ufs_encontradas = set(self.df["Localidade"])
        ufs_esperadas = set(self.UF_REGIAO)

        ufs_ausentes = sorted(ufs_esperadas - ufs_encontradas)
        ufs_extras = sorted(ufs_encontradas - ufs_esperadas)

        if ufs_ausentes or ufs_extras:
            raise ValueError(
                "A base deve representar exatamente as 27 UFs. "
                f"Ausentes: {ufs_ausentes}. Extras: {ufs_extras}."
            )

        regioes_encontradas = set(self.df["Região"])
        regioes_esperadas = set(self.ORDEM_REGIOES)

        if regioes_encontradas != regioes_esperadas:
            raise ValueError(
                "A base deve conter as cinco Grandes Regiões. "
                f"Encontradas: {sorted(regioes_encontradas)}."
            )

        self.df["Região"] = pd.Categorical(
            self.df["Região"],
            categories=self.ORDEM_REGIOES,
            ordered=True,
        )

    def _validar_colunas(
        self,
        colunas: list[str],
    ) -> None:
        """Valida presença, tipo e sinal das variáveis quantitativas."""

        colunas_ausentes = [
            coluna
            for coluna in colunas
            if coluna not in self.df.columns
        ]

        if colunas_ausentes:
            raise KeyError(
                "As seguintes colunas não existem na base: "
                f"{colunas_ausentes}"
            )

        colunas_nao_numericas = [
            coluna
            for coluna in colunas
            if not pd.api.types.is_numeric_dtype(self.df[coluna])
        ]

        if colunas_nao_numericas:
            raise TypeError(
                "As seguintes colunas devem ser numéricas: "
                f"{colunas_nao_numericas}"
            )

        colunas_com_negativos = [
            coluna
            for coluna in colunas
            if self.df[coluna].lt(0).any()
        ]

        if colunas_com_negativos:
            raise ValueError(
                "As seguintes colunas possuem contagens negativas: "
                f"{colunas_com_negativos}"
            )

    @staticmethod
    def _formatar_inteiro(valor: float) -> str:
        """Formata números inteiros com separador de milhar brasileiro."""

        return f"{valor:,.0f}".replace(",", ".")

    @staticmethod
    def _formatar_percentual(
        valor: float,
        casas_decimais: int = 1,
    ) -> str:
        """Formata percentuais com vírgula decimal."""

        return f"{valor:.{casas_decimais}f}".replace(".", ",")

    def _adicionar_cabecalho(
        self,
        fig,
        titulo: str,
        subtitulo: str,
        y_titulo: float = 0.975,
        y_subtitulo: float = 0.875,
    ) -> None:
        """Adiciona título orientado ao achado e subtítulo explicativo."""

        fig.text(
            0.06,
            y_titulo,
            titulo,
            ha="left",
            va="top",
            fontsize=23.0,
            fontweight="bold",
            color=self.cor_texto,
            linespacing=1.20,
        )

        fig.text(
            0.06,
            y_subtitulo,
            subtitulo,
            ha="left",
            va="top",
            fontsize=12.0,
            color=self.cor_secundaria,
            linespacing=1.30,
        )

    def _adicionar_fonte(
        self,
        fig,
        texto: str,
        y: float = 0.022,
    ) -> None:
        """Adiciona fonte e autoria à figura."""

        fig.text(
            0.06,
            y,
            texto,
            ha="left",
            va="bottom",
            fontsize=8.5,
            color=self.cor_secundaria,
        )

    def _aplicar_estilo_eixo(
        self,
        ax,
        eixo_grade: str = "x",
    ) -> None:
        """Aplica o padrão visual básico aos eixos."""

        ax.set_facecolor(self.cor_fundo)

        for lado in ("top", "right", "left", "bottom"):
            ax.spines[lado].set_visible(False)

        ax.tick_params(
            axis="both",
            length=0,
            labelcolor=self.cor_texto,
        )

        ax.grid(
            axis=eixo_grade,
            linestyle="--",
            linewidth=0.7,
            alpha=0.55,
            color=self.cor_grade,
        )

        ax.set_axisbelow(True)

    def _finalizar_grafico(
        self,
        fig,
        nome_arquivo: str,
        exibir: bool,
    ) -> Path:
        """Salva, exibe opcionalmente e encerra a figura."""

        self.diretorio_saida.mkdir(
            parents=True,
            exist_ok=True,
        )

        caminho_saida = self.diretorio_saida / nome_arquivo

        fig.savefig(
            caminho_saida,
            dpi=300,
            bbox_inches="tight",
            facecolor=self.cor_fundo,
        )

        if exibir:
            plt.show()

        plt.close(fig)

        return caminho_saida

    def _calcular_participacoes(self) -> pd.DataFrame:
        """Calcula participação nacional, regional e presença em TI."""

        colunas = [
            "Indígenas 2022 Total",
            "Indígenas 2022 TI Total",
        ]

        self._validar_colunas(colunas)

        dados = self.df[
            [
                "Localidade",
                "Região",
                *colunas,
            ]
        ].copy()

        if dados["Indígenas 2022 Total"].le(0).any():
            raise ValueError(
                "Todos os totais estaduais de 2022 devem ser positivos."
            )

        total_brasil = dados["Indígenas 2022 Total"].sum()
        total_regional = dados.groupby(
            "Região",
            observed=True,
        )["Indígenas 2022 Total"].transform("sum")

        dados["Participação no Brasil (%)"] = (
            dados["Indígenas 2022 Total"]
            .div(total_brasil)
            .mul(100)
        )

        dados["Participação na Região (%)"] = (
            dados["Indígenas 2022 Total"]
            .div(total_regional)
            .mul(100)
        )

        dados["Indígenas em TI (%)"] = (
            dados["Indígenas 2022 TI Total"]
            .div(dados["Indígenas 2022 Total"])
            .mul(100)
        )

        return dados

    def _calcular_perfil_contexto(self) -> pd.DataFrame:
        """Calcula a proporção urbana dentro e fora de TI."""

        colunas = [
            "Indígenas 2022 TI Total",
            "Indígenas 2022 TI Urbano",
            "Indígenas 2022 TI Rural",
            "Indígenas 2022 Fora TI Total",
            "Indígenas 2022 Fora TI Urbano",
            "Indígenas 2022 Fora TI Rural",
        ]

        self._validar_colunas(colunas)

        dados = self.df[
            [
                "Localidade",
                "Região",
                *colunas,
            ]
        ].copy()

        if not (
            dados["Indígenas 2022 TI Total"]
            == dados["Indígenas 2022 TI Urbano"]
            + dados["Indígenas 2022 TI Rural"]
        ).all():
            raise ValueError(
                "O total em TI não coincide com a soma urbano + rural."
            )

        if not (
            dados["Indígenas 2022 Fora TI Total"]
            == dados["Indígenas 2022 Fora TI Urbano"]
            + dados["Indígenas 2022 Fora TI Rural"]
        ).all():
            raise ValueError(
                "O total fora de TI não coincide com a soma urbano + rural."
            )

        denominador_ti = dados["Indígenas 2022 TI Total"].where(
            dados["Indígenas 2022 TI Total"].ne(0)
        )

        denominador_fora_ti = dados["Indígenas 2022 Fora TI Total"].where(
            dados["Indígenas 2022 Fora TI Total"].ne(0)
        )

        dados["TI urbano (%)"] = (
            dados["Indígenas 2022 TI Urbano"]
            .div(denominador_ti)
            .mul(100)
        )

        dados["Fora TI urbano (%)"] = (
            dados["Indígenas 2022 Fora TI Urbano"]
            .div(denominador_fora_ti)
            .mul(100)
        )

        return dados

    def _calcular_crescimento(self) -> pd.DataFrame:
        """Calcula o crescimento estadual absoluto e relativo."""

        colunas = [
            "Indígenas 2010 Total",
            "Indígenas 2022 Total",
        ]

        self._validar_colunas(colunas)

        dados = self.df[
            [
                "Localidade",
                "Região",
                *colunas,
            ]
        ].copy()

        if dados["Indígenas 2010 Total"].le(0).any():
            raise ValueError(
                "Todos os totais estaduais de 2010 devem ser positivos."
            )

        dados["Crescimento absoluto"] = (
            dados["Indígenas 2022 Total"]
            - dados["Indígenas 2010 Total"]
        )

        dados["Crescimento relativo (%)"] = (
            dados["Crescimento absoluto"]
            .div(dados["Indígenas 2010 Total"])
            .mul(100)
        )

        return dados

    def _calcular_mudanca_urbanizacao(self) -> pd.DataFrame:
        """Calcula a variação da proporção urbana em pontos percentuais."""

        colunas = [
            "Indígenas 2010 Total",
            "Indígenas 2010 Urbano",
            "Indígenas 2022 Total",
            "Indígenas 2022 Urbano",
        ]

        self._validar_colunas(colunas)

        dados = self.df[
            [
                "Localidade",
                "Região",
                *colunas,
            ]
        ].copy()

        if (
            dados["Indígenas 2010 Total"].le(0).any()
            or dados["Indígenas 2022 Total"].le(0).any()
        ):
            raise ValueError(
                "Os totais estaduais de 2010 e 2022 devem ser positivos."
            )

        dados["Urbanização 2010 (%)"] = (
            dados["Indígenas 2010 Urbano"]
            .div(dados["Indígenas 2010 Total"])
            .mul(100)
        )

        dados["Urbanização 2022 (%)"] = (
            dados["Indígenas 2022 Urbano"]
            .div(dados["Indígenas 2022 Total"])
            .mul(100)
        )

        dados["Mudança na urbanização (p.p.)"] = (
            dados["Urbanização 2022 (%)"]
            - dados["Urbanização 2010 (%)"]
        )

        return dados

    def plot_concentracao_intrarregional(
        self,
        exibir: bool = True,
    ) -> Path:
        """
        Mostra a participação de cada UF no total indígena de sua região.

        O arranjo em pequenos múltiplos preserva a hierarquia regional,
        permite comparar as UFs dentro de cada grupo e evita transformar
        as 27 unidades em um único ranking sem contexto.
        """

        dados = self._calcular_participacoes()

        mosaico = [
            ["Norte", "Nordeste"],
            ["Centro-Oeste", "Sudeste"],
            ["Sul", "Insight"],
        ]

        fig, eixos = plt.subplot_mosaic(
            mosaico,
            figsize=(15, 13),
            gridspec_kw={
                "height_ratios": [
                    1.75,
                    1.05,
                    0.85,
                ]
            },
        )

        fig.subplots_adjust(
            left=0.10,
            right=0.96,
            top=0.79,
            bottom=0.07,
            wspace=0.30,
            hspace=0.55,
        )

        for regiao in self.ORDEM_REGIOES:
            ax = eixos[regiao]

            dados_regiao = (
                dados.loc[
                    dados["Região"].eq(regiao),
                    [
                        "Localidade",
                        "Participação na Região (%)",
                    ],
                ]
                .sort_values(
                    "Participação na Região (%)",
                    ascending=True,
                )
                .reset_index(drop=True)
            )

            indice_lider = int(
                dados_regiao["Participação na Região (%)"].idxmax()
            )

            cores = [
                (
                    self.cor_escura
                    if indice == indice_lider
                    else self.cor_media
                )
                for indice in dados_regiao.index
            ]

            posicoes = np.arange(len(dados_regiao))

            barras = ax.barh(
                posicoes,
                dados_regiao["Participação na Região (%)"],
                color=cores,
                height=0.62,
            )

            ax.set_yticks(posicoes)
            ax.set_yticklabels(
                dados_regiao["Localidade"],
                fontsize=9.2,
            )

            for indice, barra in enumerate(barras):
                valor = float(
                    dados_regiao.loc[
                        indice,
                        "Participação na Região (%)",
                    ]
                )

                ax.text(
                    valor + 1.0,
                    barra.get_y() + barra.get_height() / 2,
                    f"{self._formatar_percentual(valor)}%",
                    ha="left",
                    va="center",
                    fontsize=8.8,
                    fontweight=(
                        "bold"
                        if indice == indice_lider
                        else "normal"
                    ),
                    color=(
                        self.cor_escura
                        if indice == indice_lider
                        else self.cor_secundaria
                    ),
                )

            ax.set_title(
                regiao.upper(),
                loc="left",
                fontsize=12.0,
                fontweight="bold",
                color=self.cor_escura,
                pad=10,
            )

            ax.set_xlim(0, 72)
            ax.xaxis.set_major_locator(MultipleLocator(20))
            ax.xaxis.set_major_formatter(
                FuncFormatter(
                    lambda valor, _: f"{valor:.0f}%"
                )
            )

            self._aplicar_estilo_eixo(
                ax=ax,
                eixo_grade="x",
            )

            ax.tick_params(
                axis="x",
                labelsize=8.5,
                labelcolor=self.cor_secundaria,
            )

        ax_insight = eixos["Insight"]
        ax_insight.axis("off")

        ax_insight.text(
            0,
            1,
            "PRINCIPAL ACHADO",
            ha="left",
            va="top",
            fontsize=14.0,
            fontweight="bold",
            color=self.cor_escura,
        )

        ax_insight.text(
            0,
            0.82,
            (
                "Norte, Centro-Oeste, Sudeste e Nordeste\n"
                "têm mais de 43% de sua população indígena\n"
                "concentrada em uma única UF.\n\n"
                "No Sul, a distribuição é mais equilibrada:\n"
                "nenhum estado alcança metade do total regional."
            ),
            ha="left",
            va="top",
            fontsize=11.0,
            color="white",
            linespacing=1.35,
            bbox={
                "boxstyle": "round,pad=0.80",
                "facecolor": self.cor_escura,
                "edgecolor": "none",
                "alpha": 0.98,
            },
        )

        self._adicionar_cabecalho(
            fig=fig,
            titulo=(
                "Uma única UF concentra mais de 43% da população indígena\n"
                "em quatro das cinco Grandes Regiões"
            ),
            subtitulo=(
                "Participação de cada Unidade da Federação no total da "
                "população indígena de sua região — 2022"
            ),
        )

        self._adicionar_fonte(
            fig=fig,
            texto=(
                "Fonte: IBGE — Censo Demográfico 2022. "
                "Elaboração: Lucas Dias Noronha."
            ),
        )

        return self._finalizar_grafico(
            fig=fig,
            nome_arquivo="grafico_concentracao_intrarregional_2022.png",
            exibir=exibir,
        )

    def plot_peso_regional_vs_presenca_ti(
        self,
        exibir: bool = True,
    ) -> Path:
        """
        Relaciona o peso populacional regional e a presença em TI.

        O gráfico de dispersão é adequado porque cada UF possui duas
        medidas quantitativas independentes. Não é traçada uma diagonal
        de igualdade, pois os eixos utilizam denominadores diferentes.
        """

        dados = self._calcular_participacoes()

        lideres = (
            dados.sort_values(
                [
                    "Região",
                    "Participação na Região (%)",
                ],
                ascending=[
                    True,
                    False,
                ],
            )
            .groupby(
                "Região",
                observed=True,
                as_index=False,
            )
            .head(1)
        )

        nomes_lideres = set(lideres["Localidade"])

        fig, ax = plt.subplots(
            figsize=(15, 9),
        )

        fig.subplots_adjust(
            left=0.08,
            right=0.69,
            top=0.78,
            bottom=0.13,
        )

        for regiao in self.ORDEM_REGIOES:
            dados_regiao = dados.loc[
                dados["Região"].eq(regiao)
            ]

            ax.scatter(
                dados_regiao["Participação na Região (%)"],
                dados_regiao["Indígenas em TI (%)"],
                s=80,
                marker=self.MARCADORES_REGIOES[regiao],
                color=self.CORES_REGIOES[regiao],
                edgecolor="white",
                linewidth=0.8,
                alpha=0.88,
                zorder=3,
            )

        dados_lideres = dados.loc[
            dados["Localidade"].isin(nomes_lideres)
        ]

        for _, linha in dados_lideres.iterrows():
            regiao = str(linha["Região"])

            ax.scatter(
                float(linha["Participação na Região (%)"]),
                float(linha["Indígenas em TI (%)"]),
                s=155,
                marker=self.MARCADORES_REGIOES[regiao],
                color=self.CORES_REGIOES[regiao],
                edgecolor=self.cor_texto,
                linewidth=1.4,
                zorder=5,
            )

        deslocamentos = {
            "Amazonas": (-155, 18),
            "Bahia": (-145, 26),
            "Mato Grosso do Sul": (-165, 24),
            "São Paulo": (24, 28),
            "Rio Grande do Sul": (18, 16),
        }

        for _, linha in dados_lideres.iterrows():
            uf = str(linha["Localidade"])
            x = float(linha["Participação na Região (%)"])
            y = float(linha["Indígenas em TI (%)"])
            deslocamento = deslocamentos[uf]

            ax.annotate(
                (
                    f"{uf}\n"
                    f"{self._formatar_percentual(x)}% da região | "
                    f"{self._formatar_percentual(y)}% em TI"
                ),
                xy=(x, y),
                xytext=deslocamento,
                textcoords="offset points",
                ha="left",
                va="center",
                fontsize=8.4,
                color=self.cor_texto,
                linespacing=1.25,
                bbox={
                    "boxstyle": "round,pad=0.42",
                    "facecolor": "white",
                    "edgecolor": self.cor_grade,
                    "linewidth": 0.9,
                    "alpha": 0.98,
                },
                arrowprops={
                    "arrowstyle": "-",
                    "color": self.cor_secundaria,
                    "linewidth": 0.9,
                },
                zorder=6,
            )

        ax.set_xlim(-2, 72)
        ax.set_ylim(-2, 82)

        ax.xaxis.set_major_locator(MultipleLocator(10))
        ax.yaxis.set_major_locator(MultipleLocator(10))

        ax.xaxis.set_major_formatter(
            FuncFormatter(
                lambda valor, _: f"{valor:.0f}%"
            )
        )
        ax.yaxis.set_major_formatter(
            FuncFormatter(
                lambda valor, _: f"{valor:.0f}%"
            )
        )

        ax.set_xlabel(
            "Participação da UF na população indígena regional",
            fontsize=10.5,
            color=self.cor_texto,
            labelpad=12,
        )
        ax.set_ylabel(
            "Proporção da população indígena da UF residente em TI",
            fontsize=10.5,
            color=self.cor_texto,
            labelpad=12,
        )

        self._aplicar_estilo_eixo(
            ax=ax,
            eixo_grade="both",
        )

        handles = [
            Line2D(
                [0],
                [0],
                marker=self.MARCADORES_REGIOES[regiao],
                color="none",
                markerfacecolor=self.CORES_REGIOES[regiao],
                markeredgecolor="white",
                markersize=9,
                label=regiao,
            )
            for regiao in self.ORDEM_REGIOES
        ]

        fig.text(
            0.735,
            0.755,
            "GRANDES REGIÕES",
            ha="left",
            va="top",
            fontsize=12.0,
            fontweight="bold",
            color=self.cor_escura,
        )

        fig.legend(
            handles=handles,
            loc="upper left",
            bbox_to_anchor=(0.725, 0.72),
            frameon=False,
            fontsize=10.0,
            labelspacing=1.0,
        )

        fig.text(
            0.735,
            0.465,
            "PRINCIPAL ACHADO",
            ha="left",
            va="top",
            fontsize=12.0,
            fontweight="bold",
            color=self.cor_escura,
        )

        fig.text(
            0.735,
            0.415,
            (
                "Grande peso regional não implica\n"
                "alta presença em Terras Indígenas.\n\n"
                "Amazonas, Bahia e São Paulo lideram\n"
                "suas regiões, mas registram proporções\n"
                "em TI inferiores às de várias UFs\n"
                "com menor contingente populacional.\n\n"
                "Mato Grosso do Sul combina as duas\n"
                "características: grande peso regional\n"
                "e elevada presença em TI."
            ),
            ha="left",
            va="top",
            fontsize=10.2,
            color="white",
            linespacing=1.35,
            bbox={
                "boxstyle": "round,pad=0.75",
                "facecolor": self.cor_escura,
                "edgecolor": "none",
                "alpha": 0.98,
            },
        )

        fig.text(
            0.735,
            0.105,
            (
                "Como ler: os eixos possuem denominadores\n"
                "diferentes e não devem ser somados nem\n"
                "comparados por uma linha de igualdade."
            ),
            ha="left",
            va="bottom",
            fontsize=8.8,
            color=self.cor_secundaria,
            linespacing=1.30,
        )

        self._adicionar_cabecalho(
            fig=fig,
            titulo=(
                "As UFs que mais influenciam suas regiões não são,\n"
                "necessariamente, as que mais concentram população em TI"
            ),
            subtitulo=(
                "Relação entre participação no total indígena regional e "
                "proporção da população indígena da UF residente em "
                "Terras Indígenas — 2022"
            ),
        )

        self._adicionar_fonte(
            fig=fig,
            texto=(
                "Fonte: IBGE — Censo Demográfico 2022. "
                "Elaboração: Lucas Dias Noronha."
            ),
        )

        return self._finalizar_grafico(
            fig=fig,
            nome_arquivo="grafico_peso_regional_presenca_ti_2022.png",
            exibir=exibir,
        )

    def plot_padrao_territorial_estadual(
        self,
        exibir: bool = True,
    ) -> Path:
        """
        Testa o padrão urbano-rural dentro e fora de TI nas UFs.

        As linhas de 50% dividem o plano segundo a categoria
        predominante. O quadrante superior esquerdo representa o
        padrão encontrado no Estudo 3: TI predominantemente rural e
        áreas fora de TI predominantemente urbanas.
        """

        dados = self._calcular_perfil_contexto()

        comparaveis = dados.dropna(
            subset=[
                "TI urbano (%)",
                "Fora TI urbano (%)",
            ]
        ).copy()

        padrao = (
            comparaveis["TI urbano (%)"].lt(50)
            & comparaveis["Fora TI urbano (%)"].gt(50)
        )

        quantidade_padrao = int(padrao.sum())
        quantidade_comparavel = int(len(comparaveis))

        fig, ax = plt.subplots(
            figsize=(15, 9),
        )

        fig.subplots_adjust(
            left=0.08,
            right=0.69,
            top=0.78,
            bottom=0.13,
        )

        ax.fill_between(
            [0, 50],
            50,
            100,
            color=self.cor_caixa_clara,
            alpha=0.95,
            zorder=0,
        )

        demais = comparaveis.loc[
            comparaveis["Localidade"].ne("Ceará")
        ]
        ceara = comparaveis.loc[
            comparaveis["Localidade"].eq("Ceará")
        ]

        ax.scatter(
            demais["TI urbano (%)"],
            demais["Fora TI urbano (%)"],
            s=82,
            color=self.cor_media,
            edgecolor="white",
            linewidth=0.9,
            alpha=0.82,
            zorder=3,
        )

        ax.scatter(
            ceara["TI urbano (%)"],
            ceara["Fora TI urbano (%)"],
            s=175,
            color=self.cor_negativa,
            edgecolor=self.cor_texto,
            linewidth=1.3,
            zorder=5,
        )

        linha_ceara = ceara.iloc[0]
        x_ceara = float(linha_ceara["TI urbano (%)"])
        y_ceara = float(linha_ceara["Fora TI urbano (%)"])

        ax.annotate(
            (
                "Ceará\n"
                f"{self._formatar_percentual(x_ceara)}% urbano em TI\n"
                f"{self._formatar_percentual(y_ceara)}% urbano fora de TI"
            ),
            xy=(x_ceara, y_ceara),
            xytext=(18, 24),
            textcoords="offset points",
            ha="left",
            va="bottom",
            fontsize=9.0,
            color=self.cor_texto,
            bbox={
                "boxstyle": "round,pad=0.50",
                "facecolor": "white",
                "edgecolor": self.cor_negativa,
                "linewidth": 1.0,
                "alpha": 0.98,
            },
            arrowprops={
                "arrowstyle": "->",
                "color": self.cor_negativa,
                "linewidth": 1.1,
            },
            zorder=6,
        )

        ax.axvline(
            50,
            color=self.cor_secundaria,
            linewidth=1.2,
            linestyle="--",
            zorder=1,
        )
        ax.axhline(
            50,
            color=self.cor_secundaria,
            linewidth=1.2,
            linestyle="--",
            zorder=1,
        )

        ax.text(
            25,
            96,
            (
                "PADRÃO DO ESTUDO 3\n"
                "Em TI: rural • Fora de TI: urbano"
            ),
            ha="center",
            va="top",
            fontsize=10.0,
            fontweight="bold",
            color=self.cor_escura,
            linespacing=1.25,
        )

        ax.text(
            75,
            96,
            "Predominância urbana\nnos dois contextos",
            ha="center",
            va="top",
            fontsize=8.5,
            color=self.cor_secundaria,
        )
        ax.text(
            25,
            4,
            "Predominância rural\nnos dois contextos",
            ha="center",
            va="bottom",
            fontsize=8.5,
            color=self.cor_secundaria,
        )
        ax.text(
            75,
            4,
            "Em TI: urbano\nFora de TI: rural",
            ha="center",
            va="bottom",
            fontsize=8.5,
            color=self.cor_secundaria,
        )

        ax.set_xlim(-3, 103)
        ax.set_ylim(-3, 103)
        ax.set_aspect(
            "equal",
            adjustable="box",
        )

        ax.set_xticks(np.arange(0, 101, 10))
        ax.set_yticks(np.arange(0, 101, 10))

        ax.xaxis.set_major_formatter(
            FuncFormatter(
                lambda valor, _: f"{valor:.0f}%"
            )
        )
        ax.yaxis.set_major_formatter(
            FuncFormatter(
                lambda valor, _: f"{valor:.0f}%"
            )
        )

        ax.set_xlabel(
            "Proporção urbana dentro de Terras Indígenas",
            fontsize=10.5,
            color=self.cor_texto,
            labelpad=12,
        )
        ax.set_ylabel(
            "Proporção urbana fora de Terras Indígenas",
            fontsize=10.5,
            color=self.cor_texto,
            labelpad=12,
        )

        self._aplicar_estilo_eixo(
            ax=ax,
            eixo_grade="both",
        )

        fig.text(
            0.735,
            0.715,
            "CONSISTÊNCIA DO PADRÃO",
            ha="left",
            va="top",
            fontsize=12.0,
            fontweight="bold",
            color=self.cor_escura,
        )

        fig.text(
            0.735,
            0.655,
            (
                f"{quantidade_padrao} de {quantidade_comparavel} UFs comparáveis\n"
                "reproduzem o padrão regional:\n\n"
                "• residência rural predominante em TI;\n"
                "• residência urbana predominante fora de TI.\n\n"
                "O Ceará é a única exceção entre as UFs\n"
                "com população contabilizada nos dois contextos."
            ),
            ha="left",
            va="top",
            fontsize=10.4,
            color="white",
            linespacing=1.40,
            bbox={
                "boxstyle": "round,pad=0.75",
                "facecolor": self.cor_escura,
                "edgecolor": "none",
                "alpha": 0.98,
            },
        )

        fig.text(
            0.735,
            0.300,
            "CASOS SEM COMPARAÇÃO COMPLETA",
            ha="left",
            va="top",
            fontsize=11.0,
            fontweight="bold",
            color=self.cor_escura,
        )

        fig.text(
            0.735,
            0.255,
            (
                "Rio Grande do Norte e Distrito Federal\n"
                "não possuem população contabilizada em TI.\n\n"
                "Fora de TI, o Rio Grande do Norte é a única\n"
                "UF com predominância rural: 46,0% urbano."
            ),
            ha="left",
            va="top",
            fontsize=9.5,
            color=self.cor_texto,
            linespacing=1.35,
            bbox={
                "boxstyle": "round,pad=0.70",
                "facecolor": self.cor_caixa_clara,
                "edgecolor": self.cor_urbano,
                "linewidth": 1.0,
                "alpha": 0.98,
            },
        )

        self._adicionar_cabecalho(
            fig=fig,
            titulo=(
                "O padrão regional repete-se em 24 das 25 UFs comparáveis"
            ),
            subtitulo=(
                "Proporção urbana dentro e fora de Terras Indígenas; "
                "as linhas de 50% indicam a mudança de predominância — 2022"
            ),
            y_subtitulo=0.905,
        )

        self._adicionar_fonte(
            fig=fig,
            texto=(
                "Fonte: IBGE — Censo Demográfico 2022. "
                "Elaboração: Lucas Dias Noronha."
            ),
        )

        return self._finalizar_grafico(
            fig=fig,
            nome_arquivo="grafico_padrao_territorial_estadual_2022.png",
            exibir=exibir,
        )

    def plot_crescimento_absoluto_relativo(
        self,
        quantidade: int = 10,
        exibir: bool = True,
    ) -> Path:
        """
        Compara os maiores crescimentos absolutos e relativos.

        Dois painéis de barras preservam as unidades próprias de cada
        medida e tornam explícito que os rankings respondem a perguntas
        diferentes.
        """

        if quantidade < 3 or quantidade > 27:
            raise ValueError(
                "A quantidade de UFs deve estar entre 3 e 27."
            )

        dados = self._calcular_crescimento()

        ranking_absoluto = (
            dados.nlargest(
                quantidade,
                "Crescimento absoluto",
            )
            .sort_values(
                "Crescimento absoluto",
                ascending=True,
            )
            .reset_index(drop=True)
        )

        ranking_relativo = (
            dados.nlargest(
                quantidade,
                "Crescimento relativo (%)",
            )
            .sort_values(
                "Crescimento relativo (%)",
                ascending=True,
            )
            .reset_index(drop=True)
        )

        fig, eixos = plt.subplots(
            1,
            2,
            figsize=(15, 10),
        )

        fig.subplots_adjust(
            left=0.10,
            right=0.96,
            top=0.76,
            bottom=0.18,
            wspace=0.48,
        )

        configuracoes = [
            {
                "ax": eixos[0],
                "dados": ranking_absoluto,
                "coluna": "Crescimento absoluto",
                "titulo": "CRESCIMENTO ABSOLUTO",
                "subtitulo": "Aumento em número de pessoas",
                "formatador": self._formatar_inteiro,
            },
            {
                "ax": eixos[1],
                "dados": ranking_relativo,
                "coluna": "Crescimento relativo (%)",
                "titulo": "CRESCIMENTO RELATIVO",
                "subtitulo": "Aumento em relação ao total de 2010",
                "formatador": (
                    lambda valor: (
                        f"{self._formatar_percentual(valor)}%"
                    )
                ),
            },
        ]

        for configuracao in configuracoes:
            ax = configuracao["ax"]
            dados_painel = configuracao["dados"]
            coluna = configuracao["coluna"]
            formatador = configuracao["formatador"]

            indice_maior = int(
                dados_painel[coluna].idxmax()
            )

            cores = [
                (
                    self.cor_escura
                    if indice == indice_maior
                    else self.cor_media
                )
                for indice in dados_painel.index
            ]

            posicoes = np.arange(len(dados_painel))

            barras = ax.barh(
                posicoes,
                dados_painel[coluna],
                color=cores,
                height=0.62,
            )

            ax.set_yticks(posicoes)
            ax.set_yticklabels(
                dados_painel["Localidade"],
                fontsize=9.2,
            )

            maior_valor = float(
                dados_painel[coluna].max()
            )

            deslocamento = maior_valor * 0.025

            for indice, barra in enumerate(barras):
                valor = float(
                    dados_painel.loc[
                        indice,
                        coluna,
                    ]
                )

                ax.text(
                    valor + deslocamento,
                    barra.get_y() + barra.get_height() / 2,
                    formatador(valor),
                    ha="left",
                    va="center",
                    fontsize=8.8,
                    fontweight=(
                        "bold"
                        if indice == indice_maior
                        else "normal"
                    ),
                    color=(
                        self.cor_escura
                        if indice == indice_maior
                        else self.cor_secundaria
                    ),
                )

            ax.set_xlim(
                0,
                maior_valor * 1.27,
            )

            ax.set_title(
                configuracao["titulo"],
                loc="left",
                fontsize=12.5,
                fontweight="bold",
                color=self.cor_escura,
                pad=24,
            )

            ax.text(
                0,
                1.01,
                configuracao["subtitulo"],
                transform=ax.transAxes,
                ha="left",
                va="bottom",
                fontsize=9.2,
                color=self.cor_secundaria,
            )

            self._aplicar_estilo_eixo(
                ax=ax,
                eixo_grade="x",
            )

            ax.set_xticks([])

        aumento_nacional = float(
            dados["Crescimento absoluto"].sum()
        )
        aumento_am_ba = float(
            dados.loc[
                dados["Localidade"].isin(
                    [
                        "Amazonas",
                        "Bahia",
                    ]
                ),
                "Crescimento absoluto",
            ].sum()
        )
        participacao_am_ba = aumento_am_ba / aumento_nacional * 100

        fig.text(
            0.50,
            0.105,
            (
                f"Amazonas e Bahia responderam por "
                f"{self._formatar_percentual(participacao_am_ba)}% do "
                "aumento nacional. Já o Rio Grande do Norte liderou em "
                "termos relativos porque partiu de uma base reduzida em 2010."
            ),
            ha="center",
            va="center",
            fontsize=10.3,
            color=self.cor_escura,
            bbox={
                "boxstyle": "round,pad=0.80",
                "facecolor": self.cor_caixa_clara,
                "edgecolor": self.cor_urbano,
                "linewidth": 1.0,
                "alpha": 0.98,
            },
        )

        self._adicionar_cabecalho(
            fig=fig,
            titulo=(
                "Amazonas lidera o crescimento absoluto;\n"
                "Rio Grande do Norte, o crescimento relativo"
            ),
            subtitulo=(
                f"As {quantidade} maiores variações segundo duas medidas "
                "complementares — Censos de 2010 e 2022"
            ),
        )

        self._adicionar_fonte(
            fig=fig,
            texto=(
                "Fonte: IBGE — Censos Demográficos de 2010 e 2022. "
                "Elaboração: Lucas Dias Noronha."
            ),
        )

        return self._finalizar_grafico(
            fig=fig,
            nome_arquivo=(
                "grafico_crescimento_estadual_absoluto_relativo.png"
            ),
            exibir=exibir,
        )

    def plot_mudanca_urbanizacao(
        self,
        exibir: bool = True,
    ) -> Path:
        """
        Mostra a mudança da proporção urbana em pontos percentuais.

        O gráfico divergente utiliza o zero como referência e distingue
        aumentos de reduções sem sugerir que a variação decorra,
        necessariamente, de migração.
        """

        dados = (
            self._calcular_mudanca_urbanizacao()
            .sort_values(
                "Mudança na urbanização (p.p.)",
                ascending=True,
            )
            .reset_index(drop=True)
        )

        cores = []

        for _, linha in dados.iterrows():
            uf = str(linha["Localidade"])
            valor = float(
                linha["Mudança na urbanização (p.p.)"]
            )

            if uf == "Amazonas":
                cor = self.cor_escura
            elif uf in {
                "Rio Grande do Norte",
                "Piauí",
            }:
                cor = self.cor_negativa
            elif valor >= 0:
                cor = self.cor_media
            else:
                cor = self.cor_negativa_clara

            cores.append(cor)

        fig, ax = plt.subplots(
            figsize=(14, 14.5),
        )

        fig.subplots_adjust(
            left=0.20,
            right=0.95,
            top=0.82,
            bottom=0.14,
        )

        posicoes = np.arange(len(dados))

        barras = ax.barh(
            posicoes,
            dados["Mudança na urbanização (p.p.)"],
            color=cores,
            height=0.62,
        )

        ax.set_yticks(posicoes)
        ax.set_yticklabels(
            dados["Localidade"],
            fontsize=9.0,
        )

        menor_valor = float(
            dados["Mudança na urbanização (p.p.)"].min()
        )
        maior_valor = float(
            dados["Mudança na urbanização (p.p.)"].max()
        )

        ax.set_xlim(
            menor_valor - 8,
            maior_valor + 9,
        )

        for indice, barra in enumerate(barras):
            valor = float(
                dados.loc[
                    indice,
                    "Mudança na urbanização (p.p.)",
                ]
            )

            if valor >= 0:
                x_texto = valor + 0.8
                alinhamento = "left"
            else:
                x_texto = valor - 0.8
                alinhamento = "right"

            uf = str(
                dados.loc[
                    indice,
                    "Localidade",
                ]
            )

            ax.text(
                x_texto,
                barra.get_y() + barra.get_height() / 2,
                (
                    f"{valor:+.1f}".replace(".", ",")
                    + " p.p."
                ),
                ha=alinhamento,
                va="center",
                fontsize=8.3,
                fontweight=(
                    "bold"
                    if uf in {
                        "Amazonas",
                        "Rio Grande do Norte",
                        "Piauí",
                    }
                    else "normal"
                ),
                color=(
                    self.cor_texto
                    if valor >= 0
                    else self.cor_negativa
                ),
            )

        ax.axvline(
            0,
            color=self.cor_texto,
            linewidth=1.1,
            zorder=1,
        )

        ax.xaxis.set_major_locator(MultipleLocator(10))
        ax.xaxis.set_major_formatter(
            FuncFormatter(
                lambda valor, _: f"{valor:.0f}"
            )
        )

        ax.set_xlabel(
            "Variação da proporção urbana (pontos percentuais)",
            fontsize=10.5,
            color=self.cor_texto,
            labelpad=12,
        )

        self._aplicar_estilo_eixo(
            ax=ax,
            eixo_grade="x",
        )

        fig.text(
            0.50,
            0.075,
            (
                "A variação descreve uma mudança na composição censitária "
                "observada. Isoladamente, ela não comprova migração entre "
                "áreas rurais e urbanas."
            ),
            ha="center",
            va="center",
            fontsize=9.5,
            color=self.cor_escura,
            bbox={
                "boxstyle": "round,pad=0.70",
                "facecolor": self.cor_caixa_clara,
                "edgecolor": self.cor_urbano,
                "linewidth": 1.0,
                "alpha": 0.98,
            },
        )

        self._adicionar_cabecalho(
            fig=fig,
            titulo=(
                "A proporção urbana avançou 43,6 p.p. no Amazonas,\n"
                "mas recuou fortemente no Rio Grande do Norte e no Piauí"
            ),
            subtitulo=(
                "Mudança da participação urbana na população indígena "
                "de cada UF entre os Censos de 2010 e 2022"
            ),
        )

        self._adicionar_fonte(
            fig=fig,
            texto=(
                "Fonte: IBGE — Censos Demográficos de 2010 e 2022. "
                "Elaboração: Lucas Dias Noronha."
            ),
        )

        return self._finalizar_grafico(
            fig=fig,
            nome_arquivo=(
                "grafico_mudanca_urbanizacao_estadual_2010_2022.png"
            ),
            exibir=exibir,
        )
