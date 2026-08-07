from pathlib import Path

import geopandas as gpd
import pandas as pd


class PrepararBaseGeografica:
    """
    Prepara as bases geográficas estadual e regional
    utilizadas nas análises espaciais.

    A classe integra a malha territorial oficial do IBGE
    à base analítica estadual da população indígena e,
    posteriormente, agrega os estados por Grande Região.
    """

    QUANTIDADE_UFS = 27
    QUANTIDADE_REGIOES = 5

    def __init__(
        self,
        caminho_malha: str | Path,
        caminho_base_estados: str | Path,
        coluna_malha: str = "NM_UF",
        coluna_base: str = "Localidade",
        coluna_regiao: str = "NM_REGIAO",
    ) -> None:
        self.caminho_malha = Path(caminho_malha)
        self.caminho_base_estados = Path(caminho_base_estados)

        self.coluna_malha = coluna_malha
        self.coluna_base = coluna_base
        self.coluna_regiao = coluna_regiao

        self.malha: gpd.GeoDataFrame | None = None
        self.base_estados: pd.DataFrame | None = None
        self.base_geografica: gpd.GeoDataFrame | None = None
        self.base_regional: gpd.GeoDataFrame | None = None

    def _validar_arquivo(
        self,
        caminho: Path,
    ) -> None:
        """Verifica se um arquivo de entrada existe."""

        if not caminho.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {caminho.resolve()}")

    def carregar_malha(
        self,
    ) -> gpd.GeoDataFrame:
        """Carrega a malha territorial oficial do IBGE."""

        self._validar_arquivo(self.caminho_malha)

        self.malha = gpd.read_file(self.caminho_malha)

        if self.coluna_malha not in self.malha.columns:
            raise KeyError(
                f"A coluna '{self.coluna_malha}' não existe na malha. "
                f"Colunas disponíveis: {self.malha.columns.tolist()}"
            )

        if self.coluna_regiao not in self.malha.columns:
            raise KeyError(
                f"A coluna '{self.coluna_regiao}' não existe na malha. "
                f"Colunas disponíveis: {self.malha.columns.tolist()}"
            )

        if "geometry" not in self.malha.columns:
            raise ValueError("A malha carregada não possui a coluna 'geometry'.")

        if self.malha.crs is None:
            raise ValueError(
                "A malha territorial não possui sistema de referência definido."
            )

        return self.malha

    def carregar_base_estados(
        self,
    ) -> pd.DataFrame:
        """Carrega a base estadual processada."""

        self._validar_arquivo(self.caminho_base_estados)

        self.base_estados = pd.read_csv(self.caminho_base_estados)

        if self.coluna_base not in self.base_estados.columns:
            raise KeyError(
                f"A coluna '{self.coluna_base}' não existe "
                "na base estadual. "
                f"Colunas disponíveis: "
                f"{self.base_estados.columns.tolist()}"
            )

        return self.base_estados

    def integrar_bases(
        self,
    ) -> gpd.GeoDataFrame:
        """
        Integra a malha territorial e a base estadual.

        O relacionamento é realizado entre o nome da UF
        presente na malha e a localidade correspondente
        na base demográfica processada.
        """

        if self.malha is None:
            self.carregar_malha()

        if self.base_estados is None:
            self.carregar_base_estados()

        if self.malha is None or self.base_estados is None:
            raise RuntimeError("Não foi possível carregar as bases de entrada.")

        self.base_geografica = self.malha.merge(
            self.base_estados,
            left_on=self.coluna_malha,
            right_on=self.coluna_base,
            how="left",
            validate="one_to_one",
            indicator=True,
        )

        return self.base_geografica

    def validar_integracao(
        self,
    ) -> dict[str, int | bool]:
        """
        Valida a quantidade de UFs, geometrias
        e correspondências entre as bases.
        """

        if self.base_geografica is None:
            raise RuntimeError("Execute integrar_bases() antes da validação.")

        quantidade_linhas = len(self.base_geografica)

        quantidade_ufs = self.base_geografica[self.coluna_malha].nunique()

        correspondencias_invalidas = int(
            (self.base_geografica["_merge"] != "both").sum()
        )

        geometrias_ausentes = int(self.base_geografica.geometry.isna().sum())

        geometrias_invalidas = int((~self.base_geografica.geometry.is_valid).sum())

        integracao_valida = (
            quantidade_linhas == self.QUANTIDADE_UFS
            and quantidade_ufs == self.QUANTIDADE_UFS
            and correspondencias_invalidas == 0
            and geometrias_ausentes == 0
            and geometrias_invalidas == 0
        )

        resultado = {
            "quantidade_linhas": quantidade_linhas,
            "quantidade_ufs": quantidade_ufs,
            "correspondencias_invalidas": correspondencias_invalidas,
            "geometrias_ausentes": geometrias_ausentes,
            "geometrias_invalidas": geometrias_invalidas,
            "integracao_valida": integracao_valida,
        }

        if not integracao_valida:
            raise ValueError(f"A integração apresentou inconsistências: {resultado}")

        return resultado

    def limpar_base(
        self,
    ) -> gpd.GeoDataFrame:
        """Remove colunas auxiliares utilizadas na integração."""

        if self.base_geografica is None:
            raise RuntimeError("Execute integrar_bases() antes da limpeza.")

        colunas_remover = [
            "_merge",
        ]

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

    def criar_base_regional(
        self,
        colunas_somar: list[str] | None = None,
    ) -> gpd.GeoDataFrame:
        """
        Agrega a base estadual por Grande Região.

        As geometrias das Unidades da Federação são unidas
        pelo método dissolve, enquanto as variáveis
        demográficas selecionadas são somadas.
        """

        if self.base_geografica is None:
            raise RuntimeError("Execute limpar_base() antes de criar a base regional.")

        if self.coluna_regiao not in self.base_geografica.columns:
            raise KeyError(
                f"A coluna '{self.coluna_regiao}' não existe "
                "na base geográfica estadual."
            )

        if colunas_somar is None:
            colunas_somar = [
                coluna
                for coluna in self.base_geografica.columns
                if (
                    coluna.startswith("Indígenas")
                    and pd.api.types.is_numeric_dtype(self.base_geografica[coluna])
                )
            ]

        colunas_inexistentes = [
            coluna
            for coluna in colunas_somar
            if coluna not in self.base_geografica.columns
        ]

        if colunas_inexistentes:
            raise KeyError(
                "As seguintes colunas não existem "
                "na base geográfica: "
                f"{colunas_inexistentes}"
            )

        colunas_nao_numericas = [
            coluna
            for coluna in colunas_somar
            if not pd.api.types.is_numeric_dtype(self.base_geografica[coluna])
        ]

        if colunas_nao_numericas:
            raise TypeError(
                "As seguintes colunas não são numéricas "
                "e não podem ser somadas: "
                f"{colunas_nao_numericas}"
            )

        if not colunas_somar:
            raise ValueError(
                "Nenhuma coluna numérica foi selecionada para agregação regional."
            )

        agregacoes = {coluna: "sum" for coluna in colunas_somar}

        self.base_regional = self.base_geografica.dissolve(
            by=self.coluna_regiao,
            aggfunc=agregacoes,
        ).reset_index()

        if len(self.base_regional) != self.QUANTIDADE_REGIOES:
            raise ValueError(
                "A base regional deveria possuir "
                f"{self.QUANTIDADE_REGIOES} registros, "
                f"mas foram encontrados "
                f"{len(self.base_regional)}."
            )

        if self.base_regional.geometry.isna().any():
            raise ValueError("A base regional possui geometrias ausentes.")

        if (~self.base_regional.geometry.is_valid).any():
            raise ValueError("A base regional possui geometrias inválidas.")

        return self.base_regional

    def exportar_base_estadual(
        self,
        diretorio_saida: str | Path,
        nome_arquivo: str = "gdf_estados",
        salvar_geojson: bool = True,
        salvar_parquet: bool = True,
    ) -> dict[str, Path]:
        """Exporta a base geográfica estadual."""

        if self.base_geografica is None:
            raise RuntimeError("Não existe uma base geográfica estadual para exportar.")

        diretorio_saida = Path(diretorio_saida)

        diretorio_saida.mkdir(
            parents=True,
            exist_ok=True,
        )

        arquivos_gerados: dict[str, Path] = {}

        if salvar_geojson:
            caminho_geojson = diretorio_saida / f"{nome_arquivo}.geojson"

            self.base_geografica.to_file(
                caminho_geojson,
                driver="GeoJSON",
            )

            arquivos_gerados["geojson"] = caminho_geojson

        if salvar_parquet:
            caminho_parquet = diretorio_saida / f"{nome_arquivo}.parquet"

            self.base_geografica.to_parquet(
                caminho_parquet,
                index=False,
            )

            arquivos_gerados["parquet"] = caminho_parquet

        return arquivos_gerados

    def exportar_base_regional(
        self,
        diretorio_saida: str | Path,
        nome_arquivo: str = "gdf_regioes",
        salvar_geojson: bool = True,
        salvar_parquet: bool = True,
    ) -> dict[str, Path]:
        """Exporta a base geográfica regional."""

        if self.base_regional is None:
            raise RuntimeError("Não existe uma base geográfica regional para exportar.")

        diretorio_saida = Path(diretorio_saida)

        diretorio_saida.mkdir(
            parents=True,
            exist_ok=True,
        )

        arquivos_gerados: dict[str, Path] = {}

        if salvar_geojson:
            caminho_geojson = diretorio_saida / f"{nome_arquivo}.geojson"

            self.base_regional.to_file(
                caminho_geojson,
                driver="GeoJSON",
            )

            arquivos_gerados["geojson"] = caminho_geojson

        if salvar_parquet:
            caminho_parquet = diretorio_saida / f"{nome_arquivo}.parquet"

            self.base_regional.to_parquet(
                caminho_parquet,
                index=False,
            )

            arquivos_gerados["parquet"] = caminho_parquet

        return arquivos_gerados

    def exportar(
        self,
        diretorio_saida: str | Path,
    ) -> dict[str, dict[str, Path]]:
        """
        Exporta as bases geográficas estadual e regional.

        Retorna os caminhos dos arquivos produzidos.
        """

        arquivos_estaduais = self.exportar_base_estadual(
            diretorio_saida=diretorio_saida,
        )

        arquivos_regionais = self.exportar_base_regional(
            diretorio_saida=diretorio_saida,
        )

        return {
            "estadual": arquivos_estaduais,
            "regional": arquivos_regionais,
        }

    def executar(
        self,
        diretorio_saida: str | Path | None = None,
        colunas_regionais: list[str] | None = None,
    ) -> gpd.GeoDataFrame:
        """
        Executa o fluxo completo de preparação das bases
        geográficas estadual e regional.

        Retorna a base geográfica estadual. A base regional
        permanece disponível no atributo ``base_regional``.
        """

        self.carregar_malha()
        self.carregar_base_estados()
        self.integrar_bases()
        self.validar_integracao()
        self.limpar_base()
        self.criar_base_regional(
            colunas_somar=colunas_regionais,
        )

        if diretorio_saida is not None:
            self.exportar(
                diretorio_saida=diretorio_saida,
            )

        if self.base_geografica is None:
            raise RuntimeError("A base geográfica estadual não foi gerada.")

        return self.base_geografica
