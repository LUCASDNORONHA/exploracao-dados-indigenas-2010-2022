from pathlib import Path

import geopandas as gpd
import pandas as pd


class PrepararBaseGeografica:
    """
    Prepara a base geográfica estadual utilizada nas análises espaciais.

    A classe integra a malha territorial oficial do IBGE à base
    analítica estadual da população indígena.
    """

    QUANTIDADE_UFS = 27

    def __init__(
        self,
        caminho_malha: str | Path,
        caminho_base_estados: str | Path,
        coluna_malha: str = "NM_UF",
        coluna_base: str = "Localidade",
    ) -> None:
        self.caminho_malha = Path(caminho_malha)
        self.caminho_base_estados = Path(caminho_base_estados)

        self.coluna_malha = coluna_malha
        self.coluna_base = coluna_base

        self.malha: gpd.GeoDataFrame | None = None
        self.base_estados: pd.DataFrame | None = None
        self.base_geografica: gpd.GeoDataFrame | None = None

    def _validar_arquivo(self, caminho: Path) -> None:
        """Verifica se um arquivo de entrada existe."""

        if not caminho.exists():
            raise FileNotFoundError(
                f"Arquivo não encontrado: {caminho.resolve()}"
            )

    def carregar_malha(self) -> gpd.GeoDataFrame:
        """Carrega a malha territorial oficial do IBGE."""

        self._validar_arquivo(self.caminho_malha)

        self.malha = gpd.read_file(self.caminho_malha)

        if self.coluna_malha not in self.malha.columns:
            raise KeyError(
                f"A coluna '{self.coluna_malha}' não existe na malha. "
                f"Colunas disponíveis: {self.malha.columns.tolist()}"
            )

        if "geometry" not in self.malha.columns:
            raise ValueError(
                "A malha carregada não possui a coluna 'geometry'."
            )

        return self.malha

    def carregar_base_estados(self) -> pd.DataFrame:
        """Carrega a base estadual processada."""

        self._validar_arquivo(self.caminho_base_estados)

        self.base_estados = pd.read_csv(
            self.caminho_base_estados
        )

        if self.coluna_base not in self.base_estados.columns:
            raise KeyError(
                f"A coluna '{self.coluna_base}' não existe na base estadual. "
                f"Colunas disponíveis: "
                f"{self.base_estados.columns.tolist()}"
            )

        return self.base_estados

    def integrar_bases(self) -> gpd.GeoDataFrame:
        """
        Integra a malha territorial e a base estadual.

        O relacionamento é realizado entre o nome da UF na malha
        e a localidade correspondente na base processada.
        """

        if self.malha is None:
            self.carregar_malha()

        if self.base_estados is None:
            self.carregar_base_estados()

        self.base_geografica = self.malha.merge(
            self.base_estados,
            left_on=self.coluna_malha,
            right_on=self.coluna_base,
            how="left",
            validate="one_to_one",
            indicator=True,
        )

        return self.base_geografica

    def validar_integracao(self) -> dict[str, int | bool]:
        """Valida a quantidade de UFs, geometrias e correspondências."""

        if self.base_geografica is None:
            raise RuntimeError(
                "Execute integrar_bases() antes da validação."
            )

        quantidade_linhas = len(self.base_geografica)
        quantidade_ufs = self.base_geografica[
            self.coluna_malha
        ].nunique()

        correspondencias_invalidas = int(
            (
                self.base_geografica["_merge"]
                != "both"
            ).sum()
        )

        geometrias_ausentes = int(
            self.base_geografica.geometry.isna().sum()
        )

        geometrias_invalidas = int(
            (~self.base_geografica.geometry.is_valid).sum()
        )

        resultado = {
            "quantidade_linhas": quantidade_linhas,
            "quantidade_ufs": quantidade_ufs,
            "correspondencias_invalidas": correspondencias_invalidas,
            "geometrias_ausentes": geometrias_ausentes,
            "geometrias_invalidas": geometrias_invalidas,
            "integracao_valida": (
                quantidade_linhas == self.QUANTIDADE_UFS
                and quantidade_ufs == self.QUANTIDADE_UFS
                and correspondencias_invalidas == 0
                and geometrias_ausentes == 0
                and geometrias_invalidas == 0
            ),
        }

        if not resultado["integracao_valida"]:
            raise ValueError(
                "A integração apresentou inconsistências: "
                f"{resultado}"
            )

        return resultado

    def limpar_base(self) -> gpd.GeoDataFrame:
        """Remove colunas auxiliares utilizadas na integração."""

        if self.base_geografica is None:
            raise RuntimeError(
                "Execute integrar_bases() antes da limpeza."
            )

        colunas_remover = ["_merge"]

        if self.coluna_base != self.coluna_malha:
            colunas_remover.append(self.coluna_base)

        self.base_geografica = self.base_geografica.drop(
            columns=[
                coluna
                for coluna in colunas_remover
                if coluna in self.base_geografica.columns
            ]
        )

        return self.base_geografica

    def exportar(
        self,
        diretorio_saida: str | Path,
        nome_arquivo: str = "db_estados_geo",
        salvar_geojson: bool = True,
        salvar_parquet: bool = True,
    ) -> dict[str, Path]:
        """Exporta a base geográfica nos formatos selecionados."""

        if self.base_geografica is None:
            raise RuntimeError(
                "Não existe uma base geográfica para exportar."
            )

        diretorio_saida = Path(diretorio_saida)
        diretorio_saida.mkdir(
            parents=True,
            exist_ok=True,
        )

        arquivos_gerados: dict[str, Path] = {}

        if salvar_geojson:
            caminho_geojson = (
                diretorio_saida
                / f"{nome_arquivo}.geojson"
            )

            self.base_geografica.to_file(
                caminho_geojson,
                driver="GeoJSON",
            )

            arquivos_gerados["geojson"] = caminho_geojson

        if salvar_parquet:
            caminho_parquet = (
                diretorio_saida
                / f"{nome_arquivo}.parquet"
            )

            self.base_geografica.to_parquet(
                caminho_parquet,
                index=False,
            )

            arquivos_gerados["parquet"] = caminho_parquet

        return arquivos_gerados

    def executar(
        self,
        diretorio_saida: str | Path | None = None,
    ) -> gpd.GeoDataFrame:
        """
        Executa o fluxo completo de preparação da base geográfica.
        """

        self.carregar_malha()
        self.carregar_base_estados()
        self.integrar_bases()
        self.validar_integracao()
        self.limpar_base()

        if diretorio_saida is not None:
            self.exportar(diretorio_saida)

        return self.base_geografica