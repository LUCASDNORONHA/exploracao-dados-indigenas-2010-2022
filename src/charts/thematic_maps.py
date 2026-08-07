from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.cm import ScalarMappable
from matplotlib.colors import LinearSegmentedColormap, Normalize, TwoSlopeNorm


class PlotMapas:
    """
    Constrói os mapas temáticos utilizados na análise espacial
    da população indígena brasileira.
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
        self.cor_borda = "#FFFFFF"
        self.cor_sem_dados = "#E0E0E0"

        self.mapa_cores = LinearSegmentedColormap.from_list(
            "azul_indigena",
            [
                self.cor_clara,
                self.cor_media,
                self.cor_escura,
            ],
        )

        # Escala divergente para variáveis com perdas e ganhos.
        self.mapa_divergente = LinearSegmentedColormap.from_list(
            "mudanca_participacao",
            [
                "#B5483A",
                "#F7F7F7",
                self.cor_escura,
            ],
        )

        self._validar_base()

    def _validar_base(self) -> None:
        """Verifica se a base possui os elementos necessários."""

        if not isinstance(self.gdf, gpd.GeoDataFrame):
            raise TypeError("O objeto informado deve ser um GeoDataFrame.")

        if "geometry" not in self.gdf.columns:
            raise ValueError("O GeoDataFrame não possui a coluna 'geometry'.")

        if self.gdf.empty:
            raise ValueError("O GeoDataFrame está vazio.")

        if self.gdf.crs is None:
            raise ValueError(
                "O GeoDataFrame não possui sistema de referência definido."
            )

    def _validar_coluna(
        self,
        coluna: str,
        gdf: gpd.GeoDataFrame | None = None,
    ) -> None:
        """Verifica se uma coluna existe na base informada."""

        base = self.gdf if gdf is None else gdf

        if coluna not in base.columns:
            raise KeyError(
                f"A coluna '{coluna}' não existe. "
                f"Colunas disponíveis: {base.columns.tolist()}"
            )

    @staticmethod
    def _formatar_inteiro(valor: float) -> str:
        """Formata valores inteiros segundo a notação brasileira."""

        return f"{valor:,.0f}".replace(",", ".")

    @staticmethod
    def _formatar_percentual(valor: float) -> str:
        """Formata percentuais segundo a notação brasileira."""

        return f"{valor:.1f}".replace(".", ",")

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

    def _adicionar_fonte(
        self,
        fig,
        texto: str,
    ) -> None:
        """Adiciona a fonte dos dados."""

        fig.text(
            0.06,
            0.045,
            texto,
            ha="left",
            va="center",
            fontsize=8.5,
            color=self.cor_secundaria,
        )

    def _adicionar_caixa_insight(
        self,
        ax,
        texto: str,
        x: float = 1.04,
        y: float = 0.58,
        fontsize: float = 9.2,
    ) -> None:
        """
        Adiciona uma caixa interpretativa ao lado do mapa.

        Os parâmetros x e y utilizam coordenadas relativas ao eixo.
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

    def _destacar_estado(
        self,
        ax,
        gdf: gpd.GeoDataFrame,
        estado: str,
        texto: str,
        coluna_estado: str = "NM_UF",
        xytext: tuple[float, float] = (1.04, 0.79),
        cor_borda: str | None = None,
        linewidth: float = 2.2,
        fontsize: float = 9.2,
    ) -> None:
        """Destaca uma Unidade da Federação e adiciona uma anotação."""

        self._validar_coluna(
            coluna=coluna_estado,
            gdf=gdf,
        )

        estado_selecionado = gdf.loc[gdf[coluna_estado].eq(estado)]

        if estado_selecionado.empty:
            raise ValueError(
                f"O estado '{estado}' não foi encontrado na coluna '{coluna_estado}'."
            )

        if len(estado_selecionado) > 1:
            raise ValueError(f"O estado '{estado}' possui mais de um registro.")

        cor_borda = cor_borda or self.cor_escura

        estado_selecionado.boundary.plot(
            ax=ax,
            color=cor_borda,
            linewidth=linewidth,
            zorder=7,
        )

        ponto = estado_selecionado.geometry.representative_point().iloc[0]

        ax.annotate(
            texto,
            xy=(ponto.x, ponto.y),
            xycoords="data",
            xytext=xytext,
            textcoords=ax.transAxes,
            ha="left",
            va="center",
            fontsize=fontsize,
            color=self.cor_escura,
            clip_on=False,
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

    def _adicionar_barra_cores(
        self,
        fig,
        gdf: gpd.GeoDataFrame,
        coluna: str,
        label: str,
        posicao: tuple[float, float, float, float] = (
            0.84,
            0.20,
            0.02,
            0.42,
        ),
        cmap=None,
        norm=None,
    ) -> None:
        """
        Adiciona uma barra de cores padronizada à figura.

        A posição segue:
        (esquerda, inferior, largura, altura).

        Quando ``cmap`` e ``norm`` não são informados, utiliza-se
        a escala sequencial padrão do projeto.
        """

        self._validar_coluna(
            coluna=coluna,
            gdf=gdf,
        )

        valores = gdf[coluna].dropna()

        if valores.empty:
            raise ValueError(f"A coluna '{coluna}' não possui valores válidos.")

        cmap = self.mapa_cores if cmap is None else cmap

        if norm is None:
            norm = Normalize(
                vmin=float(valores.min()),
                vmax=float(valores.max() * 1.05),
            )

        mapeamento = ScalarMappable(
            norm=norm,
            cmap=cmap,
        )

        mapeamento.set_array([])

        eixo_cores = fig.add_axes(posicao)

        barra = fig.colorbar(
            mapeamento,
            cax=eixo_cores,
        )

        barra.set_label(
            label,
            fontsize=9.5,
            color=self.cor_texto,
            labelpad=12,
        )

        barra.ax.tick_params(
            labelsize=8.5,
            colors=self.cor_texto,
        )

        barra.outline.set_linewidth(0.8)

    def _finalizar_mapa(
        self,
        fig,
        nome_arquivo: str,
    ) -> None:
        """Salva e exibe o mapa."""

        caminho_saida = self.diretorio_saida / nome_arquivo

        fig.savefig(
            caminho_saida,
            dpi=300,
            bbox_inches="tight",
            facecolor="white",
        )

        plt.show()

    def plot_populacao_indigena_2022(
        self,
        coluna: str = "Indígenas 2022 Total",
        coluna_estado: str = "NM_UF",
    ) -> None:
        """
        Constrói o mapa da distribuição absoluta da população
        indígena pelas Unidades da Federação em 2022.
        """

        self._validar_coluna(coluna)
        self._validar_coluna(coluna_estado)

        dados_validos = self.gdf.dropna(subset=[coluna, "geometry"]).copy()

        if dados_validos.empty:
            raise ValueError("Não existem registros válidos para construir o mapa.")

        fig, ax = plt.subplots(
            figsize=(13, 9),
        )

        fig.subplots_adjust(
            left=0.04,
            right=0.72,
            top=0.86,
            bottom=0.11,
        )

        dados_validos.plot(
            ax=ax,
            column=coluna,
            cmap=self.mapa_cores,
            edgecolor=self.cor_borda,
            linewidth=0.8,
            legend=False,
            missing_kwds={
                "color": self.cor_sem_dados,
                "edgecolor": self.cor_borda,
                "label": "Sem informação",
            },
        )

        self._adicionar_titulo_subtitulo(
            ax=ax,
            titulo=(
                "Poucos estados concentravam grande parte\n"
                "da população indígena brasileira em 2022"
            ),
            subtitulo=(
                "Distribuição absoluta da população indígena por Unidade da Federação"
            ),
        )

        ax.set_axis_off()

        indice_maior = dados_validos[coluna].idxmax()
        maior_registro = dados_validos.loc[indice_maior]

        estado_destaque = str(maior_registro[coluna_estado])

        valor_destaque = float(maior_registro[coluna])

        texto_anotacao = (
            f"{estado_destaque} concentrou\n"
            "o maior contingente\n"
            "indígena do país:\n"
            f"{self._formatar_inteiro(valor_destaque)} pessoas."
        )

        self._destacar_estado(
            ax=ax,
            gdf=dados_validos,
            estado=estado_destaque,
            texto=texto_anotacao,
            coluna_estado=coluna_estado,
            xytext=(0.75, 0.85),
            linewidth=2.3,
            fontsize=9.2,
        )

        texto_insight = (
            "Amazonas e Bahia concentram\n"
            "os maiores contingentes\n"
            "indígenas, enquanto a maior\n"
            "parte das Unidades da Federação\n"
            "apresenta populações\n"
            "significativamente menores."
        )

        self._adicionar_caixa_insight(
            ax=ax,
            texto=texto_insight,
            x=0.78,
            y=0.50,
            fontsize=9.2,
        )

        self._adicionar_barra_cores(
            fig=fig,
            gdf=dados_validos,
            coluna=coluna,
            label="Pessoas indígenas",
            posicao=(
                0.735,
                0.18,
                0.020,
                0.50,
            ),
        )

        self._adicionar_fonte(
            fig=fig,
            texto=(
                "Fonte: IBGE — Censo Demográfico 2022. Elaboração: Lucas Dias Noronha."
            ),
        )

        self._finalizar_mapa(
            fig=fig,
            nome_arquivo="mapa_populacao_indigena_2022.png",
        )

    def plot_crescimento_percentual(
        self,
        coluna_2010: str = "Indígenas 2010 Total",
        coluna_2022: str = "Indígenas 2022 Total",
        coluna_estado: str = "NM_UF",
    ) -> None:
        """
        Constrói o mapa do crescimento percentual da população
        indígena entre 2010 e 2022 por Unidade da Federação.
        """

        self._validar_coluna(coluna_2010)
        self._validar_coluna(coluna_2022)
        self._validar_coluna(coluna_estado)

        coluna_variacao = "Crescimento percentual"

        dados = self.gdf.copy()

        denominador = dados[coluna_2010]

        dados[coluna_variacao] = (
            (dados[coluna_2022] - dados[coluna_2010])
            .div(denominador.where(denominador.ne(0)))
            .mul(100)
        )

        dados_validos = dados.dropna(
            subset=[
                coluna_variacao,
                "geometry",
            ]
        ).copy()

        if dados_validos.empty:
            raise ValueError("Não existem registros válidos para construir o mapa.")

        fig, ax = plt.subplots(
            figsize=(13, 9),
        )

        fig.subplots_adjust(
            left=0.04,
            right=0.72,
            top=0.86,
            bottom=0.11,
        )

        dados_validos.plot(
            ax=ax,
            column=coluna_variacao,
            cmap=self.mapa_cores,
            edgecolor=self.cor_borda,
            linewidth=0.8,
            legend=False,
            missing_kwds={
                "color": self.cor_sem_dados,
                "edgecolor": self.cor_borda,
                "label": "Sem informação",
            },
        )

        self._adicionar_titulo_subtitulo(
            ax=ax,
            titulo=(
                "O crescimento percentual da população indígena\n"
                "foi liderado pelo Nordeste entre 2010 e 2022"
            ),
            subtitulo=(
                "Variação percentual da população indígena "
                "por Unidade da Federação — 2010 a 2022"
            ),
        )

        ax.set_axis_off()

        indice_maior = dados_validos[coluna_variacao].idxmax()
        maior_registro = dados_validos.loc[indice_maior]

        estado_destaque = str(maior_registro[coluna_estado])

        valor_destaque = float(maior_registro[coluna_variacao])

        texto_anotacao = (
            f"{estado_destaque} apresentou\n"
            "o maior crescimento\n"
            "percentual do país:\n"
            f"{self._formatar_percentual(valor_destaque)}%."
        )

        self._destacar_estado(
            ax=ax,
            gdf=dados_validos,
            estado=estado_destaque,
            texto=texto_anotacao,
            coluna_estado=coluna_estado,
            xytext=(0.75, 0.90),
            linewidth=2.3,
            fontsize=9.2,
        )

        ranking = dados_validos.nlargest(
            4,
            coluna_variacao,
        )

        estados_destaque = ranking[coluna_estado].tolist()

        texto_insight = (
            f"{estados_destaque[0]}, {estados_destaque[1]},\n"
            f"{estados_destaque[2]} e {estados_destaque[3]}\n"
            "lideraram o crescimento\n"
            "proporcional, evidenciando\n"
            "uma expansão especialmente\n"
            "intensa em estados nordestinos.\n"
            "Isso não significa, porém, que\n"
            "possuíam os maiores contingentes\n"
            "absolutos em 2022."
        )

        self._adicionar_caixa_insight(
            ax=ax,
            texto=texto_insight,
            x=0.78,
            y=0.50,
            fontsize=9.2,
        )

        self._adicionar_barra_cores(
            fig=fig,
            gdf=dados_validos,
            coluna=coluna_variacao,
            label="Crescimento entre 2010 e 2022 (%)",
            posicao=(
                0.735,
                0.18,
                0.020,
                0.50,
            ),
        )

        self._adicionar_fonte(
            fig=fig,
            texto=(
                "Fonte: IBGE — Censos Demográficos de 2010 e 2022. "
                "Elaboração: Lucas Dias Noronha."
            ),
        )

        self._finalizar_mapa(
            fig=fig,
            nome_arquivo="mapa_crescimento_percentual_2010_2022.png",
        )

    def plot_mudanca_participacao(
        self,
        coluna_2010: str = "Indígenas 2010 Total",
        coluna_2022: str = "Indígenas 2022 Total",
        coluna_estado: str = "NM_UF",
    ) -> None:
        """
        Constrói o mapa da mudança, em pontos percentuais,
        da participação de cada UF no total nacional da
        população indígena entre 2010 e 2022.
        """

        self._validar_coluna(coluna_2010)
        self._validar_coluna(coluna_2022)
        self._validar_coluna(coluna_estado)

        dados = self.gdf.copy()

        total_2010 = float(dados[coluna_2010].sum())
        total_2022 = float(dados[coluna_2022].sum())

        if total_2010 == 0 or total_2022 == 0:
            raise ValueError(
                "Os totais nacionais de 2010 e 2022 devem ser maiores que zero."
            )

        coluna_participacao_2010 = "Participação 2010 (%)"
        coluna_participacao_2022 = "Participação 2022 (%)"
        coluna_mudanca = "Mudança participação (p.p.)"

        dados[coluna_participacao_2010] = dados[coluna_2010].div(total_2010).mul(100)

        dados[coluna_participacao_2022] = dados[coluna_2022].div(total_2022).mul(100)

        dados[coluna_mudanca] = (
            dados[coluna_participacao_2022] - dados[coluna_participacao_2010]
        )

        dados_validos = dados.dropna(
            subset=[
                coluna_mudanca,
                "geometry",
            ]
        ).copy()

        if dados_validos.empty:
            raise ValueError("Não existem registros válidos para construir o mapa.")

        valores = dados_validos[coluna_mudanca]

        limite = max(
            abs(float(valores.min())),
            abs(float(valores.max())),
        )

        if limite == 0:
            raise ValueError(
                "Não houve mudança de participação entre os dois períodos."
            )

        normalizacao = TwoSlopeNorm(
            vmin=valores.min(),
            vcenter=0,
            vmax=valores.max(),
        )

        fig, ax = plt.subplots(
            figsize=(13, 9),
        )

        fig.subplots_adjust(
            left=0.04,
            right=0.72,
            top=0.86,
            bottom=0.11,
        )

        dados_validos.plot(
            ax=ax,
            column=coluna_mudanca,
            cmap=self.mapa_divergente,
            norm=normalizacao,
            edgecolor=self.cor_borda,
            linewidth=0.8,
            legend=False,
            missing_kwds={
                "color": self.cor_sem_dados,
                "edgecolor": self.cor_borda,
                "label": "Sem informação",
            },
        )

        self._adicionar_titulo_subtitulo(
            ax=ax,
            titulo=(
                "Amazonas e Bahia ampliaram sua participação\n"
                "na população indígena brasileira entre 2010 e 2022"
            ),
            subtitulo=(
                "Variação, em pontos percentuais, da participação de cada Unidade da Federação no total da população indígena brasileira."
            ),
        )

        ax.set_axis_off()

        indice_maior = dados_validos[coluna_mudanca].idxmax()
        maior_registro = dados_validos.loc[indice_maior]

        estado_destaque = str(maior_registro[coluna_estado])

        valor_destaque = float(maior_registro[coluna_mudanca])

        texto_anotacao = (
            f"{estado_destaque} ampliou sua\n"
            "participação nacional em\n"
            f"{self._formatar_percentual(valor_destaque)} "
            "pontos percentuais."
        )

        self._destacar_estado(
            ax=ax,
            gdf=dados_validos,
            estado=estado_destaque,
            texto=texto_anotacao,
            coluna_estado=coluna_estado,
            xytext=(0.62, 0.87),
            linewidth=2.3,
            fontsize=9.2,
        )

        maiores_ganhos = dados_validos.nlargest(
            2,
            coluna_mudanca,
        )

        maior_perda = dados_validos.nsmallest(
            1,
            coluna_mudanca,
        ).iloc[0]

        primeiro = str(maiores_ganhos.iloc[0][coluna_estado])

        segundo = str(maiores_ganhos.iloc[1][coluna_estado])

        estado_maior_perda = str(maior_perda[coluna_estado])

        valor_maior_perda = float(maior_perda[coluna_mudanca])

        texto_insight = (
            f"{primeiro} e {segundo} ampliaram\n"
            "significativamente sua participação\n"
            "na população indígena brasileira.\n"
            "Em sentido oposto, "
            f"{estado_maior_perda}\n"
            "apresentou a maior perda de\n"
            "participação relativa no periodo,\n"
            "de "
            f"{self._formatar_percentual(abs(valor_maior_perda))} pontos percentuais."
        )

        self._adicionar_caixa_insight(
            ax=ax,
            texto=texto_insight,
            x=0.78,
            y=0.50,
            fontsize=9.2,
        )

        self._adicionar_barra_cores(
            fig=fig,
            gdf=dados_validos,
            coluna=coluna_mudanca,
            label="Mudança na participação nacional (p.p.)",
            posicao=(
                0.740,
                0.18,
                0.020,
                0.50,
            ),
            cmap=self.mapa_divergente,
            norm=normalizacao,
        )

        self._adicionar_fonte(
            fig=fig,
            texto=(
                "Fonte: IBGE — Censos Demográficos de 2010 e 2022. "
                "Elaboração: Lucas Dias Noronha."
            ),
        )

        self._finalizar_mapa(
            fig=fig,
            nome_arquivo="mapa_mudanca_participacao_2010_2022.png",
        )

    def plot_distribuicao_regional(
        self,
        coluna: str = "Indígenas 2022 Total",
        coluna_regiao: str = "NM_REGIAO",
    ) -> None:
        """
        Constrói o mapa da distribuição regional da população
        indígena brasileira registrada no Censo de 2022.
        """

        self._validar_coluna(coluna)
        self._validar_coluna(coluna_regiao)

        dados_validos = self.gdf.dropna(
            subset=[
                coluna,
                coluna_regiao,
                "geometry",
            ]
        ).copy()

        if dados_validos.empty:
            raise ValueError(
                "Não existem registros válidos para construir o mapa regional."
            )

        regioes = dados_validos.dissolve(
            by=coluna_regiao,
            aggfunc={
                coluna: "sum",
            },
        ).reset_index()

        total_nacional = float(regioes[coluna].sum())

        if total_nacional <= 0:
            raise ValueError("O total nacional deve ser maior que zero.")

        coluna_participacao = "Participação regional (%)"

        regioes[coluna_participacao] = regioes[coluna].div(total_nacional).mul(100)

        fig, ax = plt.subplots(
            figsize=(13, 9),
        )

        fig.subplots_adjust(
            left=0.04,
            right=0.72,
            top=0.86,
            bottom=0.11,
        )

        regioes.plot(
            ax=ax,
            column=coluna_participacao,
            cmap=self.mapa_cores,
            edgecolor=self.cor_borda,
            linewidth=1.2,
            legend=False,
            missing_kwds={
                "color": self.cor_sem_dados,
                "edgecolor": self.cor_borda,
                "label": "Sem informação",
            },
        )

        self._adicionar_titulo_subtitulo(
            ax=ax,
            titulo=(
                "Norte e Nordeste concentram cerca de três quartos\n"
                "da população indígena brasileira em 2022"
            ),
            subtitulo=(
                "Participação de cada Grande Região no "
                "total da população indígena brasileira"
            ),
        )

        ax.set_axis_off()

        nomes_rotulos = {
            "Centro-Oeste": "CENTRO-\nOESTE",
            "Nordeste": "NORDESTE",
            "Norte": "NORTE",
            "Sudeste": "SUDESTE",
            "Sul": "SUL",
        }

        participacao_maxima = float(regioes[coluna_participacao].max())

        for _, linha in regioes.iterrows():
            regiao = str(linha[coluna_regiao])

            participacao = float(linha[coluna_participacao])

            ponto = linha.geometry.representative_point()

            cor_rotulo = (
                "white"
                if participacao >= participacao_maxima * 0.45
                else self.cor_escura
            )

            nome_rotulo = nomes_rotulos.get(
                regiao,
                regiao.upper(),
            )

            texto_rotulo = f"{nome_rotulo}\n{self._formatar_percentual(participacao)}%"

            ax.text(
                ponto.x,
                ponto.y,
                texto_rotulo,
                ha="center",
                va="center",
                fontsize=10.2,
                fontweight="bold",
                color=cor_rotulo,
                linespacing=1.15,
                zorder=8,
            )

        participacao_norte_nordeste = float(
            regioes.loc[
                regioes[coluna_regiao].isin(
                    [
                        "Norte",
                        "Nordeste",
                    ]
                ),
                coluna_participacao,
            ].sum()
        )

        texto_insight = (
            "Norte e Nordeste concentram\n"
            f"{self._formatar_percentual(participacao_norte_nordeste)}% "
            "da população indígena\n"
            "brasileira, evidenciando uma\n"
            "forte concentração regional."
        )

        self._adicionar_caixa_insight(
            ax=ax,
            texto=texto_insight,
            x=0.78,
            y=0.50,
            fontsize=9.2,
        )

        self._adicionar_barra_cores(
            fig=fig,
            gdf=regioes,
            coluna=coluna_participacao,
            label="Participação na população indígena brasileira (%)",
            posicao=(
                0.710,
                0.18,
                0.020,
                0.50,
            ),
        )

        self._adicionar_fonte(
            fig=fig,
            texto=(
                "Fonte: IBGE — Censo Demográfico 2022. Elaboração: Lucas Dias Noronha."
            ),
        )

        self._finalizar_mapa(
            fig=fig,
            nome_arquivo="mapa_distribuicao_regional_2022.png",
        )
