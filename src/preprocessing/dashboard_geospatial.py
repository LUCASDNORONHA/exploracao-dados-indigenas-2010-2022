from pathlib import Path
from typing import ClassVar

import geopandas as gpd
import pandas as pd
import shapely


class PrepararGeometriasDashboard:
    """
    Produz geometrias leves e topologicamente coerentes para o dashboard.

    As UFs são tratadas como uma cobertura: suas fronteiras compartilhadas
    são simplificadas conjuntamente. As regiões são dissolvidas a partir das
    UFs simplificadas, preservando a correspondência entre os dois níveis.
    """

    QUANTIDADE_UFS = 27
    QUANTIDADE_REGIOES = 5

    CRS_METRICO = 5880
    CRS_WEB = 4326

    PRECISAO_METRICA_M = 1.0
    TOLERANCIA_SIMPLIFICACAO_M = 2_000.0
    PRECISAO_COORDENADAS_GRAUS = 0.000001

    REDUCAO_MINIMA_COORDENADAS_PCT = 98.0
    ERRO_MAXIMO_AREA_ESTADUAL_PCT = 0.5
    ERRO_MAXIMO_AREA_REGIONAL_PCT = 0.1
    TAMANHO_MAXIMO_ARQUIVO_MB = 2.0

    COLUNAS_DIMENSAO: ClassVar[list[str]] = [
        "uf_id",
        "sigla_uf",
        "uf",
        "regiao_id",
        "regiao",
        "ordem_uf",
        "ordem_regiao",
    ]

    COLUNAS_ESTADOS_SAIDA: ClassVar[list[str]] = [
        *COLUNAS_DIMENSAO,
        "geometry",
    ]

    COLUNAS_REGIOES_SAIDA: ClassVar[list[str]] = [
        "regiao_id",
        "regiao",
        "ordem_regiao",
        "geometry",
    ]

    TIPOS_GEOMETRIA_PERMITIDOS: ClassVar[set[str]] = {
        "Polygon",
        "MultiPolygon",
    }

    def __init__(
        self,
        caminho_estados: str | Path,
        caminho_dim_geography: str | Path,
        diretorio_saida: str | Path,
    ) -> None:
        self.caminho_estados = Path(caminho_estados)
        self.caminho_dim_geography = Path(caminho_dim_geography)
        self.diretorio_saida = Path(diretorio_saida)

        self.estados_originais: gpd.GeoDataFrame | None = None
        self.estados_metricos_originais: gpd.GeoDataFrame | None = None
        self.estados_metricos_simplificados: gpd.GeoDataFrame | None = None
        self.estados_web: gpd.GeoDataFrame | None = None

        self.regioes_metricas_originais: gpd.GeoDataFrame | None = None
        self.regioes_metricas_simplificadas: gpd.GeoDataFrame | None = None
        self.regioes_web: gpd.GeoDataFrame | None = None

    @classmethod
    def criar_com_caminhos_padrao(
        cls,
        raiz_projeto: str | Path,
    ) -> "PrepararGeometriasDashboard":
        """Cria o preparador com os caminhos convencionais do projeto."""

        raiz = Path(raiz_projeto)

        return cls(
            caminho_estados=(
                raiz / "data" / "processed" / "geo" / "gdf_estados.parquet"
            ),
            caminho_dim_geography=(
                raiz / "data" / "processed" / "dashboard" / "dim_geography.parquet"
            ),
            diretorio_saida=(raiz / "data" / "processed" / "dashboard"),
        )

    @staticmethod
    def _validar_arquivo(caminho: Path) -> None:
        """Verifica se um arquivo de entrada existe."""

        if not caminho.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {caminho.resolve()}")

    @staticmethod
    def _validar_colunas(
        dataframe: pd.DataFrame,
        colunas: list[str],
        nome_base: str,
    ) -> None:
        """Verifica a presença das colunas obrigatórias."""

        ausentes = [coluna for coluna in colunas if coluna not in dataframe.columns]

        if ausentes:
            raise KeyError(
                f"A base '{nome_base}' não possui as colunas obrigatórias: "
                f"{ausentes}"
            )

    @staticmethod
    def _contar_coordenadas(dataframe: gpd.GeoDataFrame) -> int:
        """Conta todas as coordenadas armazenadas nas geometrias."""

        return int(shapely.get_num_coordinates(dataframe.geometry.array).sum())

    @staticmethod
    def _erro_area_percentual(
        original: gpd.GeoDataFrame,
        simplificado: gpd.GeoDataFrame,
        chave: str,
    ) -> pd.Series:
        """Calcula a distorção absoluta de área por unidade territorial."""

        areas_originais = original.set_index(chave).geometry.area
        areas_simplificadas = simplificado.set_index(chave).geometry.area

        return (areas_simplificadas - areas_originais).abs() / areas_originais * 100

    @classmethod
    def _validar_geometrias(
        cls,
        dataframe: gpd.GeoDataFrame,
        nome_base: str,
    ) -> None:
        """Valida presença, domínio e integridade geométrica."""

        if dataframe.crs is None:
            raise ValueError(f"A base '{nome_base}' não possui CRS definido.")

        if dataframe.geometry.isna().any():
            raise ValueError(f"A base '{nome_base}' possui geometrias ausentes.")

        if dataframe.geometry.is_empty.any():
            raise ValueError(f"A base '{nome_base}' possui geometrias vazias.")

        if not dataframe.geometry.is_valid.all():
            invalidas = dataframe.loc[
                ~dataframe.geometry.is_valid,
                dataframe.columns.difference(["geometry"]),
            ].to_dict("records")
            raise ValueError(
                f"A base '{nome_base}' possui geometrias inválidas: " f"{invalidas[:5]}"
            )

        tipos = set(dataframe.geometry.geom_type.unique())
        tipos_invalidos = tipos - cls.TIPOS_GEOMETRIA_PERMITIDOS

        if tipos_invalidos:
            raise ValueError(
                f"A base '{nome_base}' possui tipos geométricos inválidos: "
                f"{sorted(tipos_invalidos)}"
            )

    def carregar_bases(self) -> gpd.GeoDataFrame:
        """Carrega a malha estadual e incorpora os atributos canônicos."""

        self._validar_arquivo(self.caminho_estados)
        self._validar_arquivo(self.caminho_dim_geography)

        estados = gpd.read_parquet(self.caminho_estados)[["CD_UF", "geometry"]].rename(
            columns={"CD_UF": "uf_id"}
        )
        dimensao = pd.read_parquet(self.caminho_dim_geography)

        self._validar_colunas(estados, ["uf_id", "geometry"], "estados")
        self._validar_colunas(
            dimensao,
            self.COLUNAS_DIMENSAO,
            "dim_geography",
        )

        estados["uf_id"] = estados["uf_id"].astype("string").str.zfill(2)
        dimensao = dimensao[self.COLUNAS_DIMENSAO].copy()
        dimensao["uf_id"] = dimensao["uf_id"].astype("string").str.zfill(2)

        estados = estados.merge(
            dimensao,
            on="uf_id",
            how="left",
            validate="one_to_one",
            indicator=True,
        )

        sem_correspondencia = estados.loc[
            estados["_merge"] != "both",
            "uf_id",
        ].tolist()

        if sem_correspondencia:
            raise ValueError(
                "As seguintes UFs não foram encontradas em "
                f"dim_geography: {sem_correspondencia}"
            )

        estados = estados.drop(columns="_merge")
        self.estados_originais = gpd.GeoDataFrame(
            estados[self.COLUNAS_ESTADOS_SAIDA],
            geometry="geometry",
            crs=estados.crs,
        ).sort_values("uf_id", ignore_index=True)

        return self.estados_originais

    def validar_entrada(self) -> dict[str, int | bool]:
        """Valida a malha original antes da simplificação."""

        if self.estados_originais is None:
            raise RuntimeError("Execute carregar_bases() antes da validação.")

        self._validar_geometrias(self.estados_originais, "estados_originais")

        quantidade_ufs = len(self.estados_originais)
        ids_unicos = self.estados_originais["uf_id"].nunique()
        regioes = self.estados_originais["regiao_id"].nunique()

        entrada_valida = (
            quantidade_ufs == self.QUANTIDADE_UFS
            and ids_unicos == self.QUANTIDADE_UFS
            and regioes == self.QUANTIDADE_REGIOES
        )

        resultado = {
            "ufs_entrada": quantidade_ufs,
            "ufs_ids_unicos": ids_unicos,
            "regioes_entrada": regioes,
            "entrada_valida": entrada_valida,
        }

        if not entrada_valida:
            raise ValueError(f"Malha estadual de entrada inconsistente: {resultado}")

        return resultado

    def simplificar_estados(self) -> gpd.GeoDataFrame:
        """Simplifica conjuntamente as fronteiras compartilhadas das UFs."""

        if self.estados_originais is None:
            raise RuntimeError("Execute carregar_bases() antes da simplificação.")

        originais = self.estados_originais.to_crs(self.CRS_METRICO)
        cobertura = originais.copy()
        cobertura.geometry = cobertura.geometry.set_precision(self.PRECISAO_METRICA_M)

        self._validar_geometrias(cobertura, "estados_ajustados")

        if not cobertura.geometry.is_valid_coverage():
            raise ValueError(
                "A malha estadual não formou uma cobertura válida após "
                "o ajuste de precisão."
            )

        simplificados = cobertura.copy()
        simplificados.geometry = cobertura.geometry.simplify_coverage(
            self.TOLERANCIA_SIMPLIFICACAO_M
        )

        self._validar_geometrias(simplificados, "estados_simplificados")

        if not simplificados.geometry.is_valid_coverage():
            raise ValueError(
                "As UFs deixaram de formar uma cobertura válida após "
                "a simplificação."
            )

        self.estados_metricos_originais = originais
        self.estados_metricos_simplificados = simplificados
        self.estados_web = simplificados.to_crs(self.CRS_WEB)
        self.estados_web.geometry = self.estados_web.geometry.set_precision(
            self.PRECISAO_COORDENADAS_GRAUS
        )
        self.estados_web = self.estados_web.sort_values(
            "uf_id",
            ignore_index=True,
        )

        return self.estados_web

    def criar_regioes(self) -> gpd.GeoDataFrame:
        """Dissolve as UFs originais e simplificadas em cinco regiões."""

        if (
            self.estados_metricos_originais is None
            or self.estados_metricos_simplificados is None
        ):
            raise RuntimeError("Execute simplificar_estados() antes das regiões.")

        colunas = ["regiao_id", "regiao", "ordem_regiao", "geometry"]
        agrupamento = ["regiao_id", "regiao", "ordem_regiao"]

        regioes_originais = self.estados_metricos_originais[colunas].dissolve(
            by=agrupamento,
            as_index=False,
        )
        regioes_simplificadas = self.estados_metricos_simplificados[colunas].dissolve(
            by=agrupamento,
            as_index=False,
        )

        self._validar_geometrias(regioes_originais, "regioes_originais")
        self._validar_geometrias(
            regioes_simplificadas,
            "regioes_simplificadas",
        )

        if not regioes_simplificadas.geometry.is_valid_coverage():
            raise ValueError(
                "As regiões simplificadas não formam uma cobertura válida."
            )

        self.regioes_metricas_originais = regioes_originais.sort_values(
            "regiao_id",
            ignore_index=True,
        )
        self.regioes_metricas_simplificadas = regioes_simplificadas.sort_values(
            "regiao_id",
            ignore_index=True,
        )
        self.regioes_web = self.regioes_metricas_simplificadas.to_crs(self.CRS_WEB)
        self.regioes_web.geometry = self.regioes_web.geometry.set_precision(
            self.PRECISAO_COORDENADAS_GRAUS
        )

        return self.regioes_web

    def validar_resultados(self) -> dict[str, int | float | bool]:
        """Avalia redução, área, topologia e correspondência territorial."""

        if any(
            dataframe is None
            for dataframe in [
                self.estados_metricos_originais,
                self.estados_metricos_simplificados,
                self.estados_web,
                self.regioes_metricas_originais,
                self.regioes_metricas_simplificadas,
                self.regioes_web,
            ]
        ):
            raise RuntimeError(
                "Execute simplificar_estados() e criar_regioes() " "antes da validação."
            )

        assert self.estados_metricos_originais is not None
        assert self.estados_metricos_simplificados is not None
        assert self.estados_web is not None
        assert self.regioes_metricas_originais is not None
        assert self.regioes_metricas_simplificadas is not None
        assert self.regioes_web is not None

        self._validar_geometrias(self.estados_web, "estados_web")
        self._validar_geometrias(self.regioes_web, "regioes_web")

        coordenadas_originais = self._contar_coordenadas(
            self.estados_metricos_originais
        )
        coordenadas_simplificadas = self._contar_coordenadas(
            self.estados_metricos_simplificados
        )
        reducao = (1 - coordenadas_simplificadas / coordenadas_originais) * 100

        erro_estados = self._erro_area_percentual(
            self.estados_metricos_originais,
            self.estados_metricos_simplificados,
            "uf_id",
        )
        erro_regioes = self._erro_area_percentual(
            self.regioes_metricas_originais,
            self.regioes_metricas_simplificadas,
            "regiao_id",
        )

        resultado = {
            "ufs_saida": len(self.estados_web),
            "regioes_saida": len(self.regioes_web),
            "coordenadas_originais": coordenadas_originais,
            "coordenadas_simplificadas": coordenadas_simplificadas,
            "reducao_coordenadas_pct": round(float(reducao), 4),
            "erro_maximo_area_estadual_pct": round(
                float(erro_estados.max()),
                6,
            ),
            "erro_medio_area_estadual_pct": round(
                float(erro_estados.mean()),
                6,
            ),
            "erro_maximo_area_regional_pct": round(
                float(erro_regioes.max()),
                6,
            ),
            "erro_medio_area_regional_pct": round(
                float(erro_regioes.mean()),
                6,
            ),
            "cobertura_estadual_valida": bool(
                self.estados_web.geometry.is_valid_coverage()
            ),
            "cobertura_regional_valida": bool(
                self.regioes_web.geometry.is_valid_coverage()
            ),
            "crs_web_valido": (
                self.estados_web.crs is not None
                and self.regioes_web.crs is not None
                and self.estados_web.crs.to_epsg() == self.CRS_WEB
                and self.regioes_web.crs.to_epsg() == self.CRS_WEB
            ),
        }

        resultados_validos = (
            resultado["ufs_saida"] == self.QUANTIDADE_UFS
            and resultado["regioes_saida"] == self.QUANTIDADE_REGIOES
            and (
                resultado["reducao_coordenadas_pct"]
                >= self.REDUCAO_MINIMA_COORDENADAS_PCT
            )
            and (
                resultado["erro_maximo_area_estadual_pct"]
                <= self.ERRO_MAXIMO_AREA_ESTADUAL_PCT
            )
            and (
                resultado["erro_maximo_area_regional_pct"]
                <= self.ERRO_MAXIMO_AREA_REGIONAL_PCT
            )
            and resultado["cobertura_estadual_valida"]
            and resultado["cobertura_regional_valida"]
            and resultado["crs_web_valido"]
        )

        resultado["resultados_validos"] = bool(resultados_validos)

        if not resultados_validos:
            raise ValueError(
                "As geometrias simplificadas não atenderam ao contrato: " f"{resultado}"
            )

        return resultado

    @staticmethod
    def _salvar_geojson(
        dataframe: gpd.GeoDataFrame,
        caminho: Path,
    ) -> None:
        """Salva um GeoJSON compacto, sem índice e em UTF-8."""

        conteudo = dataframe.to_json(
            drop_id=True,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        caminho.write_text(conteudo, encoding="utf-8")

    def salvar_geometrias(self) -> dict[str, Path]:
        """Persiste as geometrias estaduais e regionais otimizadas."""

        if self.estados_web is None or self.regioes_web is None:
            raise RuntimeError("Crie e valide as geometrias antes de salvar.")

        self.diretorio_saida.mkdir(parents=True, exist_ok=True)

        caminhos = {
            "states_web": self.diretorio_saida / "states_web.geojson",
            "regions_web": self.diretorio_saida / "regions_web.geojson",
        }

        self._salvar_geojson(self.estados_web, caminhos["states_web"])
        self._salvar_geojson(self.regioes_web, caminhos["regions_web"])

        return caminhos

    def validar_arquivos_salvos(
        self,
        caminhos: dict[str, Path],
    ) -> dict[str, int | float | bool]:
        """Relê os GeoJSON e verifica sua integridade após a serialização."""

        estados = gpd.read_file(caminhos["states_web"])
        regioes = gpd.read_file(caminhos["regions_web"])

        self._validar_geometrias(estados, "states_web.geojson")
        self._validar_geometrias(regioes, "regions_web.geojson")

        tamanho_estados = caminhos["states_web"].stat().st_size / 1024 / 1024
        tamanho_regioes = caminhos["regions_web"].stat().st_size / 1024 / 1024

        arquivos_validos = (
            len(estados) == self.QUANTIDADE_UFS
            and len(regioes) == self.QUANTIDADE_REGIOES
            and estados["uf_id"].nunique() == self.QUANTIDADE_UFS
            and regioes["regiao_id"].nunique() == self.QUANTIDADE_REGIOES
            and estados.crs is not None
            and regioes.crs is not None
            and estados.crs.to_epsg() == self.CRS_WEB
            and regioes.crs.to_epsg() == self.CRS_WEB
            and estados.geometry.is_valid_coverage()
            and regioes.geometry.is_valid_coverage()
            and tamanho_estados <= self.TAMANHO_MAXIMO_ARQUIVO_MB
            and tamanho_regioes <= self.TAMANHO_MAXIMO_ARQUIVO_MB
        )

        resultado = {
            "tamanho_states_web_mb": round(tamanho_estados, 4),
            "tamanho_regions_web_mb": round(tamanho_regioes, 4),
            "ufs_persistidas": len(estados),
            "regioes_persistidas": len(regioes),
            "arquivos_geojson_validos": bool(arquivos_validos),
        }

        if not arquivos_validos:
            raise ValueError(f"GeoJSON persistidos inconsistentes: {resultado}")

        return resultado

    def executar(
        self,
    ) -> tuple[dict[str, int | float | bool], dict[str, Path]]:
        """Executa carregamento, simplificação, validação e persistência."""

        self.carregar_bases()
        relatorio_entrada = self.validar_entrada()
        self.simplificar_estados()
        self.criar_regioes()
        relatorio_resultados = self.validar_resultados()
        caminhos = self.salvar_geometrias()
        relatorio_arquivos = self.validar_arquivos_salvos(caminhos)

        relatorio = {
            **relatorio_entrada,
            **relatorio_resultados,
            **relatorio_arquivos,
        }

        return relatorio, caminhos


def main() -> None:
    """Gera as geometrias web a partir da raiz do projeto."""

    raiz_projeto = Path(__file__).resolve().parents[2]
    preparador = PrepararGeometriasDashboard.criar_com_caminhos_padrao(raiz_projeto)
    relatorio, caminhos = preparador.executar()

    print("Geometrias do dashboard geradas com sucesso.")
    print(f"UFs: {relatorio['ufs_saida']}")
    print(f"Regiões: {relatorio['regioes_saida']}")
    print("Redução de coordenadas: " f"{relatorio['reducao_coordenadas_pct']:.2f}%")
    print(
        "Erro máximo de área estadual: "
        f"{relatorio['erro_maximo_area_estadual_pct']:.4f}%"
    )
    print(
        "Tamanho combinado: "
        f"{relatorio['tamanho_states_web_mb'] + relatorio['tamanho_regions_web_mb']:.3f} MB"
    )
    print("Arquivos:")

    for caminho in caminhos.values():
        print(f"- {caminho.relative_to(raiz_projeto)}")


if __name__ == "__main__":
    main()
