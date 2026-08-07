from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np


class PlotPerfilRegional:
    """
    Constrói os gráficos comparativos utilizados no estudo
    do perfil regional da população indígena brasileira.
    """

    def __init__(
        self,
        gdf: gpd.GeoDataFrame,
        diretorio_saida: str | Path,
    ) -> None:
        self.gdf = gdf.copy()
        self.diretorio_saida = Path(diretorio_saida)

        self.diretorio_saida.mkdir(
            parents=True,
            exist_ok=True,
        )

        # Paleta visual do projeto.
        self.cor_clara = "#DCEAF2"
        self.cor_media = "#39708E"
        self.cor_escura = "#173F5F"
        self.cor_texto = "#263238"
        self.cor_secundaria = "#607D8B"
        self.cor_grade = "#D9E1E5"
        self.cor_fundo = "#FFFFFF"

        self._validar_base()

    def _validar_base(self) -> None:
        """Verifica se a base regional possui estrutura válida."""

        if not isinstance(self.gdf, gpd.GeoDataFrame):
            raise TypeError("O objeto informado deve ser um GeoDataFrame.")

        if self.gdf.empty:
            raise ValueError("O GeoDataFrame regional está vazio.")

        if len(self.gdf) != 5:
            raise ValueError(
                "A base regional deve possuir cinco registros, "
                f"mas foram encontrados {len(self.gdf)}."
            )

        if "NM_REGIAO" not in self.gdf.columns:
            raise KeyError("A coluna 'NM_REGIAO' não existe na base regional.")

        quantidade_regioes = self.gdf["NM_REGIAO"].nunique()

        if quantidade_regioes != 5:
            raise ValueError(
                "A coluna 'NM_REGIAO' deve conter cinco Grandes Regiões distintas."
            )

    def _validar_coluna(
        self,
        coluna: str,
    ) -> None:
        """Verifica se uma coluna existe na base."""

        if coluna not in self.gdf.columns:
            raise KeyError(
                f"A coluna '{coluna}' não existe. "
                f"Colunas disponíveis: {self.gdf.columns.tolist()}"
            )

    @staticmethod
    def _formatar_inteiro(
        valor: float,
    ) -> str:
        """Formata valores inteiros segundo a notação brasileira."""

        return f"{valor:,.0f}".replace(",", ".")

    @staticmethod
    def _formatar_percentual(
        valor: float,
        casas_decimais: int = 1,
    ) -> str:
        """Formata percentuais segundo a notação brasileira."""

        return f"{valor:.{casas_decimais}f}".replace(".", ",")

    def _adicionar_titulo_subtitulo(
        self,
        ax,
        titulo: str,
        subtitulo: str,
    ) -> None:
        """Adiciona título e subtítulo alinhados à esquerda."""

        ax.set_title(
            titulo,
            fontsize=16,
            fontweight="bold",
            loc="left",
            pad=38,
            color=self.cor_texto,
        )

        ax.text(
            0,
            1.015,
            subtitulo,
            transform=ax.transAxes,
            ha="left",
            va="bottom",
            fontsize=10,
            color=self.cor_secundaria,
        )

    def _adicionar_caixa_insight(
        self,
        ax,
        texto: str,
        x: float = 0.69,
        y: float = 0.42,
        fontsize: float = 9.2,
    ) -> None:
        """
        Adiciona uma caixa interpretativa ao gráfico.

        Os valores de x e y utilizam coordenadas relativas ao eixo.
        """

        ax.text(
            x,
            y,
            texto,
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=fontsize,
            color="white",
            linespacing=1.35,
            clip_on=False,
            zorder=10,
            bbox={
                "boxstyle": "round,pad=0.70",
                "facecolor": self.cor_escura,
                "edgecolor": "none",
                "alpha": 0.97,
            },
        )

    def _adicionar_anotacao(
        self,
        ax,
        texto: str,
        xy: tuple[float, float],
        xytext: tuple[float, float],
        fontsize: float = 9.2,
    ) -> None:
        """Adiciona uma anotação com seta ao gráfico."""

        ax.annotate(
            texto,
            xy=xy,
            xycoords="data",
            xytext=xytext,
            textcoords="data",
            ha="left",
            va="center",
            fontsize=fontsize,
            color=self.cor_escura,
            zorder=10,
            bbox={
                "boxstyle": "round,pad=0.55",
                "facecolor": "white",
                "edgecolor": self.cor_escura,
                "linewidth": 1,
                "alpha": 0.98,
            },
            arrowprops={
                "arrowstyle": "->",
                "color": self.cor_escura,
                "linewidth": 1.3,
                "connectionstyle": "arc3,rad=0.06",
            },
        )

    def _adicionar_fonte(
        self,
        fig,
        texto: str,
    ) -> None:
        """Adiciona a fonte dos dados."""

        fig.text(
            0.07,
            0.045,
            texto,
            ha="left",
            va="center",
            fontsize=8.5,
            color=self.cor_secundaria,
        )

    def _aplicar_estilo_base(
        self,
        ax,
    ) -> None:
        """Aplica o estilo visual padronizado do projeto."""

        ax.set_facecolor(self.cor_fundo)

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)
        ax.spines["bottom"].set_visible(False)

        ax.tick_params(
            axis="both",
            length=0,
            labelcolor=self.cor_texto,
        )

        ax.grid(
            axis="x",
            linestyle="--",
            linewidth=0.6,
            alpha=0.30,
            color=self.cor_grade,
        )

        ax.set_axisbelow(True)

    def _finalizar_grafico(
        self,
        fig,
        nome_arquivo: str,
    ) -> None:
        """Salva e exibe o gráfico."""

        caminho_saida = self.diretorio_saida / nome_arquivo

        fig.savefig(
            caminho_saida,
            dpi=300,
            bbox_inches="tight",
            facecolor=self.cor_fundo,
        )

        plt.show()

    def plot_crescimento_regional(
        self,
        coluna_2010: str = "Indígenas 2010 Total",
        coluna_2022: str = "Indígenas 2022 Total",
        coluna_regiao: str = "NM_REGIAO",
    ) -> None:
        """
        Constrói o gráfico do crescimento percentual da
        população indígena por Grande Região entre 2010 e 2022.
        """

        self._validar_coluna(coluna_2010)

        self._validar_coluna(coluna_2022)

        self._validar_coluna(coluna_regiao)

        dados = self.gdf[
            [
                coluna_regiao,
                coluna_2010,
                coluna_2022,
            ]
        ].copy()

        denominador = dados[coluna_2010]

        dados["Crescimento (%)"] = (
            (dados[coluna_2022] - dados[coluna_2010])
            .div(denominador.where(denominador.ne(0)))
            .mul(100)
        )

        dados = (
            dados.dropna(
                subset=[
                    "Crescimento (%)",
                ]
            )
            .sort_values(
                "Crescimento (%)",
                ascending=True,
            )
            .reset_index(drop=True)
        )

        if dados.empty:
            raise ValueError("Não existem registros válidos para construir o gráfico.")

        indice_maior = int(dados["Crescimento (%)"].idxmax())

        regiao_destaque = str(
            dados.loc[
                indice_maior,
                coluna_regiao,
            ]
        )

        valor_destaque = float(
            dados.loc[
                indice_maior,
                "Crescimento (%)",
            ]
        )

        cores_barras = [
            (self.cor_escura if indice == indice_maior else self.cor_media)
            for indice in dados.index
        ]

        fig, ax = plt.subplots(
            figsize=(
                13,
                8,
            ),
        )

        fig.subplots_adjust(
            left=0.12,
            right=0.95,
            top=0.83,
            bottom=0.12,
        )

        y_pos = np.arange(len(dados))

        barras = ax.barh(
            y_pos,
            dados["Crescimento (%)"],
            color=cores_barras,
            height=0.58,
        )

        ax.set_yticks(y_pos)

        ax.set_yticklabels(
            dados[coluna_regiao],
            fontsize=10,
        )

        maior_valor = float(dados["Crescimento (%)"].max())

        deslocamento_rotulo = maior_valor * 0.025

        for indice, barra in enumerate(barras):
            valor = float(
                dados.loc[
                    indice,
                    "Crescimento (%)",
                ]
            )

            ax.text(
                barra.get_width() + deslocamento_rotulo,
                barra.get_y() + barra.get_height() / 2,
                f"{self._formatar_percentual(valor)}%",
                ha="left",
                va="center",
                fontsize=10,
                fontweight=("bold" if indice == indice_maior else "normal"),
                color=(
                    self.cor_escura if indice == indice_maior else self.cor_secundaria
                ),
            )

        self._adicionar_titulo_subtitulo(
            ax=ax,
            titulo=(
                "O crescimento da população indígena foi mais intenso\n"
                "no Nordeste entre 2010 e 2022"
            ),
            subtitulo=(
                "Crescimento percentual da população indígena por Grande Região"
            ),
        )

        self._aplicar_estilo_base(
            ax=ax,
        )

        ax.set_xlabel("")
        ax.set_xticks([])
        ax.set_xlim(
            0,
            maior_valor * 1.48,
        )

        y_destaque = float(y_pos[indice_maior])

        self._adicionar_anotacao(
            ax=ax,
            texto=(
                f"{regiao_destaque} apresentou\n"
                "o maior crescimento\n"
                "regional no período."
            ),
            xy=(
                valor_destaque,
                y_destaque,
            ),
            xytext=(
                maior_valor * 1.07,
                y_destaque - 0.7,
            ),
            fontsize=11.2,
        )

        ranking = dados.sort_values(
            "Crescimento (%)",
            ascending=False,
        ).reset_index(drop=True)

        primeira_regiao = str(
            ranking.loc[
                0,
                coluna_regiao,
            ]
        )

        segunda_regiao = str(
            ranking.loc[
                1,
                coluna_regiao,
            ]
        )

        float(
            ranking.loc[
                0,
                "Crescimento (%)",
            ]
        )

        float(
            ranking.loc[
                1,
                "Crescimento (%)",
            ]
        )

        texto_insight = (
            f"{primeira_regiao} e {segunda_regiao} lideraram o\n"
            "crescimento da população indígena.\n"
            "Nas demais regiões, a expansão ocorreu\n"
            "em ritmo significativamente menor,\n"
            "evidenciando que, embora o Norte reúna\n"
            "o maior contingente indígena do país,\n"
            "o crescimento proporcional mais intenso\n"
            "foi registrado no Nordeste."
        )

        self._adicionar_caixa_insight(
            ax=ax,
            texto=texto_insight,
            x=0.250,
            y=0.40,
            fontsize=13.0,
        )

        self._adicionar_fonte(
            fig=fig,
            texto=(
                "Fonte: IBGE — Censos Demográficos de 2010 e 2022. "
                "Elaboração: Lucas Dias Noronha."
            ),
        )

        self._finalizar_grafico(
            fig=fig,
            nome_arquivo=("grafico_crescimento_regional_2010_2022.png"),
        )

    def plot_urbanizacao_regional(
        self,
        coluna_urbano: str = "Indígenas 2022 Urbano",
        coluna_total: str = "Indígenas 2022 Total",
        coluna_regiao: str = "NM_REGIAO",
    ) -> None:
        """
        Constrói o gráfico da proporção da população indígena
        residente em áreas urbanas por Grande Região em 2022.
        """

        self._validar_coluna(coluna_urbano)
        self._validar_coluna(coluna_total)
        self._validar_coluna(coluna_regiao)

        dados = self.gdf[
            [
                coluna_regiao,
                coluna_urbano,
                coluna_total,
            ]
        ].copy()

        denominador = dados[coluna_total]

        dados["Percentual Urbano"] = (
            dados[coluna_urbano].div(denominador.where(denominador.ne(0))).mul(100)
        )

        dados = (
            dados.dropna(
                subset=[
                    "Percentual Urbano",
                ]
            )
            .sort_values(
                "Percentual Urbano",
                ascending=True,
            )
            .reset_index(drop=True)
        )

        if dados.empty:
            raise ValueError("Não existem registros válidos para construir o gráfico.")

        indice_maior = int(dados["Percentual Urbano"].idxmax())

        regiao_destaque = str(
            dados.loc[
                indice_maior,
                coluna_regiao,
            ]
        )

        valor_destaque = float(
            dados.loc[
                indice_maior,
                "Percentual Urbano",
            ]
        )

        cores_barras = [
            (self.cor_escura if indice == indice_maior else self.cor_media)
            for indice in dados.index
        ]

        fig, ax = plt.subplots(
            figsize=(13, 8),
        )

        fig.subplots_adjust(
            left=0.12,
            right=0.95,
            top=0.83,
            bottom=0.08,
        )

        y_pos = np.arange(len(dados))

        barras = ax.barh(
            y_pos,
            dados["Percentual Urbano"],
            color=cores_barras,
            height=0.58,
        )

        ax.set_yticks(y_pos)

        ax.set_yticklabels(
            dados[coluna_regiao],
            fontsize=10,
        )

        maior_valor = float(dados["Percentual Urbano"].max())

        deslocamento_rotulo = maior_valor * 0.025

        for indice, barra in enumerate(barras):
            valor = float(
                dados.loc[
                    indice,
                    "Percentual Urbano",
                ]
            )

            ax.text(
                barra.get_width() + deslocamento_rotulo,
                barra.get_y() + barra.get_height() / 2,
                f"{self._formatar_percentual(valor)}%",
                ha="left",
                va="center",
                fontsize=10,
                fontweight=("bold" if indice == indice_maior else "normal"),
                color=(
                    self.cor_escura if indice == indice_maior else self.cor_secundaria
                ),
            )

        self._adicionar_titulo_subtitulo(
            ax=ax,
            titulo=("O Sudeste possui a população indígena mais urbanizada do país"),
            subtitulo=(
                "Distribuição da população indígena residente em Terras Indígenas entre áreas urbanas e rurais — 2022"
            ),
        )

        self._aplicar_estilo_base(
            ax=ax,
        )

        ax.set_xlabel("")
        ax.set_xticks([])
        ax.tick_params(
            axis="x",
            bottom=False,
            labelbottom=False,
        )

        ax.set_xlim(
            0,
            maior_valor * 1.48,
        )

        for indice, label in enumerate(ax.get_yticklabels()):
            if indice == indice_maior:
                label.set_fontweight("bold")

        y_destaque = float(y_pos[indice_maior])

        self._adicionar_anotacao(
            ax=ax,
            texto=(
                f"{regiao_destaque} apresentou\n"
                "a maior taxa de\n"
                "urbanização da\n"
                "população indígena."
            ),
            xy=(
                valor_destaque,
                y_destaque,
            ),
            xytext=(
                maior_valor * 1.0,
                y_destaque - 0.80,
            ),
            fontsize=10.2,
        )

        ranking = dados.sort_values(
            "Percentual Urbano",
            ascending=False,
        ).reset_index(drop=True)

        str(ranking.iloc[-1][coluna_regiao])

        float(ranking.iloc[-1]["Percentual Urbano"])

        float(
            dados.loc[
                dados[coluna_regiao].eq("Norte"),
                "Percentual Urbano",
            ].iloc[0]
        )

        texto_insight = (
            "O Sudeste apresentou a maior proporção\n"
            "de população indígena residente em\n"
            "áreas urbanas, enquanto o Centro-Oeste\n"
            "registrou o menor percentual. No Norte,\n"
            "a população indígena mostrou uma\n"
            "distribuição praticamente equilibrada\n"
            "entre áreas urbanas e rurais."
        )

        self._adicionar_caixa_insight(
            ax=ax,
            texto=texto_insight,
            x=0.50,
            y=0.39,
            fontsize=12.0,
        )

        self._adicionar_fonte(
            fig=fig,
            texto=(
                "Fonte: IBGE — Censo Demográfico 2022. Elaboração: Lucas Dias Noronha."
            ),
        )

        self._finalizar_grafico(
            fig=fig,
            nome_arquivo=("grafico_urbanizacao_regional_2022.png"),
        )

    def plot_urbanizacao_terras_indigenas(
        self,
        coluna_ti_urbano: str = "Indígenas 2022 TI Urbano",
        coluna_ti_rural: str = "Indígenas 2022 TI Rural",
        coluna_ti_total: str = "Indígenas 2022 TI Total",
        coluna_regiao: str = "NM_REGIAO",
    ) -> None:
        """
        Constrói um gráfico de barras horizontais empilhadas a 100%,
        comparando a população indígena urbana e rural residente em
        Terras Indígenas por Grande Região em 2022.
        """

        self._validar_coluna(coluna_ti_urbano)
        self._validar_coluna(coluna_ti_rural)
        self._validar_coluna(coluna_ti_total)
        self._validar_coluna(coluna_regiao)

        dados = self.gdf[
            [
                coluna_regiao,
                coluna_ti_urbano,
                coluna_ti_rural,
                coluna_ti_total,
            ]
        ].copy()

        denominador = dados[coluna_ti_total]

        dados["Percentual TI Urbano"] = (
            dados[coluna_ti_urbano].div(denominador.where(denominador.ne(0))).mul(100)
        )

        dados["Percentual TI Rural"] = (
            dados[coluna_ti_rural].div(denominador.where(denominador.ne(0))).mul(100)
        )

        dados = (
            dados.dropna(
                subset=[
                    "Percentual TI Urbano",
                    "Percentual TI Rural",
                ]
            )
            .sort_values(
                "Percentual TI Urbano",
                ascending=False,
            )
            .reset_index(drop=True)
        )

        if dados.empty:
            raise ValueError("Não existem registros válidos para construir o gráfico.")

        soma_percentuais = dados["Percentual TI Urbano"] + dados["Percentual TI Rural"]

        if not np.allclose(
            soma_percentuais,
            100,
            atol=0.01,
        ):
            raise ValueError(
                "Os percentuais urbano e rural não totalizam 100% em todas as regiões."
            )

        fig, ax = plt.subplots(
            figsize=(13, 8),
        )

        # Reserva espaço à direita para a caixa de insight.
        fig.subplots_adjust(
            left=0.13,
            right=0.73,
            top=0.82,
            bottom=0.09,
        )

        y_pos = np.arange(len(dados))

        ax.barh(
            y_pos,
            dados["Percentual TI Urbano"],
            color="#8FB7CF",
            height=0.48,
            label="Urbano",
        )

        barras_rurais = ax.barh(
            y_pos,
            dados["Percentual TI Rural"],
            left=dados["Percentual TI Urbano"],
            color=self.cor_escura,
            height=0.48,
            label="Rural",
        )

        ax.set_yticks(y_pos)

        ax.set_yticklabels(
            dados[coluna_regiao],
            fontsize=10,
        )

        # A primeira observação da tabela deve aparecer no topo.
        ax.invert_yaxis()

        # Exibe apenas os percentuais rurais, pois eles representam
        # a principal descoberta comunicada pelo gráfico.
        for indice, barra_rural in enumerate(barras_rurais):
            percentual_urbano = float(
                dados.loc[
                    indice,
                    "Percentual TI Urbano",
                ]
            )

            percentual_rural = float(
                dados.loc[
                    indice,
                    "Percentual TI Rural",
                ]
            )

            posicao_rotulo = percentual_urbano + percentual_rural / 2

            ax.text(
                posicao_rotulo,
                barra_rural.get_y() + barra_rural.get_height() / 2,
                f"{self._formatar_percentual(percentual_rural)}%",
                ha="center",
                va="center",
                fontsize=10.0,
                fontweight="bold",
                color="white",
                zorder=5,
            )

        self._adicionar_titulo_subtitulo(
            ax=ax,
            titulo=(
                "A população indígena residente em Terras Indígenas\n"
                "permanece predominantemente rural em todas as regiões"
            ),
            subtitulo=(
                "Distribuição da população indígena residente em Terras Indígenas entre áreas urbanas e rurais — Censo Demográfico 2022"
            ),
        )

        self._aplicar_estilo_base(
            ax=ax,
        )

        ax.set_xlim(
            0,
            100,
        )

        ax.set_xlabel("")
        ax.set_xticks([])

        ax.tick_params(
            axis="x",
            bottom=False,
            labelbottom=False,
        )

        ax.legend(
            loc="upper left",
            bbox_to_anchor=(1.20, 1.0),
            frameon=False,
            ncol=2,
            fontsize=10.2,
            handlelength=1.8,
            columnspacing=1.5,
        )

        indice_maior_urbano = int(dados["Percentual TI Urbano"].idxmax())

        str(
            dados.loc[
                indice_maior_urbano,
                coluna_regiao,
            ]
        )

        float(
            dados.loc[
                indice_maior_urbano,
                "Percentual TI Urbano",
            ]
        )

        indice_maior_rural = int(dados["Percentual TI Rural"].idxmax())

        str(
            dados.loc[
                indice_maior_rural,
                coluna_regiao,
            ]
        )

        float(
            dados.loc[
                indice_maior_rural,
                "Percentual TI Rural",
            ]
        )

        texto_insight_01 = (
            "Em todas as Grandes Regiões predominou\n"
            "a população indigena residente em\n"
            "áreas rurais dentro das Terras Indigenas.\n"
            "O Nordeste apresentou a maior participação\n"
            "urbana,enquanto o Centro-Oeste o perfil\n"
            "mais rural."
        )

        texto_insight_02 = (
            "Maior participação urbana\n"
            "\n"
            "Nordeste\n"
            "23,3% da população em TI"
            "\n"
            "────────────────────────"
            "\n"
            "Maior participação rural\n"
            "\n"
            "Centro-Oeste\n"
            "98,4% da população em TI"
        )

        self._adicionar_caixa_insight(
            ax=ax,
            texto=texto_insight_01,
            x=1.04,
            y=0.86,
            fontsize=10.0,
        )

        self._adicionar_caixa_insight(
            ax=ax,
            texto=texto_insight_02,
            x=1.10,
            y=0.50,
            fontsize=12.5,
        )

        self._adicionar_fonte(
            fig=fig,
            texto=(
                "Fonte: IBGE — Censo Demográfico 2022. Elaboração: Lucas Dias Noronha."
            ),
        )

        self._finalizar_grafico(
            fig=fig,
            nome_arquivo=("grafico_urbano_rural_terras_indigenas_2022.png"),
        )

    def plot_urbanizacao_fora_terras_indigenas(
        self,
        coluna_fora_ti_urbano: str = "Indígenas 2022 Fora TI Urbano",
        coluna_fora_ti_rural: str = "Indígenas 2022 Fora TI Rural",
        coluna_fora_ti_total: str = "Indígenas 2022 Fora TI Total",
        coluna_regiao: str = "NM_REGIAO",
    ) -> None:
        """
        Constrói um gráfico de barras horizontais empilhadas a 100%,
        comparando a população indígena urbana e rural residente
        fora das Terras Indígenas por Grande Região em 2022.
        """

        self._validar_coluna(coluna_fora_ti_urbano)
        self._validar_coluna(coluna_fora_ti_rural)
        self._validar_coluna(coluna_fora_ti_total)
        self._validar_coluna(coluna_regiao)

        dados = self.gdf[
            [
                coluna_regiao,
                coluna_fora_ti_urbano,
                coluna_fora_ti_rural,
                coluna_fora_ti_total,
            ]
        ].copy()

        denominador = dados[coluna_fora_ti_total]

        dados["Percentual Fora TI Urbano"] = (
            dados[coluna_fora_ti_urbano]
            .div(denominador.where(denominador.ne(0)))
            .mul(100)
        )

        dados["Percentual Fora TI Rural"] = (
            dados[coluna_fora_ti_rural]
            .div(denominador.where(denominador.ne(0)))
            .mul(100)
        )

        dados = (
            dados.dropna(
                subset=[
                    "Percentual Fora TI Urbano",
                    "Percentual Fora TI Rural",
                ]
            )
            .sort_values(
                "Percentual Fora TI Urbano",
                ascending=False,
            )
            .reset_index(drop=True)
        )

        if dados.empty:
            raise ValueError("Não existem registros válidos para construir o gráfico.")

        soma_percentuais = (
            dados["Percentual Fora TI Urbano"] + dados["Percentual Fora TI Rural"]
        )

        if not np.allclose(
            soma_percentuais,
            100,
            atol=0.01,
        ):
            raise ValueError(
                "Os percentuais urbano e rural não totalizam 100% em todas as regiões."
            )

        fig, ax = plt.subplots(
            figsize=(13, 8),
        )

        fig.subplots_adjust(
            left=0.13,
            right=0.73,
            top=0.82,
            bottom=0.09,
        )

        y_pos = np.arange(len(dados))

        barras_urbanas = ax.barh(
            y_pos,
            dados["Percentual Fora TI Urbano"],
            color="#8FB7CF",
            height=0.48,
            label="Urbano",
        )

        ax.barh(
            y_pos,
            dados["Percentual Fora TI Rural"],
            left=dados["Percentual Fora TI Urbano"],
            color=self.cor_escura,
            height=0.48,
            label="Rural",
        )

        ax.set_yticks(y_pos)

        ax.set_yticklabels(
            dados[coluna_regiao],
            fontsize=10,
        )

        ax.invert_yaxis()

        # Exibe apenas os percentuais urbanos.
        for indice, barra_urbana in enumerate(barras_urbanas):
            percentual_urbano = float(
                dados.loc[
                    indice,
                    "Percentual Fora TI Urbano",
                ]
            )

            ax.text(
                percentual_urbano / 2,
                barra_urbana.get_y() + barra_urbana.get_height() / 2,
                f"{self._formatar_percentual(percentual_urbano)}%",
                ha="center",
                va="center",
                fontsize=10.0,
                fontweight="bold",
                color=self.cor_escura,
                zorder=5,
            )

        self._adicionar_titulo_subtitulo(
            ax=ax,
            titulo=(
                "A população indígena residente fora de Terras Indígenas\n"
                "é predominantemente urbana em todas as regiões"
            ),
            subtitulo=(
                "Distribuição da população indígena residente fora de Terras Indígenas "
                "entre áreas urbanas e rurais — Censo Demográfico 2022"
            ),
        )

        self._aplicar_estilo_base(
            ax=ax,
        )

        ax.set_xlim(
            0,
            100,
        )

        ax.set_xlabel("")
        ax.set_xticks([])

        ax.tick_params(
            axis="x",
            bottom=False,
            labelbottom=False,
        )

        ax.legend(
            loc="upper left",
            bbox_to_anchor=(1.20, 1.0),
            frameon=False,
            ncol=2,
            fontsize=10.2,
            handlelength=1.8,
            columnspacing=1.5,
        )

        indice_maior_urbano = int(dados["Percentual Fora TI Urbano"].idxmax())

        regiao_maior_urbano = str(
            dados.loc[
                indice_maior_urbano,
                coluna_regiao,
            ]
        )

        valor_maior_urbano = float(
            dados.loc[
                indice_maior_urbano,
                "Percentual Fora TI Urbano",
            ]
        )

        indice_maior_rural = int(dados["Percentual Fora TI Rural"].idxmax())

        regiao_maior_rural = str(
            dados.loc[
                indice_maior_rural,
                coluna_regiao,
            ]
        )

        valor_maior_rural = float(
            dados.loc[
                indice_maior_rural,
                "Percentual Fora TI Rural",
            ]
        )

        texto_insight_01 = (
            "Em todas as Grandes Regiões predominou\n"
            "a população indígena residente em\n"
            "áreas urbanas fora das Terras Indígenas.\n"
            "O Sudeste concentrou a maior participação\n"
            "urbana, enquanto o Sul apresentou\n"
            "a maior participação rural."
        )

        texto_insight_02 = (
            "Maior proporção urbana\n"
            "\n"
            f"{regiao_maior_urbano}\n"
            f"{self._formatar_percentual(valor_maior_urbano)}% da população fora de TI"
            "\n"
            "────────────────────────"
            "\n"
            "Maior proporção rural\n"
            "\n"
            f"{regiao_maior_rural}\n"
            f"{self._formatar_percentual(valor_maior_rural)}% da população fora de TI"
        )

        self._adicionar_caixa_insight(
            ax=ax,
            texto=texto_insight_01,
            x=1.04,
            y=0.86,
            fontsize=10.0,
        )

        self._adicionar_caixa_insight(
            ax=ax,
            texto=texto_insight_02,
            x=1.08,
            y=0.50,
            fontsize=12.5,
        )

        self._adicionar_fonte(
            fig=fig,
            texto=(
                "Fonte: IBGE — Censo Demográfico 2022. Elaboração: Lucas Dias Noronha."
            ),
        )

        self._finalizar_grafico(
            fig=fig,
            nome_arquivo=("grafico_urbano_rural_fora_terras_indigenas_2022.png"),
        )
