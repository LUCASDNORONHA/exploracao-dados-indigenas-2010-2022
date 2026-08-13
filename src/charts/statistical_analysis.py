"""Visualizações do Estudo 6 — Análise Estatística."""

from pathlib import Path
from typing import ClassVar

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter, PercentFormatter

from analysis.statistical_analysis import (
    CRITERIOS_ACEITACAO_AGRUPAMENTOS,
    VARIAVEIS_MULTIVARIADAS,
    avaliar_agrupamentos_multivariados,
    calcular_correlacoes_spearman,
    calcular_curva_lorenz,
    calcular_estabilidade_ranking_populacional,
    calcular_influencia_correlacoes_leave_one_out,
    calcular_influencia_leave_one_out,
    calcular_medidas_concentracao,
    calcular_pca_multivariada,
    calcular_resumo_distribuicoes,
    detectar_valores_atipicos,
    resumir_estabilidade_ranking,
    validar_base_estatistica,
)


class PlotAnaliseEstatistica:
    """Constrói as visualizações estatísticas das 27 UFs."""

    CORES_REGIOES: ClassVar[dict[str, str]] = {
        "Norte": "#173F5F",
        "Nordeste": "#2D5A80",
        "Centro-Oeste": "#39708E",
        "Sudeste": "#5E8EAA",
        "Sul": "#8FB7CF",
    }

    CONFIGURACAO_DISTRIBUICOES: ClassVar[list[dict[str, str | bool]]] = [
        {
            "coluna": "Indígenas 2022 Total",
            "titulo": "População indígena em 2022",
            "unidade": "Pessoas — escala logarítmica",
            "formato": "inteiro",
            "escala_log": True,
            "linha_zero": False,
        },
        {
            "coluna": "Crescimento relativo (%)",
            "titulo": "Crescimento relativo",
            "unidade": "Variação entre 2010 e 2022 (%)",
            "formato": "percentual",
            "escala_log": False,
            "linha_zero": True,
        },
        {
            "coluna": "Urbanização 2022 (%)",
            "titulo": "Urbanização em 2022",
            "unidade": "Parcela urbana da população indígena (%)",
            "formato": "percentual",
            "escala_log": False,
            "linha_zero": False,
        },
        {
            "coluna": "Mudança na urbanização (p.p.)",
            "titulo": "Mudança da urbanização",
            "unidade": "Diferença entre 2010 e 2022 (p.p.)",
            "formato": "pontos_percentuais",
            "escala_log": False,
            "linha_zero": True,
        },
        {
            "coluna": "Presença em TI 2022 (%)",
            "titulo": "Presença em Terras Indígenas",
            "unidade": "Parcela residente em TI em 2022 (%)",
            "formato": "percentual",
            "escala_log": False,
            "linha_zero": False,
        },
        {
            "coluna": "Mudança na presença em TI (p.p.)",
            "titulo": "Mudança da presença em TI",
            "unidade": "Diferença entre 2010 e 2022 (p.p.)",
            "formato": "pontos_percentuais",
            "escala_log": False,
            "linha_zero": True,
        },
    ]

    CONFIGURACAO_RELACOES: ClassVar[list[dict[str, str | bool]]] = [
        {
            "relacao": "Magnitude populacional × urbanização em 2022",
            "variavel_x": "Indígenas 2022 Total",
            "variavel_y": "Urbanização 2022 (%)",
            "titulo": "Magnitude populacional × urbanização",
            "rotulo_x": "População indígena em 2022 — escala logarítmica",
            "rotulo_y": "Urbanização em 2022 (%)",
            "escala_log_x": True,
        },
        {
            "relacao": "Crescimento × mudança da urbanização",
            "variavel_x": "Crescimento relativo (%)",
            "variavel_y": "Mudança na urbanização (p.p.)",
            "titulo": "Crescimento × mudança da urbanização",
            "rotulo_x": "Crescimento populacional entre os censos (%)",
            "rotulo_y": "Mudança da urbanização (p.p.)",
            "escala_log_x": False,
        },
        {
            "relacao": "Crescimento × mudança da presença em TI",
            "variavel_x": "Crescimento relativo (%)",
            "variavel_y": "Mudança na presença em TI (p.p.)",
            "titulo": "Crescimento × mudança da presença em TI",
            "rotulo_x": "Crescimento populacional entre os censos (%)",
            "rotulo_y": "Mudança da presença em TI (p.p.)",
            "escala_log_x": False,
        },
        {
            "relacao": "Urbanização × presença em TI em 2022",
            "variavel_x": "Urbanização 2022 (%)",
            "variavel_y": "Presença em TI 2022 (%)",
            "titulo": "Urbanização × presença em TI",
            "rotulo_x": "Urbanização em 2022 (%)",
            "rotulo_y": "Presença em TI em 2022 (%)",
            "escala_log_x": False,
        },
    ]

    def __init__(
        self,
        df: pd.DataFrame,
        diretorio_saida: str | Path,
    ) -> None:
        self.df = df.copy()
        self.diretorio_saida = Path(diretorio_saida)

        self.cor_clara = "#DCEAF2"
        self.cor_media = "#39708E"
        self.cor_escura = "#173F5F"
        self.cor_texto = "#263238"
        self.cor_secundaria = "#607D8B"
        self.cor_grade = "#D9E1E5"
        self.cor_fundo = "#FFFFFF"
        self.cor_destaque = "#2D5A80"

        validar_base_estatistica(self.df)

    @staticmethod
    def _formatar_inteiro(valor: float) -> str:
        return f"{valor:,.0f}".replace(",", ".")

    @classmethod
    def _formatar_valor(cls, valor: float, formato: str) -> str:
        if formato == "inteiro":
            return cls._formatar_inteiro(valor)
        if formato == "percentual":
            return f"{valor:.1f}%".replace(".", ",")
        if formato == "pontos_percentuais":
            return f"{valor:.1f} p.p.".replace(".", ",")
        raise ValueError(f"Formato desconhecido: {formato}")

    @staticmethod
    def _formatar_eixo_populacao(valor: float, _posicao: float) -> str:
        if valor >= 1_000_000:
            return f"{valor / 1_000_000:.0f} mi"
        if valor >= 1_000:
            return f"{valor / 1_000:.0f} mil"
        return f"{valor:.0f}"

    @staticmethod
    def _formatar_eixo_pp(valor: float, _posicao: float) -> str:
        return f"{valor:.0f} p.p."

    def _adicionar_cabecalho(
        self,
        fig,
        titulo: str,
        subtitulo: str,
        y_titulo: float = 0.975,
        y_subtitulo: float = 0.925,
    ) -> None:
        fig.text(
            0.06,
            y_titulo,
            titulo,
            ha="left",
            va="top",
            fontsize=22,
            fontweight="bold",
            color=self.cor_texto,
        )
        fig.text(
            0.06,
            y_subtitulo,
            subtitulo,
            ha="left",
            va="top",
            fontsize=11.5,
            color=self.cor_secundaria,
            linespacing=1.35,
        )

    def _aplicar_estilo_eixo(self, ax, eixo_grade: str = "x") -> None:
        ax.set_facecolor(self.cor_fundo)
        for lado in ("top", "right", "left", "bottom"):
            ax.spines[lado].set_visible(False)
        ax.tick_params(axis="both", length=0, labelcolor=self.cor_texto)
        ax.grid(
            axis=eixo_grade,
            linestyle="--",
            linewidth=0.7,
            alpha=0.55,
            color=self.cor_grade,
        )
        ax.set_axisbelow(True)

    def _adicionar_fonte(self, fig, y: float = 0.018) -> None:
        fig.text(
            0.06,
            y,
            "Fonte: IBGE — Censos Demográficos de 2010 e 2022. Elaboração própria.",
            ha="left",
            va="bottom",
            fontsize=8.5,
            color=self.cor_secundaria,
        )

    def _finalizar_grafico(
        self,
        fig,
        nome_arquivo: str,
        exibir: bool,
    ) -> Path:
        self.diretorio_saida.mkdir(parents=True, exist_ok=True)
        caminho = self.diretorio_saida / nome_arquivo
        fig.savefig(
            caminho,
            dpi=300,
            bbox_inches="tight",
            facecolor=self.cor_fundo,
        )
        if exibir:
            plt.show()
        plt.close(fig)
        return caminho

    def plot_distribuicoes_estaduais(self, exibir: bool = True) -> Path:
        """Mostra a distribuição dos seis indicadores centrais do estudo."""

        indicadores = [
            str(configuracao["coluna"])
            for configuracao in self.CONFIGURACAO_DISTRIBUICOES
        ]
        resumo = calcular_resumo_distribuicoes(
            self.df,
            indicadores=indicadores,
        ).set_index("Indicador")

        fig, eixos = plt.subplots(3, 2, figsize=(15.5, 14.5))
        fig.subplots_adjust(
            left=0.07,
            right=0.97,
            top=0.82,
            bottom=0.10,
            wspace=0.22,
            hspace=0.68,
        )

        self._adicionar_cabecalho(
            fig,
            (
                "A magnitude populacional é muito mais assimétrica que os "
                "indicadores de composição"
            ),
            (
                "Cada ponto representa uma UF; as caixas mostram Q1, mediana e "
                "Q3. A população utiliza escala logarítmica para que as 27 "
                "unidades permaneçam visíveis."
            ),
        )

        for indice, (ax, configuracao) in enumerate(
            zip(eixos.flat, self.CONFIGURACAO_DISTRIBUICOES, strict=True)
        ):
            coluna = str(configuracao["coluna"])
            formato = str(configuracao["formato"])
            valores = self.df[coluna].astype(float)
            estatisticas = resumo.loc[coluna]

            boxplot = ax.boxplot(
                valores,
                positions=[1.0],
                widths=0.22,
                orientation="horizontal",
                patch_artist=True,
                showfliers=False,
                whis=1.5,
                medianprops={
                    "color": self.cor_escura,
                    "linewidth": 2.1,
                },
                boxprops={
                    "facecolor": self.cor_clara,
                    "edgecolor": self.cor_media,
                    "linewidth": 1.2,
                },
                whiskerprops={
                    "color": self.cor_media,
                    "linewidth": 1.1,
                },
                capprops={
                    "color": self.cor_media,
                    "linewidth": 1.1,
                },
            )
            for elemento in boxplot["boxes"]:
                elemento.set_alpha(0.70)

            gerador = np.random.default_rng(20260812 + indice)
            posicoes_y = 1.0 + gerador.uniform(-0.115, 0.115, len(self.df))
            cores = self.df["Região"].map(self.CORES_REGIOES)

            ax.scatter(
                valores,
                posicoes_y,
                s=48,
                c=cores,
                alpha=0.90,
                edgecolors=self.cor_fundo,
                linewidths=0.7,
                zorder=3,
            )

            if bool(configuracao["linha_zero"]):
                ax.axvline(
                    0,
                    color=self.cor_secundaria,
                    linestyle=":",
                    linewidth=1.1,
                    zorder=0,
                )

            if bool(configuracao["escala_log"]):
                ax.set_xscale("log")
                ax.xaxis.set_major_formatter(
                    FuncFormatter(self._formatar_eixo_populacao)
                )
            elif formato == "percentual":
                ax.xaxis.set_major_formatter(PercentFormatter(xmax=100, decimals=0))
            else:
                ax.xaxis.set_major_formatter(FuncFormatter(self._formatar_eixo_pp))

            mediana = self._formatar_valor(float(estatisticas["Mediana"]), formato)
            iqr = self._formatar_valor(float(estatisticas["IQR"]), formato)

            ax.set_title(
                str(configuracao["titulo"]),
                loc="left",
                fontsize=13.5,
                fontweight="bold",
                color=self.cor_texto,
                pad=17,
            )
            ax.set_xlabel(
                str(configuracao["unidade"]),
                fontsize=9.5,
                color=self.cor_secundaria,
                labelpad=9,
            )
            ax.text(
                0.99,
                1.05,
                f"Mediana: {mediana}  |  IQR: {iqr}",
                transform=ax.transAxes,
                ha="right",
                va="bottom",
                fontsize=9.2,
                color=self.cor_secundaria,
            )
            ax.set_yticks([])
            ax.set_ylim(0.72, 1.28)
            ax.margins(x=0.08)
            self._aplicar_estilo_eixo(ax)

        itens_legenda = [
            Line2D(
                [0],
                [0],
                marker="o",
                color="none",
                markerfacecolor=cor,
                markeredgecolor=self.cor_fundo,
                markersize=8,
                label=regiao,
            )
            for regiao, cor in self.CORES_REGIOES.items()
        ]
        fig.legend(
            handles=itens_legenda,
            loc="lower center",
            bbox_to_anchor=(0.52, 0.045),
            ncol=5,
            frameon=False,
            fontsize=9.5,
        )
        self._adicionar_fonte(fig)

        return self._finalizar_grafico(
            fig,
            "grafico_distribuicoes_estatisticas_estaduais.png",
            exibir,
        )

    def plot_concentracao_estadual(self, exibir: bool = True) -> Path:
        """Combina a acumulação por ranking e a curva de Lorenz de 2022."""

        coluna = "Indígenas 2022 Total"
        medidas = calcular_medidas_concentracao(self.df, coluna=coluna).iloc[0]
        curva = calcular_curva_lorenz(self.df[coluna])
        ranking = self.df[["Localidade", coluna]].sort_values(
            coluna,
            ascending=False,
        )
        ranking["Participação acumulada"] = (
            ranking[coluna].cumsum().div(ranking[coluna].sum())
        )

        cr3 = float(medidas["CR3 (%)"])
        cr5 = float(medidas["CR5 (%)"])
        gini = float(medidas["Gini"])
        hhi = float(medidas["HHI"])
        numero_efetivo = float(medidas["Número efetivo de UFs"])
        texto_cr3 = f"{cr3:.1f}".replace(".", ",")
        texto_cr5 = f"{cr5:.1f}".replace(".", ",")
        texto_gini = f"{gini:.3f}".replace(".", ",")
        texto_hhi = f"{hhi:.3f}".replace(".", ",")
        texto_numero_efetivo = f"{numero_efetivo:.1f}".replace(".", ",")

        fig, (ax_acumulacao, ax_lorenz) = plt.subplots(
            1,
            2,
            figsize=(16, 8.8),
            gridspec_kw={"width_ratios": [1.12, 1.0]},
        )
        fig.subplots_adjust(
            left=0.07,
            right=0.96,
            top=0.77,
            bottom=0.20,
            wspace=0.27,
        )

        self._adicionar_cabecalho(
            fig,
            "Três UFs concentram quase metade da população indígena brasileira",
            (
                "Em 2022, as três maiores participações somavam "
                f"{texto_cr3}% e as cinco maiores, {texto_cr5}%. A curva de Lorenz "
                "quantifica a desigualdade da distribuição entre as 27 UFs."
            ),
            y_subtitulo=0.91,
        )

        posicoes = np.arange(1, len(ranking) + 1)
        acumulado = ranking["Participação acumulada"].to_numpy()

        ax_acumulacao.plot(
            posicoes,
            acumulado,
            color=self.cor_escura,
            linewidth=2.5,
            marker="o",
            markersize=4.5,
            markerfacecolor=self.cor_media,
            markeredgecolor=self.cor_fundo,
        )
        ax_acumulacao.fill_between(
            posicoes,
            0,
            acumulado,
            color=self.cor_clara,
            alpha=0.65,
        )
        ax_acumulacao.axhline(
            0.50,
            color=self.cor_secundaria,
            linestyle="--",
            linewidth=1.0,
        )

        for quantidade, valor, rotulo in (
            (3, cr3 / 100, f"CR3 = {texto_cr3}%"),
            (5, cr5 / 100, f"CR5 = {texto_cr5}%"),
        ):
            ax_acumulacao.scatter(
                quantidade,
                valor,
                s=85,
                color=self.cor_destaque,
                edgecolor=self.cor_fundo,
                linewidth=1.0,
                zorder=5,
            )
            ax_acumulacao.annotate(
                rotulo,
                xy=(quantidade, valor),
                xytext=(quantidade + 1.5, valor - 0.11),
                fontsize=10,
                fontweight="bold",
                color=self.cor_texto,
                arrowprops={
                    "arrowstyle": "-",
                    "color": self.cor_secundaria,
                    "linewidth": 0.9,
                },
            )

        tres_maiores = ", ".join(ranking["Localidade"].head(3))
        ax_acumulacao.text(
            0.04,
            0.13,
            f"Três maiores participações\n{tres_maiores}",
            transform=ax_acumulacao.transAxes,
            ha="left",
            va="bottom",
            fontsize=9.5,
            color=self.cor_texto,
            linespacing=1.35,
            bbox={
                "boxstyle": "round,pad=0.55",
                "facecolor": self.cor_clara,
                "edgecolor": "none",
                "alpha": 0.90,
            },
        )
        ax_acumulacao.set_title(
            "Acumulação pelas maiores UFs",
            loc="left",
            fontsize=13.5,
            fontweight="bold",
            color=self.cor_texto,
            pad=16,
        )
        ax_acumulacao.set_xlabel(
            "Quantidade de UFs, da maior para a menor população",
            fontsize=9.5,
            color=self.cor_secundaria,
            labelpad=10,
        )
        ax_acumulacao.set_ylabel(
            "Participação acumulada",
            fontsize=9.5,
            color=self.cor_secundaria,
            labelpad=10,
        )
        ax_acumulacao.set_xlim(1, 27)
        ax_acumulacao.set_ylim(0, 1.03)
        ax_acumulacao.set_xticks([1, 3, 5, 10, 15, 20, 27])
        ax_acumulacao.yaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
        self._aplicar_estilo_eixo(ax_acumulacao, eixo_grade="y")

        eixo_ufs = curva["Proporção acumulada de UFs"].to_numpy()
        eixo_populacao = curva["Proporção acumulada da população"].to_numpy()

        ax_lorenz.plot(
            [0, 1],
            [0, 1],
            color=self.cor_secundaria,
            linestyle="--",
            linewidth=1.2,
            label="Igualdade perfeita",
        )
        ax_lorenz.plot(
            eixo_ufs,
            eixo_populacao,
            color=self.cor_escura,
            linewidth=2.8,
            label="Distribuição observada",
        )
        ax_lorenz.fill_between(
            eixo_ufs,
            eixo_populacao,
            eixo_ufs,
            color=self.cor_clara,
            alpha=0.75,
        )
        ax_lorenz.text(
            0.06,
            0.78,
            (
                f"Gini: {texto_gini}\n"
                f"HHI: {texto_hhi}\n"
                f"Número efetivo: {texto_numero_efetivo} UFs"
            ),
            transform=ax_lorenz.transAxes,
            ha="left",
            va="top",
            fontsize=11,
            fontweight="bold",
            color=self.cor_texto,
            linespacing=1.45,
            bbox={
                "boxstyle": "round,pad=0.65",
                "facecolor": self.cor_fundo,
                "edgecolor": self.cor_clara,
                "linewidth": 1.0,
                "alpha": 0.95,
            },
        )
        ax_lorenz.set_title(
            "Curva de Lorenz",
            loc="left",
            fontsize=13.5,
            fontweight="bold",
            color=self.cor_texto,
            pad=16,
        )
        ax_lorenz.set_xlabel(
            "Proporção acumulada de UFs",
            fontsize=9.5,
            color=self.cor_secundaria,
            labelpad=10,
        )
        ax_lorenz.set_ylabel(
            "Proporção acumulada da população",
            fontsize=9.5,
            color=self.cor_secundaria,
            labelpad=10,
        )
        ax_lorenz.set_xlim(0, 1)
        ax_lorenz.set_ylim(0, 1)
        ax_lorenz.set_aspect("equal", adjustable="box")
        ax_lorenz.xaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
        ax_lorenz.yaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
        ax_lorenz.legend(
            loc="lower right",
            frameon=False,
            fontsize=9,
        )
        self._aplicar_estilo_eixo(ax_lorenz, eixo_grade="both")

        fig.text(
            0.06,
            0.085,
            (
                "Leitura: embora existam 27 UFs, o HHI corresponde a apenas "
                f"{texto_numero_efetivo} unidades de mesmo tamanho populacional."
            ),
            ha="left",
            va="bottom",
            fontsize=10,
            color=self.cor_texto,
            fontweight="bold",
        )
        self._adicionar_fonte(fig)

        return self._finalizar_grafico(
            fig,
            "grafico_concentracao_estadual_2022.png",
            exibir,
        )

    def plot_valores_atipicos_estaduais(self, exibir: bool = True) -> Path:
        """Compara as sinalizações de Tukey e do escore robusto mediana/MAD."""

        indicadores = [
            str(configuracao["coluna"])
            for configuracao in self.CONFIGURACAO_DISTRIBUICOES
        ]
        diagnostico = detectar_valores_atipicos(
            self.df,
            indicadores=indicadores,
        )
        total_ufs_sinalizadas = diagnostico.loc[
            diagnostico["Sinalizada"], "Localidade"
        ].nunique()

        fig, eixos = plt.subplots(3, 2, figsize=(15.5, 15.2))
        fig.subplots_adjust(
            left=0.07,
            right=0.97,
            top=0.80,
            bottom=0.15,
            wspace=0.22,
            hspace=0.72,
        )

        self._adicionar_cabecalho(
            fig,
            (
                f"Os critérios robustos sinalizam {total_ufs_sinalizadas} UFs "
                "em ao menos um indicador"
            ),
            (
                "Tukey utiliza 1,5 IQR e o escore robusto usa mediana/MAD com "
                "limite de ±3,5. Sinalização descreve atipicidade: não comprova "
                "erro e não determina exclusão."
            ),
        )

        marcadores = {
            "Não sinalizada": "o",
            "Ambos os critérios": "D",
            "Somente Tukey": "s",
            "Somente MAD": "^",
        }

        for indice, (ax, configuracao) in enumerate(
            zip(eixos.flat, self.CONFIGURACAO_DISTRIBUICOES, strict=True)
        ):
            indicador = str(configuracao["coluna"])
            grupo = diagnostico.loc[diagnostico["Indicador"].eq(indicador)].copy()
            mad = float(grupo["MAD"].iloc[0])
            mediana = float(grupo["Mediana"].iloc[0])
            constante = 0.6744897501960817
            if mad > 0:
                limite_tukey_inferior = (
                    constante
                    * (float(grupo["Limite inferior de Tukey"].iloc[0]) - mediana)
                    / mad
                )
                limite_tukey_superior = (
                    constante
                    * (float(grupo["Limite superior de Tukey"].iloc[0]) - mediana)
                    / mad
                )
            else:
                limite_tukey_inferior = float("nan")
                limite_tukey_superior = float("nan")

            gerador = np.random.default_rng(20260813 + indice)
            grupo["Posição vertical"] = 1.0 + gerador.uniform(
                -0.14,
                0.14,
                len(grupo),
            )

            for concordancia, marcador in marcadores.items():
                subconjunto = grupo.loc[grupo["Concordância"].eq(concordancia)]
                if subconjunto.empty:
                    continue
                sinalizada = concordancia != "Não sinalizada"
                ax.scatter(
                    subconjunto["Escore robusto"],
                    subconjunto["Posição vertical"],
                    s=80 if sinalizada else 45,
                    c=subconjunto["Região"].map(self.CORES_REGIOES),
                    marker=marcador,
                    alpha=0.98 if sinalizada else 0.62,
                    edgecolors=self.cor_texto if sinalizada else self.cor_fundo,
                    linewidths=1.0 if sinalizada else 0.6,
                    zorder=4 if sinalizada else 3,
                )

            limite_mad = float(grupo["Limite do escore robusto"].iloc[0])
            for limite in (-limite_mad, limite_mad):
                ax.axvline(
                    limite,
                    color=self.cor_secundaria,
                    linestyle="--",
                    linewidth=1.15,
                    zorder=1,
                )
            for limite in (limite_tukey_inferior, limite_tukey_superior):
                if np.isfinite(limite):
                    ax.axvline(
                        limite,
                        color=self.cor_media,
                        linestyle=":",
                        linewidth=1.25,
                        zorder=1,
                    )
            ax.axvline(
                0,
                color=self.cor_grade,
                linewidth=0.9,
                zorder=0,
            )

            sinalizadas = grupo.loc[grupo["Sinalizada"]].sort_values("Escore robusto")
            for ordem_rotulo, (_, linha) in enumerate(sinalizadas.iterrows()):
                deslocamento_y = 13 if ordem_rotulo % 2 == 0 else -17
                ax.annotate(
                    linha["Localidade"],
                    xy=(linha["Escore robusto"], linha["Posição vertical"]),
                    xytext=(4, deslocamento_y),
                    textcoords="offset points",
                    ha="left",
                    va="center",
                    fontsize=7.7,
                    fontweight="bold",
                    color=self.cor_texto,
                    arrowprops={
                        "arrowstyle": "-",
                        "color": self.cor_grade,
                        "linewidth": 0.7,
                    },
                )

            quantidade_tukey = int(grupo["Sinalizada por Tukey"].sum())
            quantidade_mad = int(grupo["Sinalizada por MAD"].sum())
            quantidade_uniao = int(grupo["Sinalizada"].sum())
            ax.text(
                0.99,
                1.05,
                (
                    f"Tukey: {quantidade_tukey}  |  MAD: {quantidade_mad}  |  "
                    f"União: {quantidade_uniao}"
                ),
                transform=ax.transAxes,
                ha="right",
                va="bottom",
                fontsize=9.1,
                color=self.cor_secundaria,
            )
            ax.set_title(
                str(configuracao["titulo"]),
                loc="left",
                fontsize=13.5,
                fontweight="bold",
                color=self.cor_texto,
                pad=17,
            )
            ax.set_xlabel(
                "Escore robusto em relação à mediana",
                fontsize=9.5,
                color=self.cor_secundaria,
                labelpad=9,
            )
            ax.set_yticks([])
            ax.set_ylim(0.68, 1.32)
            valores_e_limites = grupo["Escore robusto"].dropna().tolist() + [
                -limite_mad,
                limite_mad,
                limite_tukey_inferior,
                limite_tukey_superior,
            ]
            valores_finitos = np.asarray(valores_e_limites, dtype=float)
            valores_finitos = valores_finitos[np.isfinite(valores_finitos)]
            minimo, maximo = valores_finitos.min(), valores_finitos.max()
            margem = max(0.8, 0.10 * (maximo - minimo))
            ax.set_xlim(minimo - margem, maximo + margem)
            self._aplicar_estilo_eixo(ax)

        itens_regiao = [
            Line2D(
                [0],
                [0],
                marker="o",
                color="none",
                markerfacecolor=cor,
                markersize=7.5,
                label=regiao,
            )
            for regiao, cor in self.CORES_REGIOES.items()
        ]
        itens_criterio = [
            Line2D(
                [0],
                [0],
                marker=marcador,
                color="none",
                markerfacecolor=self.cor_clara,
                markeredgecolor=self.cor_texto,
                markersize=7.5,
                label=rotulo,
            )
            for rotulo, marcador in marcadores.items()
        ]
        fig.legend(
            handles=itens_regiao + itens_criterio,
            loc="lower center",
            bbox_to_anchor=(0.52, 0.055),
            ncol=5,
            frameon=False,
            fontsize=8.8,
            columnspacing=1.4,
        )
        fig.text(
            0.06,
            0.098,
            (
                "Linhas pontilhadas: limites de Tukey convertidos à escala do "
                "escore. Linhas tracejadas: limite mediana/MAD."
            ),
            ha="left",
            va="bottom",
            fontsize=9,
            color=self.cor_secundaria,
        )
        self._adicionar_fonte(fig)

        return self._finalizar_grafico(
            fig,
            "grafico_valores_atipicos_estaduais.png",
            exibir,
        )

    def plot_influencia_estadual(self, exibir: bool = True) -> Path:
        """Exibe a sensibilidade das medidas à retirada hipotética de cada UF."""

        influencia = calcular_influencia_leave_one_out(self.df)
        colunas_variacao = [
            "Variação da média (%)",
            "Variação da mediana (%)",
            "Variação do Gini (%)",
            "Variação do HHI (%)",
            "Variação do CR3 (%)",
        ]
        rotulos_colunas = ["Média", "Mediana", "Gini", "HHI", "CR3"]
        matriz = influencia[colunas_variacao].to_numpy(dtype=float)
        maior_valor = float(np.nanmax(np.abs(matriz)))
        uf_maior_influencia = str(influencia.loc[0, "UF retirada hipoteticamente"])
        valor_maior_influencia = float(
            influencia.loc[0, "Variação máxima absoluta (%)"]
        )
        texto_maior_influencia = f"{valor_maior_influencia:.1f}".replace(".", ",")

        mapa_cores = LinearSegmentedColormap.from_list(
            "influencia_panorama",
            ["#B84A62", self.cor_fundo, self.cor_escura],
        )
        normalizacao = TwoSlopeNorm(
            vmin=-maior_valor,
            vcenter=0.0,
            vmax=maior_valor,
        )

        fig, ax = plt.subplots(figsize=(13.5, 13.0))
        fig.subplots_adjust(
            left=0.24,
            right=0.89,
            top=0.81,
            bottom=0.12,
        )
        self._adicionar_cabecalho(
            fig,
            f"{uf_maior_influencia} é a UF de maior influência sobre as medidas de 2022",
            (
                "A retirada unitária hipotética altera uma das cinco medidas em até "
                f"{texto_maior_influencia}%. As células mostram a variação relativa "
                "frente à base completa; nenhuma observação foi removida da análise."
            ),
        )

        imagem = ax.imshow(
            matriz,
            cmap=mapa_cores,
            norm=normalizacao,
            aspect="auto",
        )
        ax.set_xticks(np.arange(len(rotulos_colunas)), labels=rotulos_colunas)
        ax.set_yticks(
            np.arange(len(influencia)),
            labels=influencia["UF retirada hipoteticamente"],
        )
        ax.xaxis.tick_top()
        ax.tick_params(
            axis="x",
            length=0,
            labelsize=10.5,
            labelcolor=self.cor_texto,
            pad=10,
        )
        ax.tick_params(
            axis="y",
            length=0,
            labelsize=9.2,
            labelcolor=self.cor_texto,
            pad=8,
        )
        for indice_rotulo, rotulo in enumerate(ax.get_yticklabels()):
            if indice_rotulo < 5:
                rotulo.set_fontweight("bold")

        for linha in range(matriz.shape[0]):
            for coluna in range(matriz.shape[1]):
                valor = matriz[linha, coluna]
                texto = f"{valor:+.1f}".replace(".", ",")
                cor_texto = (
                    self.cor_fundo
                    if abs(valor) >= maior_valor * 0.38
                    else self.cor_texto
                )
                ax.text(
                    coluna,
                    linha,
                    texto,
                    ha="center",
                    va="center",
                    fontsize=8.2,
                    fontweight="bold" if linha < 5 else "normal",
                    color=cor_texto,
                )

        ax.set_xticks(np.arange(-0.5, matriz.shape[1], 1), minor=True)
        ax.set_yticks(np.arange(-0.5, matriz.shape[0], 1), minor=True)
        ax.grid(which="minor", color=self.cor_fundo, linewidth=1.2)
        ax.tick_params(which="minor", bottom=False, left=False)
        for lado in ("top", "right", "left", "bottom"):
            ax.spines[lado].set_visible(False)

        barra = fig.colorbar(
            imagem,
            ax=ax,
            fraction=0.036,
            pad=0.05,
        )
        barra.set_label(
            "Variação relativa (%)",
            color=self.cor_secundaria,
            fontsize=9.5,
            labelpad=10,
        )
        barra.ax.tick_params(
            length=0,
            labelsize=8.5,
            labelcolor=self.cor_secundaria,
        )
        barra.outline.set_visible(False)

        fig.text(
            0.06,
            0.067,
            (
                "Ordenação: maior variação absoluta entre média, mediana, Gini, "
                "HHI e CR3. Vermelho indica redução; azul, aumento."
            ),
            ha="left",
            va="bottom",
            fontsize=9.3,
            color=self.cor_secundaria,
        )
        self._adicionar_fonte(fig)

        return self._finalizar_grafico(
            fig,
            "grafico_influencia_estadual_2022.png",
            exibir,
        )

    def plot_relacoes_estaduais_spearman(self, exibir: bool = True) -> Path:
        """Mostra quatro relações substantivas e seus casos mais influentes."""

        correlacoes = calcular_correlacoes_spearman(self.df).set_index("Relação")
        influencia = calcular_influencia_correlacoes_leave_one_out(self.df)

        fig, eixos = plt.subplots(2, 2, figsize=(15.5, 13.0))
        fig.subplots_adjust(
            left=0.08,
            right=0.97,
            top=0.82,
            bottom=0.18,
            wspace=0.24,
            hspace=0.42,
        )
        self._adicionar_cabecalho(
            fig,
            "Crescimento e composição territorial não formam uma única relação estadual",
            (
                "Cada painel apresenta o coeficiente de Spearman para as 27 UFs. "
                "As linhas pontilhadas marcam as medianas; os rótulos identificam "
                "os dois casos de maior influência leave-one-out em cada relação."
            ),
        )

        for ax, configuracao in zip(eixos.flat, self.CONFIGURACAO_RELACOES):
            relacao = str(configuracao["relacao"])
            variavel_x = str(configuracao["variavel_x"])
            variavel_y = str(configuracao["variavel_y"])
            dados = self.df[["Localidade", "Região", variavel_x, variavel_y]].dropna()

            for regiao, cor in self.CORES_REGIOES.items():
                grupo = dados.loc[dados["Região"].eq(regiao)]
                ax.scatter(
                    grupo[variavel_x],
                    grupo[variavel_y],
                    s=66,
                    color=cor,
                    edgecolor=self.cor_fundo,
                    linewidth=0.8,
                    alpha=0.92,
                    zorder=3,
                )

            ax.axvline(
                dados[variavel_x].median(),
                color=self.cor_secundaria,
                linestyle=":",
                linewidth=1.0,
                alpha=0.75,
                zorder=1,
            )
            ax.axhline(
                dados[variavel_y].median(),
                color=self.cor_secundaria,
                linestyle=":",
                linewidth=1.0,
                alpha=0.75,
                zorder=1,
            )
            if "Mudança" in variavel_y:
                ax.axhline(
                    0,
                    color=self.cor_texto,
                    linestyle="--",
                    linewidth=0.9,
                    alpha=0.45,
                    zorder=1,
                )

            casos_influentes = influencia.loc[
                influencia["Relação"].eq(relacao)
                & influencia["Rank de influência na relação"].le(2)
            ].sort_values("Rank de influência na relação")
            deslocamentos = [(7, 8), (7, -14)]
            alinhamentos = ["bottom", "top"]

            for posicao, linha in enumerate(casos_influentes.itertuples(index=False)):
                uf = str(linha[4])
                observacao = dados.loc[dados["Localidade"].eq(uf)].iloc[0]
                ax.annotate(
                    uf,
                    xy=(observacao[variavel_x], observacao[variavel_y]),
                    xytext=deslocamentos[posicao],
                    textcoords="offset points",
                    ha="left",
                    va=alinhamentos[posicao],
                    fontsize=8.6,
                    fontweight="bold",
                    color=self.cor_texto,
                    bbox={
                        "boxstyle": "round,pad=0.18",
                        "facecolor": self.cor_fundo,
                        "edgecolor": "none",
                        "alpha": 0.82,
                    },
                    zorder=5,
                )

            coeficiente = float(correlacoes.loc[relacao, "Spearman (ρ)"])
            quantidade = int(correlacoes.loc[relacao, "N"])
            texto_coeficiente = f"ρ = {coeficiente:+.2f}".replace(".", ",")
            ax.text(
                0.98,
                0.97,
                f"{texto_coeficiente}  |  N = {quantidade}",
                transform=ax.transAxes,
                ha="right",
                va="top",
                fontsize=9.4,
                fontweight="bold",
                color=self.cor_destaque,
            )
            ax.set_title(
                str(configuracao["titulo"]),
                loc="left",
                fontsize=13.2,
                fontweight="bold",
                color=self.cor_texto,
                pad=16,
            )
            ax.set_xlabel(
                str(configuracao["rotulo_x"]),
                fontsize=9.4,
                color=self.cor_secundaria,
                labelpad=9,
            )
            ax.set_ylabel(
                str(configuracao["rotulo_y"]),
                fontsize=9.4,
                color=self.cor_secundaria,
                labelpad=9,
            )
            if bool(configuracao["escala_log_x"]):
                ax.set_xscale("log")
                ax.xaxis.set_major_formatter(
                    FuncFormatter(self._formatar_eixo_populacao)
                )
            else:
                ax.xaxis.set_major_formatter(
                    FuncFormatter(lambda valor, _posicao: f"{valor:.0f}")
                )
            ax.yaxis.set_major_formatter(
                FuncFormatter(lambda valor, _posicao: f"{valor:.0f}")
            )
            self._aplicar_estilo_eixo(ax, eixo_grade="both")

        itens_legenda = [
            Line2D(
                [0],
                [0],
                marker="o",
                color="none",
                markerfacecolor=cor,
                markeredgecolor=self.cor_fundo,
                markersize=8,
                label=regiao,
            )
            for regiao, cor in self.CORES_REGIOES.items()
        ]
        fig.legend(
            handles=itens_legenda,
            loc="lower center",
            bbox_to_anchor=(0.52, 0.065),
            ncol=5,
            frameon=False,
            fontsize=9.2,
            columnspacing=2.0,
        )
        fig.text(
            0.06,
            0.105,
            (
                "Associações ecológicas descritivas: os coeficientes não demonstram "
                "causalidade nem relações no nível individual."
            ),
            ha="left",
            va="bottom",
            fontsize=9.2,
            color=self.cor_secundaria,
        )
        self._adicionar_fonte(fig)

        return self._finalizar_grafico(
            fig,
            "grafico_relacoes_estaduais_spearman.png",
            exibir,
        )

    def plot_estabilidade_ranking_populacional(
        self,
        exibir: bool = True,
    ) -> Path:
        """Compara as posições estaduais por população em 2010 e 2022."""

        ranking = calcular_estabilidade_ranking_populacional(self.df)
        resumo = resumir_estabilidade_ranking(ranking).iloc[0]
        rho = float(resumo["Spearman entre rankings (ρ)"])
        retencao_top_5 = float(resumo["Retenção Top 5 (%)"])
        mediana_mudanca = float(resumo["Mediana da mudança absoluta"])
        texto_rho = f"{rho:.2f}".replace(".", ",")
        texto_retencao = f"{retencao_top_5:.0f}".replace(".", ",")
        texto_mediana = f"{mediana_mudanca:.1f}".replace(".", ",")

        fig, ax = plt.subplots(figsize=(12.5, 10.5))
        fig.subplots_adjust(
            left=0.11,
            right=0.96,
            top=0.80,
            bottom=0.20,
        )
        self._adicionar_cabecalho(
            fig,
            f"A hierarquia populacional das UFs permaneceu amplamente estável entre os censos (ρ = {texto_rho})",
            (
                f"O Top 5 reteve {texto_retencao}% de seus integrantes, e a mudança "
                f"absoluta mediana foi de {texto_mediana} posições. Quanto mais perto "
                "da diagonal, maior a estabilidade da UF."
            ),
        )

        for linha in ranking.itertuples(index=False):
            posicao_2010 = int(linha[4])
            posicao_2022 = int(linha[5])
            regiao = str(linha[1])
            ax.plot(
                [posicao_2010, posicao_2010],
                [posicao_2010, posicao_2022],
                color=self.CORES_REGIOES[regiao],
                linewidth=1.0,
                alpha=0.30,
                zorder=1,
            )

        for regiao, cor in self.CORES_REGIOES.items():
            grupo = ranking.loc[ranking["Região"].eq(regiao)]
            ax.scatter(
                grupo["Posição em 2010"],
                grupo["Posição em 2022"],
                s=72,
                color=cor,
                edgecolor=self.cor_fundo,
                linewidth=0.9,
                alpha=0.94,
                zorder=3,
            )

        ax.plot(
            [1, 27],
            [1, 27],
            linestyle="--",
            linewidth=1.2,
            color=self.cor_secundaria,
            alpha=0.7,
            zorder=0,
        )

        maiores_movimentos = ranking.nlargest(
            7,
            "Mudança absoluta (posições)",
        )
        for indice, linha in enumerate(maiores_movimentos.itertuples(index=False)):
            deslocamento_y = 8 if indice % 2 == 0 else -10
            ax.annotate(
                str(linha[0]),
                xy=(int(linha[4]), int(linha[5])),
                xytext=(7, deslocamento_y),
                textcoords="offset points",
                ha="left",
                va="bottom" if deslocamento_y > 0 else "top",
                fontsize=8.8,
                fontweight="bold",
                color=self.cor_texto,
                bbox={
                    "boxstyle": "round,pad=0.18",
                    "facecolor": self.cor_fundo,
                    "edgecolor": "none",
                    "alpha": 0.84,
                },
                zorder=5,
            )

        marcas = [1, 5, 10, 15, 20, 25, 27]
        ax.set_xticks(marcas)
        ax.set_yticks(marcas)
        ax.set_xlim(0, 28)
        ax.set_ylim(28, 0)
        ax.set_xlabel(
            "Posição por população indígena em 2010",
            fontsize=10.5,
            color=self.cor_secundaria,
            labelpad=11,
        )
        ax.set_ylabel(
            "Posição por população indígena em 2022",
            fontsize=10.5,
            color=self.cor_secundaria,
            labelpad=11,
        )
        self._aplicar_estilo_eixo(ax, eixo_grade="both")

        itens_legenda = [
            Line2D(
                [0],
                [0],
                marker="o",
                color="none",
                markerfacecolor=cor,
                markeredgecolor=self.cor_fundo,
                markersize=8,
                label=regiao,
            )
            for regiao, cor in self.CORES_REGIOES.items()
        ]
        fig.legend(
            handles=itens_legenda,
            loc="lower center",
            bbox_to_anchor=(0.52, 0.072),
            ncol=5,
            frameon=False,
            fontsize=9.2,
            columnspacing=2.0,
        )
        fig.text(
            0.06,
            0.112,
            (
                "Rank 1 corresponde à maior população. Segmentos verticais mostram "
                "o deslocamento de cada UF em relação à posição de 2010."
            ),
            ha="left",
            va="bottom",
            fontsize=9.2,
            color=self.cor_secundaria,
        )
        self._adicionar_fonte(fig)

        return self._finalizar_grafico(
            fig,
            "grafico_estabilidade_ranking_populacional_2010_2022.png",
            exibir,
        )

    def plot_pca_perfis_estaduais(self, exibir: bool = True) -> Path:
        """Mostra os escores estaduais, a variância e as cargas da PCA."""

        resultado = calcular_pca_multivariada(self.df)
        variancia = resultado["variancia"]
        cargas = resultado["cargas"]
        escores = resultado["escores"]
        quantidade_retida = int(resultado["quantidade_componentes_retidos"])
        variancia_retida = float(
            variancia.loc[
                variancia["Componente retido"], "Variância explicada (%)"
            ].sum()
        )

        fig = plt.figure(figsize=(17.0, 10.5))
        grade = fig.add_gridspec(
            2,
            2,
            left=0.07,
            right=0.96,
            top=0.80,
            bottom=0.12,
            width_ratios=[1.40, 1.00],
            height_ratios=[0.92, 1.08],
            wspace=0.30,
            hspace=0.48,
        )
        ax_escores = fig.add_subplot(grade[:, 0])
        ax_variancia = fig.add_subplot(grade[0, 1])
        ax_cargas = fig.add_subplot(grade[1, 1])

        self._adicionar_cabecalho(
            fig,
            (
                f"{quantidade_retida} componentes preservam "
                f"{variancia_retida:.1f}% da variação entre as UFs"
            ).replace(".", ","),
            (
                "PCA aplicada a seis dimensões não redundantes, após "
                "centralização pela mediana e escala pelo IQR. Os eixos "
                "sintetizam padrões descritivos, sem estabelecer causalidade."
            ),
        )

        for regiao, cor in self.CORES_REGIOES.items():
            grupo = escores.loc[escores["Região"].eq(regiao)]
            ax_escores.scatter(
                grupo["PC1"],
                grupo["PC2"],
                s=82,
                color=cor,
                edgecolor=self.cor_fundo,
                linewidth=0.9,
                alpha=0.94,
                label=regiao,
                zorder=3,
            )

        distancias = np.hypot(escores["PC1"], escores["PC2"])
        extremos = escores.loc[distancias.nlargest(10).index]
        for indice, linha in enumerate(extremos.itertuples(index=False)):
            deslocamento_y = 8 if indice % 2 == 0 else -11
            ax_escores.annotate(
                str(linha[0]),
                xy=(float(linha[2]), float(linha[3])),
                xytext=(7, deslocamento_y),
                textcoords="offset points",
                ha="left",
                va="bottom" if deslocamento_y > 0 else "top",
                fontsize=8.6,
                fontweight="bold",
                color=self.cor_texto,
                bbox={
                    "boxstyle": "round,pad=0.16",
                    "facecolor": self.cor_fundo,
                    "edgecolor": "none",
                    "alpha": 0.82,
                },
                zorder=5,
            )

        ax_escores.axhline(
            0,
            color=self.cor_grade,
            linewidth=1.0,
            linestyle="--",
            zorder=0,
        )
        ax_escores.axvline(
            0,
            color=self.cor_grade,
            linewidth=1.0,
            linestyle="--",
            zorder=0,
        )
        ax_escores.set_title(
            "Mapa das UFs nos dois primeiros componentes",
            loc="left",
            fontsize=14,
            fontweight="bold",
            color=self.cor_texto,
            pad=16,
        )
        ax_escores.set_xlabel(
            f"PC1 — {float(variancia.iloc[0]['Variância explicada (%)']):.1f}%",
            fontsize=10.5,
            color=self.cor_secundaria,
            labelpad=10,
        )
        ax_escores.set_ylabel(
            f"PC2 — {float(variancia.iloc[1]['Variância explicada (%)']):.1f}%",
            fontsize=10.5,
            color=self.cor_secundaria,
            labelpad=10,
        )
        self._aplicar_estilo_eixo(ax_escores, eixo_grade="both")
        ax_escores.legend(
            loc="upper right",
            frameon=False,
            fontsize=9.2,
            title="Grande Região",
            title_fontsize=9.2,
        )

        posicoes = np.arange(len(variancia))
        cores_barras = np.where(
            variancia["Componente retido"],
            self.cor_media,
            self.cor_clara,
        )
        ax_variancia.bar(
            posicoes,
            variancia["Variância explicada (%)"],
            width=0.68,
            color=cores_barras,
            zorder=2,
        )
        ax_variancia.set_xticks(posicoes, variancia["Componente"])
        ax_variancia.set_ylabel(
            "Variância por componente (%)",
            fontsize=9.4,
            color=self.cor_secundaria,
        )
        ax_variancia.set_title(
            "Variância explicada e critério de retenção",
            loc="left",
            fontsize=13,
            fontweight="bold",
            color=self.cor_texto,
            pad=13,
        )
        self._aplicar_estilo_eixo(ax_variancia, eixo_grade="y")

        ax_acumulada = ax_variancia.twinx()
        ax_acumulada.plot(
            posicoes,
            variancia["Variância acumulada (%)"],
            color=self.cor_escura,
            marker="o",
            linewidth=1.8,
            markersize=5.5,
            zorder=4,
        )
        ax_acumulada.axhline(
            80,
            color=self.cor_secundaria,
            linestyle=":",
            linewidth=1.1,
        )
        ax_acumulada.set_ylim(0, 105)
        ax_acumulada.set_ylabel(
            "Variância acumulada (%)",
            fontsize=9.4,
            color=self.cor_secundaria,
        )
        ax_acumulada.tick_params(
            axis="y",
            length=0,
            labelcolor=self.cor_secundaria,
        )
        for lado in ("top", "right", "left", "bottom"):
            ax_acumulada.spines[lado].set_visible(False)

        cargas_retidas = (
            cargas.loc[cargas["Componente retido"]]
            .pivot(
                index="Variável",
                columns="Componente",
                values="Correlação variável–componente",
            )
            .reindex(index=VARIAVEIS_MULTIVARIADAS)
        )
        matriz_cargas = cargas_retidas.to_numpy()
        imagem = ax_cargas.imshow(
            matriz_cargas,
            cmap="RdBu_r",
            vmin=-1,
            vmax=1,
            aspect="auto",
        )
        rotulos_variaveis = [
            "Magnitude populacional",
            "Crescimento",
            "Urbanização em 2022",
            "Mudança da urbanização",
            "Presença em TI em 2022",
            "Mudança da presença em TI",
        ]
        ax_cargas.set_xticks(
            np.arange(cargas_retidas.shape[1]),
            cargas_retidas.columns,
        )
        ax_cargas.set_yticks(
            np.arange(len(rotulos_variaveis)),
            rotulos_variaveis,
        )
        ax_cargas.tick_params(axis="both", length=0, labelsize=8.8)
        for linha in range(matriz_cargas.shape[0]):
            for coluna in range(matriz_cargas.shape[1]):
                valor = float(matriz_cargas[linha, coluna])
                ax_cargas.text(
                    coluna,
                    linha,
                    f"{valor:+.2f}".replace(".", ","),
                    ha="center",
                    va="center",
                    fontsize=8.7,
                    fontweight="bold",
                    color=self.cor_fundo if abs(valor) >= 0.58 else self.cor_texto,
                )
        ax_cargas.set_title(
            "Correlação das dimensões com os componentes retidos",
            loc="left",
            fontsize=13,
            fontweight="bold",
            color=self.cor_texto,
            pad=13,
        )
        barra_cor = fig.colorbar(imagem, ax=ax_cargas, fraction=0.035, pad=0.03)
        barra_cor.set_label("Correlação", fontsize=9, color=self.cor_secundaria)
        barra_cor.ax.tick_params(length=0, labelsize=8.5)
        for lado in ("top", "right", "left", "bottom"):
            ax_cargas.spines[lado].set_visible(False)

        self._adicionar_fonte(fig)
        return self._finalizar_grafico(
            fig,
            "grafico_pca_perfis_estaduais.png",
            exibir,
        )

    def plot_validacao_agrupamentos_estaduais(
        self,
        exibir: bool = True,
        resultado: dict[str, pd.DataFrame | int] | None = None,
    ) -> Path:
        """Expõe por que nenhuma solução candidata foi aceita."""

        diagnostico = (
            avaliar_agrupamentos_multivariados(self.df)
            if resultado is None
            else resultado
        )
        avaliacao = diagnostico["avaliacao"]
        melhor_k = int(diagnostico["k_diagnostico"])
        melhor = avaliacao.loc[avaliacao["K"].eq(melhor_k)].iloc[0]

        fig, (ax_qualidade, ax_criterios) = plt.subplots(
            1,
            2,
            figsize=(17.0, 9.2),
            gridspec_kw={"width_ratios": [1.00, 1.42]},
        )
        fig.subplots_adjust(
            left=0.07,
            right=0.96,
            top=0.76,
            bottom=0.17,
            wspace=0.34,
        )
        self._adicionar_cabecalho(
            fig,
            "Nenhuma solução candidata sustenta uma segmentação estadual robusta",
            (
                "K-means avaliado de K=2 a K=6 sobre os três componentes retidos. "
                "A aceitação exigiria qualidade interna, tamanho mínimo e "
                "estabilidade em quatro perturbações — todos simultaneamente."
            ),
        )

        ax_qualidade.plot(
            avaliacao["K"],
            avaliacao["Silhouette médio"],
            color=self.cor_escura,
            linewidth=2.2,
            marker="o",
            markersize=7,
            label="Silhouette médio",
            zorder=3,
        )
        ax_qualidade.axhline(
            CRITERIOS_ACEITACAO_AGRUPAMENTOS["Silhouette médio"],
            color=self.cor_secundaria,
            linestyle="--",
            linewidth=1.1,
            label="Limiar de aceitação (0,50)",
        )
        ax_qualidade.scatter(
            [melhor_k],
            [float(melhor["Silhouette médio"])],
            s=155,
            facecolors="none",
            edgecolors=self.cor_destaque,
            linewidths=2.0,
            zorder=4,
        )
        ax_qualidade.set_ylim(0.25, 0.56)
        ax_qualidade.set_xticks(avaliacao["K"])
        ax_qualidade.set_xlabel(
            "Número de agrupamentos (K)",
            fontsize=10,
            color=self.cor_secundaria,
            labelpad=10,
        )
        ax_qualidade.set_ylabel(
            "Silhouette médio",
            fontsize=10,
            color=self.cor_secundaria,
            labelpad=10,
        )
        ax_qualidade.set_title(
            "Qualidade interna permanece abaixo do limiar",
            loc="left",
            fontsize=13.5,
            fontweight="bold",
            color=self.cor_texto,
            pad=17,
        )
        self._aplicar_estilo_eixo(ax_qualidade, eixo_grade="y")

        ax_tamanho = ax_qualidade.twinx()
        ax_tamanho.plot(
            avaliacao["K"],
            avaliacao["Menor agrupamento (UFs)"],
            color=self.cor_media,
            linewidth=1.5,
            marker="s",
            markersize=5.5,
            linestyle=":",
            label="Menor grupo",
        )
        ax_tamanho.axhline(
            CRITERIOS_ACEITACAO_AGRUPAMENTOS["Menor agrupamento (UFs)"],
            color=self.cor_media,
            linestyle="--",
            linewidth=0.9,
            alpha=0.65,
        )
        ax_tamanho.set_ylim(0, 12)
        ax_tamanho.set_ylabel(
            "UFs no menor grupo",
            fontsize=10,
            color=self.cor_media,
            labelpad=10,
        )
        ax_tamanho.tick_params(axis="y", length=0, labelcolor=self.cor_media)
        for lado in ("top", "right", "left", "bottom"):
            ax_tamanho.spines[lado].set_visible(False)

        linhas_qualidade, rotulos_qualidade = ax_qualidade.get_legend_handles_labels()
        linhas_tamanho, rotulos_tamanho = ax_tamanho.get_legend_handles_labels()
        ax_qualidade.legend(
            linhas_qualidade + linhas_tamanho,
            rotulos_qualidade + rotulos_tamanho,
            loc="lower left",
            frameon=False,
            fontsize=8.8,
        )

        especificacao_criterios = [
            (
                "Silhouette ≥ 0,50",
                "Silhouette médio",
                "Atende silhouette",
                "decimal",
            ),
            (
                "Menor grupo ≥ 3 UFs",
                "Menor agrupamento (UFs)",
                "Atende tamanho mínimo",
                "inteiro",
            ),
            (
                "ARI mediano das\nreinicializações ≥ 0,90",
                "ARI mediano — reinicializações",
                "Atende reinicializações",
                "decimal",
            ),
            (
                "ARI mínimo sem\numa UF ≥ 0,50",
                "ARI mínimo — retirada de UF",
                "Atende retirada de UF",
                "decimal",
            ),
            (
                "ARI mínimo sem\numa variável ≥ 0,50",
                "ARI mínimo — retirada de variável",
                "Atende retirada de variável",
                "decimal",
            ),
            (
                "ARI P10 das\nsubamostras ≥ 0,50",
                "ARI P10 — subamostras",
                "Atende subamostras",
                "decimal",
            ),
        ]
        matriz_criterios = np.array(
            [
                avaliacao[coluna_boolean].astype(int).to_numpy()
                for _, _, coluna_boolean, _ in especificacao_criterios
            ]
        )
        mapa_criterios = LinearSegmentedColormap.from_list(
            "criterios",
            ["#F3D6D4", "#39708E"],
        )
        ax_criterios.imshow(
            matriz_criterios,
            cmap=mapa_criterios,
            vmin=0,
            vmax=1,
            aspect="auto",
        )
        ax_criterios.set_xticks(
            np.arange(len(avaliacao)),
            [f"K={k}" for k in avaliacao["K"]],
        )
        ax_criterios.set_yticks(
            np.arange(len(especificacao_criterios)),
            [item[0] for item in especificacao_criterios],
        )
        ax_criterios.tick_params(axis="both", length=0, labelsize=9.2)
        for linha, (_, coluna_valor, coluna_boolean, formato) in enumerate(
            especificacao_criterios
        ):
            for coluna, registro in avaliacao.iterrows():
                valor = float(registro[coluna_valor])
                valor_formatado = (
                    str(int(valor))
                    if formato == "inteiro"
                    else f"{valor:.2f}".replace(".", ",")
                )
                atendeu = bool(registro[coluna_boolean])
                ax_criterios.text(
                    coluna,
                    linha,
                    f"{'✓' if atendeu else '×'}  {valor_formatado}",
                    ha="center",
                    va="center",
                    fontsize=9.2,
                    fontweight="bold",
                    color=self.cor_fundo if atendeu else self.cor_texto,
                )
        ax_criterios.set_title(
            "Matriz de decisão: os seis critérios são cumulativos",
            loc="left",
            fontsize=13.5,
            fontweight="bold",
            color=self.cor_texto,
            pad=17,
        )
        for lado in ("top", "right", "left", "bottom"):
            ax_criterios.spines[lado].set_visible(False)

        fig.text(
            0.07,
            0.095,
            (
                f"Melhor resultado interno: K={melhor_k}, silhouette "
                f"{float(melhor['Silhouette médio']):.3f} e grupos de "
                f"{melhor['Tamanhos dos agrupamentos']} UFs. A solução é "
                "mantida apenas como diagnóstico, pois não satisfaz o protocolo."
            ).replace(".", ",", 1),
            ha="left",
            va="bottom",
            fontsize=10,
            fontweight="bold",
            color=self.cor_texto,
        )
        fig.text(
            0.96,
            0.095,
            "✓ atende  |  × não atende",
            ha="right",
            va="bottom",
            fontsize=9.2,
            color=self.cor_secundaria,
        )
        self._adicionar_fonte(fig)
        return self._finalizar_grafico(
            fig,
            "grafico_validacao_agrupamentos_estaduais.png",
            exibir,
        )
