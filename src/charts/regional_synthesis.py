from pathlib import Path
from typing import ClassVar

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import patches


class PainelSinteseRegional:
    """
    Constrói um painel executivo que sintetiza o perfil de
    residência da população indígena nas Grandes Regiões.

    A visualização compara a distribuição entre áreas urbanas
    e rurais da população residente em Terras Indígenas e fora
    delas, com base no Censo Demográfico de 2022.
    """

    COLUNAS_OBRIGATORIAS : ClassVar[list[str]] = [
        "NM_REGIAO",
        "Indígenas 2022 TI Total",
        "Indígenas 2022 TI Urbano",
        "Indígenas 2022 TI Rural",
        "Indígenas 2022 Fora TI Total",
        "Indígenas 2022 Fora TI Urbano",
        "Indígenas 2022 Fora TI Rural",
    ]

    def __init__(
        self,
        gdf: pd.DataFrame,
        diretorio_saida: str | Path,
    ) -> None:
        self.gdf = gdf.copy()
        self.diretorio_saida = Path(diretorio_saida)

        # Paleta visual já utilizada no projeto.
        self.cor_urbano = "#8FB7CF"
        self.cor_rural = "#173F5F"

        self.cor_texto = "#263238"
        self.cor_secundaria = "#607D8B"
        self.cor_borda = "#D9E1E5"

        self.cor_fundo = "#FFFFFF"
        self.cor_caixa_clara = "#EAF3F8"

        self._validar_base()

    def _validar_base(
        self,
    ) -> None:
        """Verifica se a base possui as colunas necessárias."""

        if self.gdf.empty:
            raise ValueError("A base regional está vazia.")

        colunas_ausentes = [
            coluna
            for coluna in self.COLUNAS_OBRIGATORIAS
            if coluna not in self.gdf.columns
        ]

        if colunas_ausentes:
            raise KeyError(
                f"As seguintes colunas não existem na base: {colunas_ausentes}"
            )

        quantidade_regioes = self.gdf["NM_REGIAO"].nunique()

        if quantidade_regioes != 5:
            raise ValueError(
                "A base deve conter exatamente cinco "
                f"Grandes Regiões, mas foram encontradas "
                f"{quantidade_regioes}."
            )

    @staticmethod
    def _formatar_percentual(
        valor: float,
    ) -> str:
        """Formata percentuais segundo a notação brasileira."""

        return f"{valor:.1f}".replace(".", ",")

    @staticmethod
    def _normalizar_regiao(
        regiao: str,
    ) -> str:
        """Padroniza os nomes das Grandes Regiões."""

        regiao = str(regiao).strip()

        equivalencias = {
            "Centro-oeste": "Centro-Oeste",
            "Centro-Oeste": "Centro-Oeste",
            "CENTRO-OESTE": "Centro-Oeste",
            "Norte": "Norte",
            "Nordeste": "Nordeste",
            "Sudeste": "Sudeste",
            "Sul": "Sul",
        }

        return equivalencias.get(
            regiao,
            regiao,
        )

    def _preparar_dados(
        self,
    ) -> dict[str, dict[str, float]]:
        """
        Calcula os percentuais urbano e rural dentro e fora
        das Terras Indígenas em cada Grande Região.
        """

        dados: dict[str, dict[str, float]] = {}

        for _, linha in self.gdf.iterrows():
            regiao = self._normalizar_regiao(linha["NM_REGIAO"])

            ti_total = float(linha["Indígenas 2022 TI Total"])

            fora_ti_total = float(linha["Indígenas 2022 Fora TI Total"])

            if ti_total <= 0:
                raise ValueError(
                    "O total da população residente em "
                    f"Terras Indígenas é inválido para {regiao}."
                )

            if fora_ti_total <= 0:
                raise ValueError(
                    "O total da população residente fora de "
                    f"Terras Indígenas é inválido para {regiao}."
                )

            ti_urbano = float(linha["Indígenas 2022 TI Urbano"]) / ti_total * 100

            ti_rural = float(linha["Indígenas 2022 TI Rural"]) / ti_total * 100

            fora_ti_urbano = (
                float(linha["Indígenas 2022 Fora TI Urbano"]) / fora_ti_total * 100
            )

            fora_ti_rural = (
                float(linha["Indígenas 2022 Fora TI Rural"]) / fora_ti_total * 100
            )

            dados[regiao] = {
                "ti_urbano": ti_urbano,
                "ti_rural": ti_rural,
                "fora_ti_urbano": fora_ti_urbano,
                "fora_ti_rural": fora_ti_rural,
            }

        regioes_esperadas = {
            "Norte",
            "Nordeste",
            "Centro-Oeste",
            "Sudeste",
            "Sul",
        }

        regioes_ausentes = regioes_esperadas - set(dados)

        if regioes_ausentes:
            raise ValueError(
                "Não foram encontrados dados para as regiões: "
                f"{sorted(regioes_ausentes)}"
            )

        return dados

    def _desenhar_barra(
        self,
        ax,
        y: float,
        percentual_urbano: float,
        percentual_rural: float,
        categoria_destaque: str,
    ) -> None:
        """
        Desenha uma barra horizontal empilhada a 100%.

        Apenas o percentual correspondente à categoria
        predominante na comparação é destacado.
        """

        altura = 0.16

        ax.add_patch(
            patches.Rectangle(
                (0, y),
                percentual_urbano,
                altura,
                facecolor=self.cor_urbano,
                edgecolor="none",
            )
        )

        ax.add_patch(
            patches.Rectangle(
                (percentual_urbano, y),
                percentual_rural,
                altura,
                facecolor=self.cor_rural,
                edgecolor="none",
            )
        )

        if categoria_destaque == "rural":
            posicao_x = percentual_urbano + percentual_rural / 2

            valor = percentual_rural
            cor_rotulo = "white"

        elif categoria_destaque == "urbano":
            posicao_x = percentual_urbano / 2
            valor = percentual_urbano
            cor_rotulo = self.cor_rural

        else:
            raise ValueError("A categoria de destaque deve ser 'urbano' ou 'rural'.")

        ax.text(
            posicao_x,
            y + altura / 2,
            (f"{self._formatar_percentual(valor)}%"),
            ha="center",
            va="center",
            fontsize=9.3,
            fontweight="bold",
            color=cor_rotulo,
        )

    def _desenhar_painel_regional(
        self,
        ax,
        regiao: str,
        dados: dict[str, float],
    ) -> None:
        """Desenha o painel comparativo de uma região."""

        ax.set_xlim(
            0,
            100,
        )

        ax.set_ylim(
            0,
            1,
        )

        ax.axis("off")

        ax.text(
            0,
            0.97,
            regiao.upper(),
            ha="left",
            va="top",
            fontsize=12,
            fontweight="bold",
            color=self.cor_rural,
        )

        ax.plot(
            [0, 100],
            [0.88, 0.88],
            color=self.cor_borda,
            linewidth=1.1,
        )

        ax.text(
            0,
            0.80,
            "Em TI",
            ha="left",
            va="center",
            fontsize=9.2,
            color=self.cor_secundaria,
        )

        self._desenhar_barra(
            ax=ax,
            y=0.58,
            percentual_urbano=dados["ti_urbano"],
            percentual_rural=dados["ti_rural"],
            categoria_destaque="rural",
        )

        ax.text(
            0,
            0.44,
            "Fora de TI",
            ha="left",
            va="center",
            fontsize=9.2,
            color=self.cor_secundaria,
        )

        self._desenhar_barra(
            ax=ax,
            y=0.22,
            percentual_urbano=dados["fora_ti_urbano"],
            percentual_rural=dados["fora_ti_rural"],
            categoria_destaque="urbano",
        )

    def _adicionar_legenda(
        self,
        fig,
    ) -> None:
        """Adiciona a legenda da composição urbano-rural."""

        handles = [
            patches.Patch(
                facecolor=self.cor_urbano,
                edgecolor="none",
                label="Urbano",
            ),
            patches.Patch(
                facecolor=self.cor_rural,
                edgecolor="none",
                label="Rural",
            ),
        ]

        fig.legend(
            handles=handles,
            loc="upper center",
            bbox_to_anchor=(
                0.84,
                0.905,
            ),
            ncol=2,
            frameon=False,
            fontsize=12.5,
            handlelength=2.8,
            columnspacing=2.2,
        )

    def _desenhar_resumo_executivo(
        self,
        fig,
        posicao: list[float],
    ) -> None:
        """Adiciona o quadro de resumo executivo."""

        ax = fig.add_axes(posicao)

        ax.axis("off")

        texto = (
            "Terras Indígenas \n\n"
            "Predominância rural em todas as regiões\n\n"
            "──────────────────────────────────────────────────\n"
            "Fora de Terras Indígenas\n\n"
            "Predominância urbana em todas as regiões\n\n"
            "──────────────────────────────────────────────────\n"
            "Conclusão\n\n"
            "O padrão repetiu-se nas cinco regiões."
        )

        ax.text(
            0,
            1,
            "PRINCIPAIS ACHADOS",
            ha="left",
            va="top",
            fontsize=16.0,
            fontweight="bold",
            color=self.cor_rural,
        )

        ax.text(
            0,
            0.83,
            texto,
            ha="left",
            va="top",
            fontsize=12.0,
            color="white",
            linespacing=1.35,
            bbox={
                "boxstyle": "round,pad=0.85",
                "facecolor": self.cor_rural,
                "edgecolor": "none",
                "alpha": 0.98,
            },
        )

    def _desenhar_sintese(
        self,
        fig,
        posicao: list[float],
    ) -> None:
        """Adiciona a síntese interpretativa final."""

        ax = fig.add_axes(posicao)

        ax.axis("off")

        texto = (
            "A comparação revelou um padrão consistente em todas as "
            "Grandes Regiões brasileiras. Entre os indígenas residentes "
            "em Terras Indígenas,\npredominou a população localizada em "
            "áreas rurais. Fora das Terras Indígenas, ocorreu o padrão "
            "oposto, com predominância da população \nresidente em áreas "
            "urbanas. Os resultados mostram que o perfil de residência "
            "da população indígena varia de forma expressiva conforme "
            "o\ncontexto territorial analisado."
        )

        ax.text(
            0,
            1,
            "INTERPRETAÇÃO DOS RESULTADOS",
            ha="left",
            va="top",
            fontsize=18.0,
            fontweight="bold",
            color=self.cor_rural,
        )

        ax.text(
            0,
            0.46,
            texto,
            ha="left",
            va="top",
            fontsize=13.0,
            color=self.cor_rural,
            linespacing=1.45,
            wrap=True,
            bbox={
                "boxstyle": "round,pad=1.5",
                "facecolor": self.cor_caixa_clara,
                "edgecolor": self.cor_urbano,
                "linewidth": 1,
                "alpha": 0.98,
            },
        )

    def plot(
        self,
        exibir: bool = True,
    ) -> Path:
        """
        Constrói, salva e opcionalmente exibe o painel.

        Parameters
        ----------
        exibir:
            Define se a figura deve ser exibida no ambiente
            após o salvamento.

        Returns
        -------
        Path
            Caminho da imagem gerada.
        """

        dados = self._preparar_dados()

        fig = plt.figure(
            figsize=(15, 12),
            facecolor=self.cor_fundo,
        )

        fig.text(
            0.05,
            1.02,
            (
                "Dentro de terras Indígenas, residência rural; fora delas,\n"
                "residência urbana — um padrão que se repete em todo Brasil."
            ),
            ha="left",
            va="top",
            fontsize=28.5,
            fontweight="bold",
            color=self.cor_texto,
            linespacing=1.28,
        )

        fig.text(
            0.05,
            0.930,
            (
                "Em todas as Grandes Regiões, o perfil de residência da população indígena\n"
                "inverte-se conforme o contexto territorial: nas Terras Indígenas predomina\n"
                "a residência rural; fora delas, predomina a residência urbana."
            ),
            ha="left",
            va="top",
            fontsize=14.0,
            color=self.cor_rural,
        )

        self._adicionar_legenda(fig)

        posicoes = {
            "Norte": [
                0.05,
                0.675,
                0.40,
                0.18,
            ],
            "Nordeste": [
                0.50,
                0.675,
                0.40,
                0.18,
            ],
            "Centro-Oeste": [
                0.05,
                0.510,
                0.40,
                0.18,
            ],
            "Sudeste": [
                0.50,
                0.510,
                0.40,
                0.18,
            ],
            "Resumo": [
                0.06,
                0.350,
                0.40,
                0.18,
            ],
            "Sul": [
                0.50,
                0.340,
                0.40,
                0.18,
            ],
            "Síntese": [
                0.068,
                0.125,
                0.90,
                0.09,
            ],
        }

        for regiao in [
            "Norte",
            "Nordeste",
            "Centro-Oeste",
            "Sudeste",
            "Sul",
        ]:
            ax_regiao = fig.add_axes(posicoes[regiao])

            self._desenhar_painel_regional(
                ax=ax_regiao,
                regiao=regiao,
                dados=dados[regiao],
            )

        self._desenhar_resumo_executivo(
            fig=fig,
            posicao=posicoes["Resumo"],
        )

        self._desenhar_sintese(
            fig=fig,
            posicao=posicoes["Síntese"],
        )

        fig.text(
            0.05,
            0.038,
            ("Fonte: IBGE — Censo Demográfico 2022. Elaboração: Lucas Dias Noronha."),
            ha="left",
            va="bottom",
            fontsize=8.5,
            color=self.cor_secundaria,
        )

        self.diretorio_saida.mkdir(
            parents=True,
            exist_ok=True,
        )

        caminho_saida = self.diretorio_saida / "grafico_sintese_regional.png"

        fig.savefig(
            caminho_saida,
            dpi=300,
            bbox_inches="tight",
            facecolor=self.cor_fundo,
        )

        if exibir:
            plt.show()

        plt.close(fig)
