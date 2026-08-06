from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd

class PainelSinteseRegional:
    """Painel executivo de síntese regional."""

    def __init__(self, gdf: pd.DataFrame, diretorio_saida: str | Path):
        self.gdf = gdf.copy()
        self.diretorio_saida = Path(diretorio_saida)
        self.cor_urbano="#8FB7CF"
        self.cor_rural="#2D5A80"
        self.cor_texto="#222222"
        self.cor_borda="#D9D9D9"
        self.cor_fundo="#F8F9FA"

    def _preparar_dados(self):
        dados={}
        for _,r in self.gdf.iterrows():
            dados[r["NM_REGIAO"]] = {
                "ti_u": r["Indígenas 2022 TI Urbano"]/r["Indígenas 2022 TI Total"]*100,
                "ti_r": r["Indígenas 2022 TI Rural"]/r["Indígenas 2022 TI Total"]*100,
                "fo_u": r["Indígenas 2022 Fora TI Urbano"]/r["Indígenas 2022 Fora TI Total"]*100,
                "fo_r": r["Indígenas 2022 Fora TI Rural"]/r["Indígenas 2022 Fora TI Total"]*100,
            }
        return dados

    def _barra(self, ax, y, urbano, rural, destaque):
        ax.add_patch(patches.Rectangle((0,y),urbano,0.10,color=self.cor_urbano))
        ax.add_patch(patches.Rectangle((urbano,y),rural,0.10,color=self.cor_rural))
        if destaque=="rural":
            ax.text(urbano+rural/2,y+0.05,f"{rural:.1f}%",ha="center",va="center",fontsize=8,color="white",fontweight="bold")
        else:
            ax.text(urbano/2,y+0.05,f"{urbano:.1f}%",ha="center",va="center",fontsize=8,color=self.cor_rural,fontweight="bold")

    def _painel(self, ax, regiao, d):
        ax.set_xlim(0,100); ax.set_ylim(0,1); ax.axis("off")
        ax.text(0,.96,regiao.upper(),fontsize=11,fontweight="bold",color=self.cor_texto)
        ax.plot([0,100],[.91,.91],color=self.cor_borda,lw=1)
        ax.text(0,.76,"Terras Indígenas",fontsize=8.5,color="#666")
        self._barra(ax,.62,d["ti_u"],d["ti_r"],"rural")
        ax.text(0,.38,"Fora de Terras Indígenas",fontsize=8.5,color="#666")
        self._barra(ax,.24,d["fo_u"],d["fo_r"],"urbano")

    def plot(self):
        dados=self._preparar_dados()
        fig=plt.figure(figsize=(15,12))
        fig.suptitle("O perfil de residência da população indígena varia conforme o contexto territorial",
                     x=.05,ha="left",fontsize=18,fontweight="bold")
        fig.text(.05,.945,"Comparação entre Terras Indígenas e áreas externas por Grande Região — Censo Demográfico 2022",
                 fontsize=11,color="#555")
        pos={"Norte":[.05,.69,.40,.18],"Nordeste":[.55,.69,.40,.18],
             "Centro-oeste":[.05,.44,.40,.18],"Sudeste":[.55,.44,.40,.18],
             "Resumo":[.05,.19,.40,.18],"Sul":[.55,.19,.40,.18],
             "Sintese":[.05,.03,.90,.11]}
        for reg in ["Norte","Nordeste","Centro-oeste","Sudeste","Sul"]:
            self._painel(fig.add_axes(pos[reg]),reg,dados[reg])
        ax=fig.add_axes(pos["Resumo"]); ax.axis("off")
        ax.text(0,1,"RESUMO EXECUTIVO",fontsize=12,fontweight="bold")
        ax.text(0,.82,
                "• Em Terras Indígenas predominou a população residente em áreas rurais\n\n"
                "• Fora de Terras Indígenas predominou a população residente em áreas urbanas\n\n"
                "• O padrão repetiu-se nas cinco Grandes Regiões.",
                fontsize=10,va="top",
                bbox=dict(facecolor=self.cor_fundo,edgecolor=self.cor_borda,boxstyle="round,pad=.6"))
        ax=fig.add_axes(pos["Sintese"]); ax.axis("off")
        ax.text(0,1,"SÍNTESE DA ANÁLISE",fontsize=12,fontweight="bold")
        ax.text(0,.72,
                "Em todas as Grandes Regiões observou-se predominância rural nas Terras Indígenas "
                "e predominância urbana fora delas.",
                fontsize=10,va="top",
                bbox=dict(facecolor=self.cor_fundo,edgecolor=self.cor_borda,boxstyle="round,pad=.8"))
        self.diretorio_saida.mkdir(parents=True,exist_ok=True)
        fig.savefig(self.diretorio_saida/"grafico_sintese_regional.png",dpi=300,bbox_inches="tight")
        plt.close(fig)