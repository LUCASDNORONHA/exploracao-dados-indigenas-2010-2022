import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from matplotlib import ticker
from matplotlib.offsetbox import OffsetImage, AnnotationBbox


class PlotBar:
    def __init__(self, db, titulo='', rotulo_x='', rotulo_y='', cor=None):
        self.db = db
        self.titulo = titulo
        self.rotulo_x = rotulo_x
        self.rotulo_y = rotulo_y
        self.cor = cor or ['#C6D9F1', '#1B4965']
        sns.set_style("whitegrid")
        plt.rcParams.update({
            'font.size': 12,
            'font.family': 'DejaVu Sans',
            'axes.titlesize': 16,
            'axes.titleweight': 'bold'
        })

    # -------------------------------------------------------
    # MÉTODOS AUXILIARES
    # -------------------------------------------------------
    def _formatter_milhoes(self, x, pos):
        if x >= 1e6:
            return f'{x/1e6:.1f}M'
        elif x >= 1e3:
            return f'{x/1e3:.0f}k'
        return f'{x:,.0f}'

    def _adicionar_logo(self, fig):
        try:
            logo_path = '../assets/IESB_Logo.png'
            logo = plt.imread(logo_path)
            imagebox = OffsetImage(logo, zoom=0.30)
            ab = AnnotationBbox(imagebox, (0.98, 0.02), frameon=False, 
                                xycoords='figure fraction', box_alignment=(1,0))
            fig.add_artist(ab)
        except FileNotFoundError:
            print("Arquivo de logo não encontrado. O logo não será adicionado.")

    def _adicionar_fonte(self):
        plt.figtext(0.02, 0.01, 
                    'Fonte: IBGE - Censo 2022. Elaborado por Lucas Dias Noronha.', 
                    ha='left', va='bottom', fontsize=10, color='gray')

    # -------------------------------------------------------
    # MÉTODOS DE PLOTAGEM
    # -------------------------------------------------------

    def plot_crescimento_pais(self):
        db_pais = self.db[self.db['Localidade'] == 'Brasil']

        diferenca = db_pais['Indígenas 2022 Total'] - db_pais['Indígenas 2010 Total']
        crescimento_pct = (diferenca / db_pais['Indígenas 2010 Total']) * 100

        anos = ['2010', '2022']
        valores = [
            db_pais['Indígenas 2010 Total'].values[0],
            db_pais['Indígenas 2022 Total'].values[0]
        ]

        fig, ax = plt.subplots(figsize=(10, 5))
        bars = ax.barh(anos, valores, color=self.cor, height=0.6)

        ax.xaxis.set_major_formatter(ticker.FuncFormatter(self._formatter_milhoes))

     
        for i, bar in enumerate(bars):
            width = bar.get_width()   
            cor_invertida = self.cor[1 - i] 
            ax.text(width * 0.98, bar.get_y() + bar.get_height()/2,
                    f"{width:,.0f}",
                    ha='right', va='center',
                    fontsize=12, fontweight='bold',
                    color=cor_invertida) 
            
        ax.set_title(
                f'Variação Absoluta da População Indígena\nResidente no Brasil (2010–2022)',
                fontsize=14,
                loc='center',
                pad=20,
                wrap=True, 
                color=self.cor[1],
        )
        sns.despine(top=True, right=True, left=True, bottom=False)
        ax.xaxis.grid(True, linestyle='--', alpha=0.7)
        ax.yaxis.grid(False)
        ax.tick_params(axis='x', length=0, labelcolor=self.cor[1])
        ax.tick_params(axis='y', length=0, labelcolor=self.cor[1])
        # Aumentei levemente o limite para dar respiro à caixa de texto
        ax.set_xlim(right=max(valores) * 1.30)

        # Ajuste: Formatação com separador de milhar e sinal (+ ou -)
        texto_resumo = (
            "Crescimento:\n"
            f"   • Absoluto: {int(diferenca.iloc[0]):+,.0f}\n"
            f"   • Percentual: {float(crescimento_pct.iloc[0]):+.2f}%"
        )

        # Ajuste: Alinhamento pela direita (ha='right') para ancorar melhor na borda
        ax.text(0.92, 0.35, texto_resumo, transform=ax.transAxes,
                fontsize=9, ha='left', va='center', color=self.cor[0], fontstyle='italic',
                bbox=dict(boxstyle='round,pad=0.5',
                          facecolor=self.cor[1], alpha=0.999, edgecolor='none'))

        self._adicionar_fonte()
        self._adicionar_logo(fig)
        plt.tight_layout(rect=[0, 0.05, 1, 0.93])
        # Garante que a cor de fundo seja salva corretamente
        plt.savefig('../reports/figures/grafico_crescimento_populacao_indigena_brasil.png',
                    dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor())
        plt.show()

    # -------------------------------------------------------

    def plot_crescimento_area(self):
            db_pais = self.db[self.db['Localidade'] == 'Brasil']

            diferenca_urbano = db_pais['Indígenas 2022 Urbano'] - db_pais['Indígenas 2010 Urbano']
            diferenca_rural = db_pais['Indígenas 2022 Rural'] - db_pais['Indígenas 2010 Rural']
            crescimento_pct_urbano = (diferenca_urbano / db_pais['Indígenas 2010 Urbano']) * 100
            crescimento_pct_rural = (diferenca_rural / db_pais['Indígenas 2010 Rural']) * 100
            percentual_urbano_2010 = db_pais['% Indígenas 2010 Urbano']
            percentual_urbano_2022 = db_pais['% Indígenas 2022 Urbano']
            percentual_rural_2010 = db_pais['% Indígenas 2010 Rural']
            percentual_rural_2022 = db_pais['% Indígenas 2022 Rural']

            categorias = ['Urbano', 'Rural']
            localidade = db_pais['Localidade'].values[0]
            valores_2010 = [db_pais['Indígenas 2010 Urbano'].values[0], db_pais['Indígenas 2010 Rural'].values[0]]
            valores_2022 = [db_pais['Indígenas 2022 Urbano'].values[0], db_pais['Indígenas 2022 Rural'].values[0]]

            fig, ax = plt.subplots(figsize=(10, 6))
            y_pos = np.arange(len(categorias))
            height = 0.35
            gap = 0.02

            ax.barh(y_pos - height/2 - gap, valores_2010, height=height, color=self.cor[0], label='2010')
            ax.barh(y_pos + height/2 + gap, valores_2022, height=height, color=self.cor[1], label='2022')

            for i in range(len(categorias)):
                ax.text(valores_2010[i]*0.98, y_pos[i] - height/2 - gap, f"{valores_2010[i]:,.0f}",
                        va='center', ha='right', fontsize=12, color=self.cor[1], fontweight='bold')
                ax.text(valores_2022[i]*0.98, y_pos[i] + height/2 + gap, f"{valores_2022[i]:,.0f}",
                        va='center', ha='right', fontsize=12, color=self.cor[0], fontweight='bold')

            ax.set_yticks(y_pos)
            ax.set_yticklabels(categorias)
            ax.invert_yaxis()
 
            ax.set_title(
                f'Crescimento da População Indígena no {localidade} (2010–2022)\n'
                f'Segundo a Situação do Domicílio (Urbana e Rural)',
                fontsize=14,
                loc='center',
                pad=20,
                wrap=True,
                color=self.cor[1], 
            )
            ax.xaxis.set_major_formatter(ticker.FuncFormatter(self._formatter_milhoes))

            sns.despine(ax=ax, top=True, right=True, left=True, bottom=False)
            ax.xaxis.grid(True, linestyle='--', alpha=0.7)
            ax.yaxis.grid(False)
            ax.tick_params(axis='x', length=0, labelcolor=self.cor[1])
            ax.tick_params(axis='y', length=0, labelcolor=self.cor[1])

            # Aumentei um pouco o limite para garantir espaço para as caixas de texto
            ax.set_xlim(right=max(max(valores_2010), max(valores_2022)) * 1.35)
            ax.legend(frameon=False, loc='lower right', bbox_to_anchor=(1, 0.1)) # Ajuste fino na legenda

            # Formatação melhorada dos números nas caixas de texto (com separador de milhar)
            texto_resumo_1 = (
                "Variação Demográfica (Absoluta e Relativa):\n"
                f"   • Urbano: {int(diferenca_urbano.iloc[0]):+,.0f} ({float(crescimento_pct_urbano.iloc[0]):+.2f}%)\n"
                f"   • Rural:  {int(diferenca_rural.iloc[0]):+,.0f} ({float(crescimento_pct_rural.iloc[0]):+.2f}%)"
            )

            ax.text(0.99, 0.85, texto_resumo_1, transform=ax.transAxes, # Ajuste na posição X e Y
                    fontsize=9, ha='left', va='top', color=self.cor[0], fontstyle='italic',
                    bbox=dict(boxstyle='round,pad=0.5',
                            facecolor=self.cor[1],alpha=0.999, edgecolor='none'))

            texto_resumo_2 = (
                "Variação na Composição Relativa:\n"
                f"   • Urbano: {float(percentual_urbano_2010.iloc[0]):.2f}% → {float(percentual_urbano_2022.iloc[0]):.2f}%\n"
                f"   • Rural:  {float(percentual_rural_2010.iloc[0]):.2f}% → {float(percentual_rural_2022.iloc[0]):.2f}%"
            )

            ax.text(0.99, 0.50, texto_resumo_2, transform=ax.transAxes, # Ajuste na posição X e Y
                    fontsize=9, ha='left', va='top', color=self.cor[1], fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.5',
                            facecolor=self.cor[0], alpha=0.6, edgecolor='none'))

            self._adicionar_fonte()
            self._adicionar_logo(fig)
            plt.tight_layout(rect=[0, 0.05, 1, 0.93])
            plt.savefig('../reports/figures/grafico_crescimento_pop_indigena_area.png',
                        dpi=300, bbox_inches='tight')
            plt.show()

    # -------------------------------------------------------
def plot_distribuicao_detalhada_ti(self):
    db_pais = self.db[self.db['Localidade'] == 'Brasil']

    categorias = ['TI - Rural', 'Fora de TI - Urbano', 'Fora de TI - Rural', 'TI - Urbano']

    val_2010 = [
        db_pais['Indígenas 2010 TI Rural'].values[0],
        db_pais['Indígenas 2010 Fora TI Urbano'].values[0],
        db_pais['Indígenas 2010 Fora TI Rural'].values[0],
        db_pais['Indígenas 2010 TI Urbano'].values[0]
    ]

    val_2022 = [
        db_pais['Indígenas 2022 TI Rural'].values[0],
        db_pais['Indígenas 2022 Fora TI Urbano'].values[0],
        db_pais['Indígenas 2022 Fora TI Rural'].values[0],
        db_pais['Indígenas 2022 TI Urbano'].values[0]
    ]

    pct_2010 = [
        db_pais['% Indígenas 2010 TI Rural'].values[0],
        db_pais['% Indígenas 2010 Fora TI Urbano'].values[0],
        db_pais['% Indígenas 2010 Fora TI Rural'].values[0],
        db_pais['% Indígenas 2010 TI Urbano'].values[0]
    ]

    pct_2022 = [
        db_pais['% Indígenas 2022 TI Rural'].values[0],
        db_pais['% Indígenas 2022 Fora TI Urbano'].values[0],
        db_pais['% Indígenas 2022 Fora TI Rural'].values[0],
        db_pais['% Indígenas 2022 TI Urbano'].values[0]
    ]

    # Ordenação opcional (mantém lógica original)
    dados_ordenados = sorted(zip(categorias, val_2010, val_2022, pct_2010, pct_2022),
                             key=lambda x: x[2], reverse=False)
    categorias, val_2010, val_2022, pct_2010, pct_2022 = zip(*dados_ordenados)

    fig, ax = plt.subplots(figsize=(12, 8))
    y_pos = np.arange(len(categorias))
    height = 0.35
    gap = 0.02

    # Barras horizontais
    bars_2010 = ax.barh(y_pos - height/2 - gap, val_2010, height, color=self.cor[0], label='2010')
    bars_2022 = ax.barh(y_pos + height/2 + gap, val_2022, height, color=self.cor[1], label='2022')

    # --- Função auxiliar para contraste automático do texto ---
    import matplotlib.colors as mcolors
    def cor_texto_contraste(cor_rgb):
        r, g, b = mcolors.to_rgb(cor_rgb)
        luminancia = 0.299*r + 0.587*g + 0.114*b
        return 'black' if luminancia > 0.6 else 'white'

    # --- Rótulos internos com contraste invertido ---
    for i in range(len(categorias)):
        # 2010
        cor_texto_2010 = cor_texto_contraste(self.cor[0])
        ax.text(val_2010[i]*0.98, y_pos[i] - height/2 - gap,
                f"{val_2010[i]:,.0f}\n({pct_2010[i]:.1f}%)",
                ha='right', va='center', fontsize=10, color=cor_texto_2010, fontweight='bold')
        # 2022
        cor_texto_2022 = cor_texto_contraste(self.cor[1])
        ax.text(val_2022[i]*0.98, y_pos[i] + height/2 + gap,
                f"{val_2022[i]:,.0f}\n({pct_2022[i]:.1f}%)",
                ha='right', va='center', fontsize=10, color=cor_texto_2022, fontweight='bold')

    # --- Eixos e rótulos ---
    ax.set_yticks(y_pos)
    ax.set_yticklabels(categorias, fontsize=11)
    ax.invert_yaxis()

    ax.set_title(
        'Distribuição Detalhada da População Indígena (2010–2022)\n'
        'por Situação de Domicílio e Localização (TI)',
        fontsize=14, pad=25, color=self.cor[1], wrap=True
    )

    ax.xaxis.set_major_formatter(ticker.FuncFormatter(self._formatter_milhoes))
    ax.set_xlim(right=max(max(val_2010), max(val_2022)) * 1.35)
    ax.legend(frameon=False, loc='lower right', bbox_to_anchor=(1, 0.1))

    # --- Estilo gráfico ---
    sns.despine(ax=ax, top=True, right=True, left=True, bottom=False)
    ax.xaxis.grid(True, linestyle='--', alpha=0.7)
    ax.yaxis.grid(False)
    ax.tick_params(axis='x', length=0, labelcolor=self.cor[1])
    ax.tick_params(axis='y', length=0, labelcolor=self.cor[1])

    # --- Pequenas caixas de resumo (opcional) ---
    variacao_total = sum(val_2022) - sum(val_2010)
    pct_variacao = (variacao_total / sum(val_2010)) * 100
    texto_resumo = (
        f"Variação total: {variacao_total:+,.0f} indígenas\n"
        f"Crescimento relativo: {pct_variacao:+.2f}%"
    )

    ax.text(0.99, 0.85, texto_resumo, transform=ax.transAxes,
            fontsize=9, ha='left', va='top', color=self.cor[0],
            bbox=dict(boxstyle='round,pad=0.5', facecolor=self.cor[1],
                      alpha=0.95, edgecolor='none'))

    # --- Finalização ---
    self._adicionar_fonte()
    self._adicionar_logo(fig)
    plt.tight_layout(rect=[0, 0.05, 1, 0.93])
    plt.savefig('../reports/figures/grafico_distribuicao_detalhada_indigena.png',
                dpi=300, bbox_inches='tight')
    plt.show()
