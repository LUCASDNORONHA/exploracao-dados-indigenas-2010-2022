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
        localidade = db_pais['Localidade'].values[0]

        fig, ax = plt.subplots(figsize=(10, 5))
        bars = ax.barh(anos, valores, color=self.cor, height=0.6)

        ax.xaxis.set_major_formatter(ticker.FuncFormatter(self._formatter_milhoes))

        for bar in bars:
            width = bar.get_width()
            ax.text(width * 1.02, bar.get_y() + bar.get_height()/2,
                    f"{width:,.0f}", ha='left', va='center', fontsize=12)

        ax.set_title(f'Crescimento Absoluto da População Indígena no {localidade} (2010–2022)')
        ax.set_xlabel(self.rotulo_x or 'População total')
        ax.set_ylabel(self.rotulo_y or 'Ano')

        sns.despine(top=True, right=True, left=True, bottom=False)
        ax.xaxis.grid(True, linestyle='--', alpha=0.7)
        ax.yaxis.grid(False)
        ax.tick_params(axis='y', length=0)
        ax.set_xlim(right=max(valores) * 1.20)

        texto_resumo = (
            f"Crescimento Absoluto: {int(diferenca.iloc[0])}\n"
            f"Crescimento Percentual: {float(crescimento_pct.iloc[0]):.2f}%"
        )

        ax.text(0.85, 0.40, texto_resumo,
                transform=ax.transAxes,
                fontsize=8,
                fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.5',
                          facecolor='#C6D9F1', 
                          alpha=0.8, 
                          edgecolor='none'))

        self._adicionar_fonte()
        self._adicionar_logo(fig)
        plt.tight_layout(rect=[0, 0.05, 1, 0.93])
        plt.savefig('../reports/figures/grafico_crescimento_populacao_indigena_brasil.png',
                    dpi=300, bbox_inches='tight')
        plt.show()

    # -------------------------------------------------------

    def plot_crescimento_area(self):
        db_pais = self.db[self.db['Localidade'] == 'Brasil']

        diferenca_urbano = db_pais['Indígenas 2022 Urbano'] - db_pais['Indígenas 2010 Urbano']
        diferenca_rural = db_pais['Indígenas 2022 Rural'] - db_pais['Indígenas 2010 Rural']
        crescimento_pct_urbano = (diferenca_urbano / db_pais['Indígenas 2010 Urbano']) * 100
        crescimento_pct_rural = (diferenca_rural / db_pais['Indígenas 2010 Rural']) * 100

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
            ax.text(valores_2010[i]*1.02, y_pos[i] - height/2 - gap, f"{valores_2010[i]:,.0f}",
                    va='center', ha='left', fontsize=12)
            ax.text(valores_2022[i]*1.02, y_pos[i] + height/2 + gap, f"{valores_2022[i]:,.0f}",
                    va='center', ha='left', fontsize=12)

        ax.set_yticks(y_pos)
        ax.set_yticklabels(categorias)
        ax.set_xlabel('População total')
        ax.set_ylabel('Área')
        ax.set_title(f'Crescimento da População Indígena no {localidade} (2010–2022) por Área')
        ax.xaxis.set_major_formatter(ticker.FuncFormatter(self._formatter_milhoes))

        sns.despine(ax=ax, top=True, right=True, left=True, bottom=False)
        ax.xaxis.grid(True, linestyle='--', alpha=0.7)
        ax.yaxis.grid(False)
        ax.tick_params(axis='y', length=0)
        ax.set_xlim(right=max(max(valores_2010), max(valores_2022)) * 1.25)
        ax.legend(frameon=False)

        texto_resumo = (
            f"Crescimento Urbano: {int(diferenca_urbano.iloc[0])} "
            f"({float(crescimento_pct_urbano.iloc[0]):.2f}%)\n"
            f"Crescimento Rural: {int(diferenca_rural.iloc[0])} "
            f"({float(crescimento_pct_rural.iloc[0]):.2f}%)"
        )
        ax.text(0.75, 0.15, texto_resumo, transform=ax.transAxes,
                fontsize=8, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.5',
                          facecolor='#C6D9F1', alpha=0.8, edgecolor='none'))

        self._adicionar_fonte()
        self._adicionar_logo(fig)
        plt.tight_layout(rect=[0, 0.05, 1, 0.93])
        plt.savefig('../reports/figures/grafico_crescimento_pop_indigena_area.png',
                    dpi=300, bbox_inches='tight')
        plt.show()

    # -------------------------------------------------------
    def plot_crescimento_ti(self):
        db_pais = self.db[self.db['Localidade'] == 'Brasil']

        diferenca = db_pais['Indígenas 2022 TI Total'] - db_pais['Indígenas 2010 TI Total']
        crescimento_pct = (diferenca / db_pais['Indígenas 2010 TI Total']) * 100

        anos = ['2010', '2022']
        valores = [
            db_pais['Indígenas 2010 TI Total'].values[0],
            db_pais['Indígenas 2022 TI Total'].values[0]
        ]
        localidade = db_pais['Localidade'].values[0]

        fig, ax = plt.subplots(figsize=(10, 5))
        bars = ax.barh(anos, valores, color=self.cor, height=0.6)
        ax.xaxis.set_major_formatter(ticker.FuncFormatter(self._formatter_milhoes))

        for bar in bars:
            width = bar.get_width()
            ax.text(width * 1.02, bar.get_y() + bar.get_height()/2,
                    f"{width:,.0f}", ha='left', va='center', fontsize=12)

        ax.set_title(f'Crescimento da População Indígena em Terras Indígenas ({localidade}, 2010–2022)')
        ax.set_xlabel(self.rotulo_x or 'População total')
        ax.set_ylabel(self.rotulo_y or 'Ano')

        sns.despine(top=True, right=True, left=True, bottom=False)
        ax.xaxis.grid(True, linestyle='--', alpha=0.7)
        ax.yaxis.grid(False)
        ax.tick_params(axis='y', length=0)
        ax.set_xlim(right=max(valores) * 1.20)

        texto_resumo = (
            f"Crescimento Absoluto: {int(diferenca.iloc[0])}\n"
            f"Crescimento Percentual: {float(crescimento_pct.iloc[0]):.2f}%"
        )

        ax.text(0.75, 0.40, texto_resumo, transform=ax.transAxes,
                fontsize=8, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.5',
                          facecolor='#C6D9F1', alpha=0.8, edgecolor='none'))

        self._adicionar_fonte()
        self._adicionar_logo(fig)
        plt.tight_layout(rect=[0, 0.05, 1, 0.93])
        plt.savefig('../reports/figures/grafico_crescimento_populacao_indigena_ti.png',
                    dpi=300, bbox_inches='tight')
        plt.show()
