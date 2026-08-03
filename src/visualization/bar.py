import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from matplotlib import ticker
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from pathlib import Path


class PlotBar:
    """
    Classe responsável pela criação dos gráficos de barras do projeto.

    A estrutura visual segue princípios de storytelling com dados:
    - título conclusivo;
    - subtítulo contextual;
    - destaque seletivo dos dados;
    - anotações ligadas aos elementos do gráfico;
    - caixa com síntese interpretativa;
    - fonte e autoria padronizadas.
    """

    def __init__(
        self,
        db,
        titulo="",
        rotulo_x="",
        rotulo_y="",
        cor=None,
        caminho_logo="../assets/IESB_Logo.png",
        pasta_figuras="../reports/figures",
    ):
        self.db = db
        self.titulo = titulo
        self.rotulo_x = rotulo_x
        self.rotulo_y = rotulo_y
        self.cor = cor or ["#C6D9F1", "#1B4965"]
        self.caminho_logo = caminho_logo
        self.pasta_figuras = Path(pasta_figuras)

        # A pasta será criada automaticamente caso ainda não exista.
        self.pasta_figuras.mkdir(parents=True, exist_ok=True)

        sns.set_theme(style="whitegrid")

        plt.rcParams.update(
            {
                "font.size": 12,
                "font.family": "DejaVu Sans",
                "axes.titlesize": 16,
                "axes.titleweight": "bold",
                "figure.facecolor": "white",
                "axes.facecolor": "white",
            }
        )

    # =======================================================
    # MÉTODOS AUXILIARES
    # =======================================================

    @staticmethod
    def _obter_linha_brasil(db):
        """
        Retorna a linha referente ao Brasil e interrompe a execução
        com uma mensagem clara caso ela não exista.
        """
        db_pais = db.loc[db["Localidade"] == "Brasil"]

        if db_pais.empty:
            raise ValueError(
                "Não foi encontrada uma linha com Localidade igual a 'Brasil'."
            )

        return db_pais.iloc[0]

    @staticmethod
    def _formatar_inteiro(valor):
        """
        Formata valores inteiros com separador de milhar no padrão brasileiro.
        """
        return f"{valor:,.0f}".replace(",", ".")

    @staticmethod
    def _formatar_percentual(valor, casas=1):
        """
        Formata percentuais com vírgula decimal.
        """
        return f"{valor:.{casas}f}".replace(".", ",")

    def _formatter_milhoes(self, x, pos=None):
        """
        Formata os valores do eixo em milhões ou milhares.
        """
        if abs(x) >= 1e6:
            return f"{x / 1e6:.1f}M".replace(".", ",")

        if abs(x) >= 1e3:
            return f"{x / 1e3:.0f} mil"

        return self._formatar_inteiro(x)

    def _aplicar_estilo_base(self, ax):
        """
        Aplica um padrão visual limpo e consistente.
        """
        sns.despine(ax=ax, top=True, right=True, left=True, bottom=False)

        ax.set_axisbelow(True)
        ax.xaxis.grid(True, linestyle="--", linewidth=0.8, alpha=0.30)
        ax.yaxis.grid(False)

        ax.tick_params(
            axis="x",
            length=0,
            labelcolor=self.cor[1],
            labelsize=10,
        )
        ax.tick_params(
            axis="y",
            length=0,
            labelcolor=self.cor[1],
            labelsize=11,
        )

        ax.xaxis.set_major_formatter(
            ticker.FuncFormatter(self._formatter_milhoes)
        )

    def _adicionar_titulo_subtitulo(
        self,
        ax,
        titulo,
        subtitulo,
        pad_titulo=42,
    ):
        """
        Adiciona título e subtítulo alinhados exatamente à esquerda
        do eixo do gráfico.

        O título comunica a descoberta principal.
        O subtítulo fornece contexto, período ou recorte analítico.
        """
        ax.set_title(
            titulo,
            loc="left",
            fontsize=16,
            fontweight="bold",
            color=self.cor[1],
            pad=pad_titulo,
            wrap=True,
        )

        ax.text(
            0,
            1.025,
            subtitulo,
            transform=ax.transAxes,
            ha="left",
            va="bottom",
            fontsize=10.5,
            color="#666666",
        )

    def _adicionar_anotacao(
        self,
        ax,
        texto,
        xy,
        xytext,
        cor=None,
        alinhamento="left",
    ):
        """
        Adiciona uma anotação ligada ao dado por uma seta.
        """
        cor = cor or self.cor[1]

        ax.annotate(
            texto,
            xy=xy,
            xytext=xytext,
            ha=alinhamento,
            va="center",
            fontsize=10,
            color=cor,
            arrowprops={
                "arrowstyle": "->",
                "color": cor,
                "linewidth": 1.2,
                "shrinkA": 5,
                "shrinkB": 5,
            },
            bbox={
                "boxstyle": "round,pad=0.45",
                "facecolor": "white",
                "edgecolor": cor,
                "linewidth": 0.9,
                "alpha": 0.97,
            },
        )

    def _adicionar_caixa_insight(
        self,
        ax,
        texto,
        x,
        y,
        cor_texto=None,
        cor_fundo=None,
        alinhamento="left",
        fontsize=9.5,
    ):
        """
        Adiciona uma caixa de síntese interpretativa.

        As coordenadas x e y são relativas ao eixo:
        0 representa o início e 1 representa o final.
        """
        cor_texto = cor_texto or self.cor[0]
        cor_fundo = cor_fundo or self.cor[1]

        ax.text(
            x,
            y,
            texto,
            transform=ax.transAxes,
            ha=alinhamento,
            va="top",
            fontsize=fontsize,
            color=cor_texto,
            bbox={
                "boxstyle": "round,pad=0.65",
                "facecolor": cor_fundo,
                "edgecolor": "none",
                "alpha": 0.97,
            },
        )

    def _adicionar_fonte(self, fig):
        """
        Adiciona fonte e autoria no rodapé da figura.
        """
        fig.text(
            0.02,
            0.015,
            "Fonte: IBGE — Censos Demográficos de 2010 e 2022. "
            "Elaboração: Lucas Dias Noronha.",
            ha="left",
            va="bottom",
            fontsize=9,
            color="#777777",
        )

    def _adicionar_logo(self, fig):
        """
        Adiciona o logotipo, caso o arquivo esteja disponível.
        """
        try:
            logo = plt.imread(self.caminho_logo)
            imagebox = OffsetImage(logo, zoom=0.30)

            ab = AnnotationBbox(
                imagebox,
                (0.98, 0.02),
                frameon=False,
                xycoords="figure fraction",
                box_alignment=(1, 0),
            )

            fig.add_artist(ab)

        except (FileNotFoundError, OSError):
            print(
                "Arquivo de logo não encontrado ou inválido. "
                "O gráfico será criado sem o logotipo."
            )

    def _finalizar_grafico(self, fig, nome_arquivo):
        """
        Padroniza margens, fonte, logotipo, salvamento e exibição.
        """
        self._adicionar_fonte(fig)
        self._adicionar_logo(fig)

        fig.subplots_adjust(
            left=0.13,
            right=0.94,
            top=0.79,
            bottom=0.14,
        )

        caminho_saida = self.pasta_figuras / nome_arquivo

        fig.savefig(
            caminho_saida,
            dpi=300,
            bbox_inches="tight",
            facecolor=fig.get_facecolor(),
        )

        plt.show()
        plt.close(fig)

    # =======================================================
    # GRÁFICO 1 — CRESCIMENTO NACIONAL
    # =======================================================

    def plot_crescimento_pais(self):
        brasil = self._obter_linha_brasil(self.db)

        valor_2010 = float(brasil["Indígenas 2010 Total"])
        valor_2022 = float(brasil["Indígenas 2022 Total"])

        diferenca = valor_2022 - valor_2010
        crescimento_pct = (diferenca / valor_2010) * 100

        anos = ["2010", "2022"]
        valores = [valor_2010, valor_2022]

        fig, ax = plt.subplots(figsize=(11, 6))

        # A cor mais forte destaca o período mais recente.
        barras = ax.barh(
            anos,
            valores,
            color=[self.cor[0], self.cor[1]],
            height=0.56,
        )

        # Rótulos internos nas barras.
        for indice, barra in enumerate(barras):
            largura = barra.get_width()

            cor_rotulo = self.cor[1] if indice == 0 else "white"

            ax.text(
                largura * 0.975,
                barra.get_y() + barra.get_height() / 2,
                self._formatar_inteiro(largura),
                ha="right",
                va="center",
                fontsize=12,
                fontweight="bold",
                color=cor_rotulo,
            )

        self._adicionar_titulo_subtitulo(
            ax,
            (
                "A população indígena registrada no Brasil "
                f"cresceu {self._formatar_percentual(crescimento_pct, 0)}%"
            ),
            (
                "Comparação do total de pessoas indígenas recenseadas "
                "em 2010 e 2022"
            ),
        )

        self._aplicar_estilo_base(ax)

        limite_direito = max(valores) * 1.38
        ax.set_xlim(0, limite_direito)

        # Anotação conectada à barra de 2022.
        self._adicionar_anotacao(
            ax=ax,
            texto=(
                    f"Em apenas 12 anos,\n"
                    f"o Brasil passou de\n"
                    f"897 mil para quase\n"
                    f"1,7 milhão de indígenas."
            ),
            xy=(valor_2022, 1),
            xytext=(valor_2022 * 1.08, 1.18),
        )

        texto_insight = (
            "O resultado evidencia que a população\n"
            "indígena registrada passou a ocupar\n"
            "um novo patamar demográfico no país."
        )

        self._adicionar_caixa_insight(
            ax=ax,
            texto=texto_insight,
            x=0.50,
            y=0.45,
            fontsize=8.5,

        )

        self._finalizar_grafico(
            fig,
            "grafico_crescimento_populacao_indigena_brasil.png",
        )

    # =======================================================
    # GRÁFICO 2 — ÁREA URBANA E RURAL
    # =======================================================

    def plot_crescimento_area(self):
        brasil = self._obter_linha_brasil(self.db)

        categorias = ["Urbana", "Rural"]

        valores_2010 = np.array(
            [
                float(brasil["Indígenas 2010 Urbano"]),
                float(brasil["Indígenas 2010 Rural"]),
            ]
        )

        valores_2022 = np.array(
            [
                float(brasil["Indígenas 2022 Urbano"]),
                float(brasil["Indígenas 2022 Rural"]),
            ]
        )

        diferencas = valores_2022 - valores_2010
        crescimentos_pct = (diferencas / valores_2010) * 100

        percentuais_2010 = np.array(
            [
                float(brasil["% Indígenas 2010 Urbano"]),
                float(brasil["% Indígenas 2010 Rural"]),
            ]
        )

        percentuais_2022 = np.array(
            [
                float(brasil["% Indígenas 2022 Urbano"]),
                float(brasil["% Indígenas 2022 Rural"]),
            ]
        )

        indice_maior_crescimento = int(np.argmax(crescimentos_pct))
        categoria_destaque = categorias[indice_maior_crescimento]

        fig, ax = plt.subplots(figsize=(12, 7))

        y_pos = np.arange(len(categorias))
        altura = 0.32
        intervalo = 0.025

        barras_2010 = ax.barh(
            y_pos - altura / 2 - intervalo,
            valores_2010,
            height=altura,
            color=self.cor[0],
            label="2010",
        )

        barras_2022 = ax.barh(
            y_pos + altura / 2 + intervalo,
            valores_2022,
            height=altura,
            color=self.cor[1],
            label="2022",
        )

        # Valores inseridos nas próprias barras.
        for indice, barra in enumerate(barras_2010):
            ax.text(
                barra.get_width() * 0.975,
                barra.get_y() + barra.get_height() / 2,
                self._formatar_inteiro(barra.get_width()),
                ha="right",
                va="center",
                fontsize=10.5,
                fontweight="bold",
                color=self.cor[1],
            )

        for barra in barras_2022:
            ax.text(
                barra.get_width() * 0.975,
                barra.get_y() + barra.get_height() / 2,
                self._formatar_inteiro(barra.get_width()),
                ha="right",
                va="center",
                fontsize=10.5,
                fontweight="bold",
                color="white",
            )

        ax.set_yticks(y_pos)
        ax.set_yticklabels(categorias)
        ax.invert_yaxis()

        self._adicionar_titulo_subtitulo(
            ax,
            (
                f"O crescimento foi mais intenso na população indígena "
                f"{categoria_destaque.lower()}"
            ),
            (
                "Comparação por situação do domicílio, com valores absolutos "
                "e participação relativa"
            ),
        )

        self._aplicar_estilo_base(ax)

        maior_valor = max(valores_2010.max(), valores_2022.max())
        ax.set_xlim(0, maior_valor * 1.45)

        ax.legend(
            frameon=False,
            loc="lower right",
            bbox_to_anchor=(0.98, 0.04),
            ncol=2,
        )

        # Anotação ligada à categoria com maior crescimento percentual.
        y_destaque = y_pos[indice_maior_crescimento] + altura / 2 + intervalo
        valor_destaque = valores_2022[indice_maior_crescimento]

        self._adicionar_anotacao(
            ax=ax,
            texto=(
                f"O maior crescimento ocorreu\n"
                f"na população {categoria_destaque.lower()},\n"
                f"com aumento de "
                f"{self._formatar_percentual(crescimentos_pct[indice_maior_crescimento])}%."
            ),
            xy=(valor_destaque, y_destaque),
            xytext=(maior_valor * 1.08, y_destaque + 0.30),
        )

        texto_insight = (
            "A participação da população\n"
            "indígena urbana passou a\n"
            "superar a rural, indicando\n"
            "uma importante mudança\n"
            "na distribuição da população."
        )

        self._adicionar_caixa_insight(
            ax=ax,
            texto=texto_insight,
            x=0.73,
            y=0.98,
        )

        self._finalizar_grafico(
            fig,
            "grafico_crescimento_pop_indigena_area.png",
        )

    # =======================================================
    # GRÁFICO 3 — DISTRIBUIÇÃO DETALHADA POR TI
    # =======================================================

    def plot_distribuicao_detalhada_ti(self):
        """
        Compara a população indígena em 2010 e 2022
        dentro e fora das Terras Indígenas, evidenciando
        a composição urbana e rural de cada contexto.
        """

        brasil = self._obter_linha_brasil(self.db)

        # =======================================================
        # DADOS
        # =======================================================

        # População dentro de Terras Indígenas.
        ti_rural = np.array(
            [
                float(brasil["Indígenas 2010 TI Rural"]),
                float(brasil["Indígenas 2022 TI Rural"]),
            ]
        )

        ti_urbana = np.array(
            [
                float(brasil["Indígenas 2010 TI Urbano"]),
                float(brasil["Indígenas 2022 TI Urbano"]),
            ]
        )

        # População fora de Terras Indígenas.
        fora_ti_rural = np.array(
            [
                float(brasil["Indígenas 2010 Fora TI Rural"]),
                float(brasil["Indígenas 2022 Fora TI Rural"]),
            ]
        )

        fora_ti_urbana = np.array(
            [
                float(brasil["Indígenas 2010 Fora TI Urbano"]),
                float(brasil["Indígenas 2022 Fora TI Urbano"]),
            ]
        )

        # Totais de cada contexto.
        total_ti = ti_rural + ti_urbana
        total_fora_ti = fora_ti_rural + fora_ti_urbana

        # Variações do total dentro e fora de TI.
        aumento_ti = total_ti[1] - total_ti[0]
        aumento_fora_ti = total_fora_ti[1] - total_fora_ti[0]

        crescimento_ti = (aumento_ti / total_ti[0]) * 100
        crescimento_fora_ti = (
            aumento_fora_ti / total_fora_ti[0]
        ) * 100

        # =======================================================
        # CONFIGURAÇÃO DO GRÁFICO
        # =======================================================

        fig, ax = plt.subplots(figsize=(13, 8))

        # Fora de TI ficará na parte superior.
        y_fora_ti = np.array([0, 1])

        # Em TI ficará na parte inferior.
        y_ti = np.array([3, 4])

        altura = 0.62

        # Mantemos as quatro tonalidades para preservar
        # a legenda existente.
        cor_rural_2010 = "#C6D9F1"
        cor_urbana_2010 = "#91B7D5"

        cor_rural_2022 = "#39708E"
        cor_urbana_2022 = "#1B4965"

        # =======================================================
        # BARRAS EMPILHADAS — FORA DE TI
        # =======================================================

        ax.barh(
            y_fora_ti[0],
            fora_ti_rural[0],
            height=altura,
            color=cor_rural_2010,
            edgecolor="white",
            linewidth=1,
            label="Rural — 2010",
        )

        ax.barh(
            y_fora_ti[0],
            fora_ti_urbana[0],
            left=fora_ti_rural[0],
            height=altura,
            color=cor_urbana_2010,
            edgecolor="white",
            linewidth=1,
            label="Urbana — 2010",
        )

        ax.barh(
            y_fora_ti[1],
            fora_ti_rural[1],
            height=altura,
            color=cor_rural_2022,
            edgecolor="white",
            linewidth=1,
            label="Rural — 2022",
        )

        ax.barh(
            y_fora_ti[1],
            fora_ti_urbana[1],
            left=fora_ti_rural[1],
            height=altura,
            color=cor_urbana_2022,
            edgecolor="white",
            linewidth=1,
            label="Urbana — 2022",
        )

        # =======================================================
        # BARRAS EMPILHADAS — EM TI
        # =======================================================

        ax.barh(
            y_ti[0],
            ti_rural[0],
            height=altura,
            color=cor_rural_2010,
            edgecolor="white",
            linewidth=1,
        )

        ax.barh(
            y_ti[0],
            ti_urbana[0],
            left=ti_rural[0],
            height=altura,
            color=cor_urbana_2010,
            edgecolor="white",
            linewidth=1,
        )

        ax.barh(
            y_ti[1],
            ti_rural[1],
            height=altura,
            color=cor_rural_2022,
            edgecolor="white",
            linewidth=1,
        )

        ax.barh(
            y_ti[1],
            ti_urbana[1],
            left=ti_rural[1],
            height=altura,
            color=cor_urbana_2022,
            edgecolor="white",
            linewidth=1,
        )

        # =======================================================
        # RÓTULOS INTERNOS — FORA DE TI
        # =======================================================

        # Fora de TI — 2010 — Rural.
        ax.text(
            fora_ti_rural[0] / 2,
            y_fora_ti[0],
            (
                "Rural\n"
                f"{self._formatar_inteiro(fora_ti_rural[0])}"
            ),
            ha="center",
            va="center",
            fontsize=8.3,
            fontweight="bold",
            color=self.cor[1],
        )

        # Fora de TI — 2010 — Urbana.
        ax.text(
            fora_ti_rural[0] + fora_ti_urbana[0] / 2,
            y_fora_ti[0],
            (
                "Urbana\n"
                f"{self._formatar_inteiro(fora_ti_urbana[0])}"
            ),
            ha="center",
            va="center",
            fontsize=9,
            fontweight="bold",
            color=self.cor[1],
        )

        # Fora de TI — 2022 — Rural.
        ax.text(
            fora_ti_rural[1] / 2,
            y_fora_ti[1],
            (
                "Rural\n"
                f"{self._formatar_inteiro(fora_ti_rural[1])}"
            ),
            ha="center",
            va="center",
            fontsize=9,
            fontweight="bold",
            color="white",
        )

        # Fora de TI — 2022 — Urbana.
        ax.text(
            fora_ti_rural[1] + fora_ti_urbana[1] / 2,
            y_fora_ti[1],
            (
                "Urbana\n"
                f"{self._formatar_inteiro(fora_ti_urbana[1])}"
            ),
            ha="center",
            va="center",
            fontsize=9,
            fontweight="bold",
            color="white",
        )

        # =======================================================
        # RÓTULOS — EM TI
        # =======================================================

        # Em TI — 2010 — Rural.
        ax.text(
            ti_rural[0] / 2,
            y_ti[0],
            (
                "Rural\n"
                f"{self._formatar_inteiro(ti_rural[0])}"
            ),
            ha="center",
            va="center",
            fontsize=9,
            fontweight="bold",
            color=self.cor[1],
        )

        # Em TI — 2022 — Rural.
        ax.text(
            ti_rural[1] / 2,
            y_ti[1],
            (
                "Rural\n"
                f"{self._formatar_inteiro(ti_rural[1])}"
            ),
            ha="center",
            va="center",
            fontsize=9,
            fontweight="bold",
            color="white",
        )

        maior_valor = max(
            total_ti.max(),
            total_fora_ti.max(),
        )

        deslocamento = maior_valor * 0.012

        # Os segmentos urbanos em TI são pequenos;
        # seus valores ficam fora das barras.

        ax.text(
            total_ti[0] + deslocamento,
            y_ti[0],
            (
                "Urbana: "
                f"{self._formatar_inteiro(ti_urbana[0])}"
            ),
            ha="left",
            va="center",
            fontsize=9,
            color="#6A7C88",
        )

        ax.text(
            total_ti[1] + deslocamento,
            y_ti[1],
            (
                "Urbana: "
                f"{self._formatar_inteiro(ti_urbana[1])}"
            ),
            ha="left",
            va="center",
            fontsize=9,
            fontweight="bold",
            color=self.cor[1],
        )

        # =======================================================
        # EIXO Y
        # =======================================================

        ax.set_yticks(
            [
                y_fora_ti[0],
                y_fora_ti[1],
                y_ti[0],
                y_ti[1],
            ]
        )

        ax.set_yticklabels(
            [
                "2010",
                "2022",
                "2010",
                "2022",
            ]
        )

        # A posição zero aparecerá no topo.
        ax.invert_yaxis()

        # =======================================================
        # NOMES DOS CONTEXTOS
        # =======================================================

        # Nome do primeiro contexto acima das barras.
        ax.text(
            0,
            -0.52,
            "FORA DAS TERRAS INDÍGENAS",
            ha="left",
            va="center",
            fontsize=10,
            fontweight="bold",
            color=self.cor[1],
        )

        # Nome do segundo contexto acima das barras.
        ax.text(
            0,
            2.48,
            "EM TERRAS INDÍGENAS",
            ha="left",
            va="center",
            fontsize=10,
            fontweight="bold",
            color=self.cor[1],
        )

        # Separação visual entre os dois contextos.
        ax.axhline(
            2,
            color="#D9D9D9",
            linewidth=0.9,
            linestyle="--",
        )

        # =======================================================
        # TÍTULO, SUBTÍTULO E ESTILO
        # =======================================================

        self._adicionar_titulo_subtitulo(
            ax,
            (
                "O crescimento da população indígena "
                "concentrou-se fora das Terras Indígenas"
            ),
            (
                "Comparação entre 2010 e 2022, com composição "
                "urbana e rural em cada contexto"
            ),
        )

        self._aplicar_estilo_base(ax)

        # Espaço à direita para anotação e insight.
        ax.set_xlim(
            0,
            maior_valor * 1.38,
        )

        # =======================================================
        # ANOTAÇÃO
        # =======================================================

        texto_anotacao = (
            "Fora das Terras Indígenas,\n"
            "o contingente aumento em\n"
            f"{self._formatar_inteiro(aumento_fora_ti)} pessoas\n"
            f"({self._formatar_percentual(crescimento_fora_ti)}%)."
        )

        self._adicionar_anotacao(
            ax=ax,
            texto=texto_anotacao,
            xy=(
                total_fora_ti[1],
                y_fora_ti[1],
            ),
            xytext=(
                maior_valor * 1.07,
                y_fora_ti[1] + 0.25,
            ),
        )

        # =======================================================
        # INSIGHT
        # =======================================================

        texto_insight = (
            "O crescimento concentrou-se\n"
            "fora das Terras Indígenas,\n"
            "onde as populações urbana\n"
            "e rural apresentaram as\n"
            "maiores expansões."
        )

        self._adicionar_caixa_insight(
            ax=ax,
            texto=texto_insight,
            x=0.71,
            y=0.48,
            fontsize=8.8,
        )

        # =======================================================
        # LEGENDA — MANTIDA NA REGIÃO INFERIOR DIREITA
        # =======================================================

        ax.legend(
            frameon=False,
            loc="lower right",
            bbox_to_anchor=(0.98, 0.01),
            ncol=2,
            columnspacing=1.5,
            handlelength=1.8,
        )

        # =======================================================
        # FINALIZAÇÃO
        # =======================================================

        self._finalizar_grafico(
            fig,
            "grafico_populacao_em_fora_ti_urbana_rural.png",
        )