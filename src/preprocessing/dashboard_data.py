from pathlib import Path
from typing import ClassVar

import pandas as pd


class PrepararDadosDashboard:
    """
    Constrói a camada analítica compartilhada do Estudo 5.

    A tabela fato preserva somente combinações atômicas de UF, ano,
    localização territorial e situação do domicílio. Brasil, regiões,
    totais territoriais e totais domiciliares são obtidos por agregação.
    """

    QUANTIDADE_UFS = 27
    QUANTIDADE_REGIOES = 5
    QUANTIDADE_ANOS = 2
    QUANTIDADE_LOCALIZACOES = 2
    QUANTIDADE_DOMICILIOS = 2
    QUANTIDADE_ESPERADA_FATO = 216

    ANOS: ClassVar[tuple[int, int]] = (2010, 2022)

    LOCALIZACOES: ClassVar[dict[int, dict[str, str]]] = {
        1: {
            "localizacao": "Em Terras Indígenas",
            "localizacao_curta": "TI",
            "prefixo_coluna": "TI",
        },
        2: {
            "localizacao": "Fora de Terras Indígenas",
            "localizacao_curta": "Fora TI",
            "prefixo_coluna": "Fora TI",
        },
    }

    DOMICILIOS: ClassVar[dict[int, dict[str, str]]] = {
        1: {
            "situacao_domicilio": "Urbana",
            "prefixo_coluna": "Urbano",
        },
        2: {
            "situacao_domicilio": "Rural",
            "prefixo_coluna": "Rural",
        },
    }

    COLUNAS_GEOGRAFIA_ENTRADA: ClassVar[list[str]] = [
        "CD_UF",
        "NM_UF",
        "SIGLA_UF",
        "CD_REGIAO",
        "NM_REGIAO",
    ]

    CHAVE_FATO: ClassVar[list[str]] = [
        "uf_id",
        "ano",
        "localizacao_id",
        "domicilio_id",
    ]

    def __init__(
        self,
        caminho_estados: str | Path,
        caminho_geografia: str | Path,
        caminho_pais: str | Path,
        caminho_regioes: str | Path,
        diretorio_saida: str | Path,
    ) -> None:
        self.caminho_estados = Path(caminho_estados)
        self.caminho_geografia = Path(caminho_geografia)
        self.caminho_pais = Path(caminho_pais)
        self.caminho_regioes = Path(caminho_regioes)
        self.diretorio_saida = Path(diretorio_saida)

        self.base_estados: pd.DataFrame | None = None
        self.base_geografia: pd.DataFrame | None = None
        self.base_pais: pd.DataFrame | None = None
        self.base_regioes: pd.DataFrame | None = None

        self.dim_geography: pd.DataFrame | None = None
        self.dim_year: pd.DataFrame | None = None
        self.dim_location: pd.DataFrame | None = None
        self.dim_domicile: pd.DataFrame | None = None
        self.fact_population: pd.DataFrame | None = None

    @classmethod
    def criar_com_caminhos_padrao(
        cls,
        raiz_projeto: str | Path,
    ) -> "PrepararDadosDashboard":
        """Cria o preparador com os caminhos convencionais do projeto."""

        raiz = Path(raiz_projeto)

        return cls(
            caminho_estados=(raiz / "data" / "processed" / "table" / "df_estados.csv"),
            caminho_geografia=(
                raiz / "data" / "processed" / "geo" / "gdf_estados.parquet"
            ),
            caminho_pais=(raiz / "data" / "processed" / "table" / "df_pais.csv"),
            caminho_regioes=(raiz / "data" / "processed" / "table" / "df_regioes.csv"),
            diretorio_saida=(raiz / "data" / "processed" / "dashboard"),
        )

    @classmethod
    def _coluna_atomica(
        cls,
        ano: int,
        localizacao_id: int,
        domicilio_id: int,
    ) -> str:
        """Retorna o nome da coluna de origem de uma combinação atômica."""

        localizacao = cls.LOCALIZACOES[localizacao_id]["prefixo_coluna"]
        domicilio = cls.DOMICILIOS[domicilio_id]["prefixo_coluna"]

        return f"Indígenas {ano} {localizacao} {domicilio}"

    @classmethod
    def _colunas_atomicas(cls) -> list[str]:
        """Lista as oito colunas atômicas necessárias na base estadual."""

        return [
            cls._coluna_atomica(ano, localizacao_id, domicilio_id)
            for ano in cls.ANOS
            for localizacao_id in cls.LOCALIZACOES
            for domicilio_id in cls.DOMICILIOS
        ]

    @classmethod
    def _colunas_validacao_estadual(cls) -> list[str]:
        """Lista totais estaduais utilizados nas validações de aditividade."""

        colunas: list[str] = []

        for ano in cls.ANOS:
            colunas.extend(
                [
                    f"Indígenas {ano} Total",
                    f"Indígenas {ano} Urbano",
                    f"Indígenas {ano} Rural",
                    f"Indígenas {ano} TI Total",
                    f"Indígenas {ano} Fora TI Total",
                ]
            )

        return colunas

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
        """Verifica a presença das colunas obrigatórias em uma base."""

        ausentes = [coluna for coluna in colunas if coluna not in dataframe.columns]

        if ausentes:
            raise KeyError(
                f"A base '{nome_base}' não possui as colunas obrigatórias: "
                f"{ausentes}"
            )

    @staticmethod
    def _converter_colunas_inteiras(
        dataframe: pd.DataFrame,
        colunas: list[str],
        nome_base: str,
    ) -> pd.DataFrame:
        """Converte e valida colunas demográficas como inteiros não negativos."""

        resultado = dataframe.copy()

        for coluna in colunas:
            valores = pd.to_numeric(resultado[coluna], errors="raise")

            if valores.isna().any():
                raise ValueError(
                    f"A coluna '{coluna}' da base '{nome_base}' possui nulos."
                )

            if (valores < 0).any():
                raise ValueError(
                    f"A coluna '{coluna}' da base '{nome_base}' possui "
                    "populações negativas."
                )

            if not (valores % 1 == 0).all():
                raise ValueError(
                    f"A coluna '{coluna}' da base '{nome_base}' possui "
                    "valores populacionais não inteiros."
                )

            resultado[coluna] = valores.astype("int64")

        return resultado

    def carregar_bases(self) -> dict[str, pd.DataFrame]:
        """Carrega e valida as quatro bases necessárias ao processamento."""

        caminhos = [
            self.caminho_estados,
            self.caminho_geografia,
            self.caminho_pais,
            self.caminho_regioes,
        ]

        for caminho in caminhos:
            self._validar_arquivo(caminho)

        self.base_estados = pd.read_csv(self.caminho_estados)
        self.base_geografia = pd.read_parquet(
            self.caminho_geografia,
            columns=self.COLUNAS_GEOGRAFIA_ENTRADA,
        )
        self.base_pais = pd.read_csv(self.caminho_pais)
        self.base_regioes = pd.read_csv(self.caminho_regioes)

        colunas_atomicas = self._colunas_atomicas()
        colunas_estados = [
            "Localidade",
            *colunas_atomicas,
            *self._colunas_validacao_estadual(),
        ]

        self._validar_colunas(
            self.base_estados,
            colunas_estados,
            "estados",
        )
        self._validar_colunas(
            self.base_geografia,
            self.COLUNAS_GEOGRAFIA_ENTRADA,
            "geografia",
        )
        self._validar_colunas(
            self.base_pais,
            ["Localidade", *colunas_atomicas],
            "país",
        )
        self._validar_colunas(
            self.base_regioes,
            ["Localidade", *colunas_atomicas],
            "regiões",
        )

        colunas_numericas_estados = list(
            dict.fromkeys([*colunas_atomicas, *self._colunas_validacao_estadual()])
        )

        self.base_estados = self._converter_colunas_inteiras(
            self.base_estados,
            colunas_numericas_estados,
            "estados",
        )
        self.base_pais = self._converter_colunas_inteiras(
            self.base_pais,
            colunas_atomicas,
            "país",
        )
        self.base_regioes = self._converter_colunas_inteiras(
            self.base_regioes,
            colunas_atomicas,
            "regiões",
        )

        if len(self.base_estados) != self.QUANTIDADE_UFS:
            raise ValueError(
                "A base estadual deveria possuir "
                f"{self.QUANTIDADE_UFS} registros, mas possui "
                f"{len(self.base_estados)}."
            )

        if self.base_estados["Localidade"].duplicated().any():
            raise ValueError("A base estadual possui localidades duplicadas.")

        if len(self.base_geografia) != self.QUANTIDADE_UFS:
            raise ValueError(
                "A dimensão geográfica de origem deveria possuir "
                f"{self.QUANTIDADE_UFS} registros."
            )

        if self.base_geografia["CD_UF"].duplicated().any():
            raise ValueError("A base geográfica possui códigos de UF duplicados.")

        return {
            "estados": self.base_estados,
            "geografia": self.base_geografia,
            "pais": self.base_pais,
            "regioes": self.base_regioes,
        }

    def criar_dimensoes(self) -> dict[str, pd.DataFrame]:
        """Cria as dimensões geográfica, temporal, territorial e domiciliar."""

        if self.base_geografia is None:
            raise RuntimeError("Execute carregar_bases() antes de criar dimensões.")

        geografia = self.base_geografia.rename(
            columns={
                "CD_UF": "uf_id",
                "NM_UF": "uf",
                "SIGLA_UF": "sigla_uf",
                "CD_REGIAO": "regiao_id",
                "NM_REGIAO": "regiao",
            }
        ).copy()

        geografia["uf_id"] = geografia["uf_id"].astype("string").str.zfill(2)
        geografia["regiao_id"] = pd.to_numeric(
            geografia["regiao_id"],
            errors="raise",
        ).astype("int8")
        geografia["regiao"] = geografia["regiao"].replace(
            {"Centro-oeste": "Centro-Oeste"}
        )

        ordem_ufs = {
            uf: ordem
            for ordem, uf in enumerate(
                sorted(geografia["uf"].tolist()),
                start=1,
            )
        }
        geografia["ordem_uf"] = geografia["uf"].map(ordem_ufs).astype("int16")
        geografia["ordem_regiao"] = geografia["regiao_id"].astype("int8")

        self.dim_geography = geografia[
            [
                "uf_id",
                "sigla_uf",
                "uf",
                "regiao_id",
                "regiao",
                "ordem_uf",
                "ordem_regiao",
            ]
        ].sort_values("uf_id", ignore_index=True)

        self.dim_year = pd.DataFrame(
            {
                "ano": pd.Series(self.ANOS, dtype="int16"),
                "rotulo_ano": ["Censo 2010", "Censo 2022"],
                "ordem_ano": pd.Series([1, 2], dtype="int8"),
            }
        )

        self.dim_location = pd.DataFrame(
            [
                {
                    "localizacao_id": localizacao_id,
                    "localizacao": atributos["localizacao"],
                    "localizacao_curta": atributos["localizacao_curta"],
                    "ordem_localizacao": ordem,
                }
                for ordem, (localizacao_id, atributos) in enumerate(
                    self.LOCALIZACOES.items(),
                    start=1,
                )
            ]
        ).astype(
            {
                "localizacao_id": "int8",
                "ordem_localizacao": "int8",
            }
        )

        self.dim_domicile = pd.DataFrame(
            [
                {
                    "domicilio_id": domicilio_id,
                    "situacao_domicilio": atributos["situacao_domicilio"],
                    "ordem_domicilio": ordem,
                }
                for ordem, (domicilio_id, atributos) in enumerate(
                    self.DOMICILIOS.items(),
                    start=1,
                )
            ]
        ).astype(
            {
                "domicilio_id": "int8",
                "ordem_domicilio": "int8",
            }
        )

        return {
            "dim_geography": self.dim_geography,
            "dim_year": self.dim_year,
            "dim_location": self.dim_location,
            "dim_domicile": self.dim_domicile,
        }

    def criar_tabela_fato(self) -> pd.DataFrame:
        """Transforma as oito colunas atômicas em 216 observações."""

        if self.base_estados is None or self.dim_geography is None:
            raise RuntimeError(
                "Execute carregar_bases() e criar_dimensoes() "
                "antes de criar a tabela fato."
            )

        estados = self.base_estados.merge(
            self.dim_geography[["uf_id", "uf"]],
            left_on="Localidade",
            right_on="uf",
            how="left",
            validate="one_to_one",
            indicator=True,
        )

        sem_correspondencia = estados.loc[
            estados["_merge"] != "both",
            "Localidade",
        ].tolist()

        if sem_correspondencia:
            raise ValueError(
                "As seguintes UFs não foram encontradas na dimensão "
                f"geográfica: {sem_correspondencia}"
            )

        quadros: list[pd.DataFrame] = []

        for ano in self.ANOS:
            for localizacao_id in self.LOCALIZACOES:
                for domicilio_id in self.DOMICILIOS:
                    coluna_origem = self._coluna_atomica(
                        ano,
                        localizacao_id,
                        domicilio_id,
                    )
                    quadro = estados[["uf_id", coluna_origem]].rename(
                        columns={coluna_origem: "populacao_indigena"}
                    )
                    quadro = quadro.assign(
                        ano=ano,
                        localizacao_id=localizacao_id,
                        domicilio_id=domicilio_id,
                    )
                    quadros.append(quadro)

        fato = pd.concat(quadros, ignore_index=True)
        fato = fato[
            [
                "uf_id",
                "ano",
                "localizacao_id",
                "domicilio_id",
                "populacao_indigena",
            ]
        ].astype(
            {
                "uf_id": "string",
                "ano": "int16",
                "localizacao_id": "int8",
                "domicilio_id": "int8",
                "populacao_indigena": "int64",
            }
        )

        self.fact_population = fato.sort_values(
            self.CHAVE_FATO,
            ignore_index=True,
        )

        return self.fact_population

    def validar_dimensoes(self) -> dict[str, int | bool]:
        """Valida cardinalidades e chaves das quatro dimensões."""

        if any(
            dimensao is None
            for dimensao in [
                self.dim_geography,
                self.dim_year,
                self.dim_location,
                self.dim_domicile,
            ]
        ):
            raise RuntimeError("Execute criar_dimensoes() antes da validação.")

        assert self.dim_geography is not None
        assert self.dim_year is not None
        assert self.dim_location is not None
        assert self.dim_domicile is not None

        verificacoes = {
            "ufs": len(self.dim_geography),
            "regioes": self.dim_geography["regiao_id"].nunique(),
            "anos": len(self.dim_year),
            "localizacoes": len(self.dim_location),
            "domicilios": len(self.dim_domicile),
            "uf_id_duplicado": bool(self.dim_geography["uf_id"].duplicated().any()),
        }

        dimensoes_validas = (
            verificacoes["ufs"] == self.QUANTIDADE_UFS
            and verificacoes["regioes"] == self.QUANTIDADE_REGIOES
            and verificacoes["anos"] == self.QUANTIDADE_ANOS
            and verificacoes["localizacoes"] == self.QUANTIDADE_LOCALIZACOES
            and verificacoes["domicilios"] == self.QUANTIDADE_DOMICILIOS
            and not verificacoes["uf_id_duplicado"]
        )

        if not dimensoes_validas:
            raise ValueError(f"Dimensões inconsistentes: {verificacoes}")

        return {**verificacoes, "dimensoes_validas": True}

    def validar_tabela_fato(self) -> dict[str, int | bool]:
        """Valida granularidade, completude e domínio da tabela fato."""

        if self.fact_population is None:
            raise RuntimeError("Execute criar_tabela_fato() antes da validação.")

        fato = self.fact_population
        duplicacoes = int(fato.duplicated(self.CHAVE_FATO).sum())
        valores_nulos = int(fato.isna().sum().sum())
        valores_negativos = int((fato["populacao_indigena"] < 0).sum())

        combinacoes_por_uf = fato.groupby("uf_id", observed=True).size()
        combinacoes_incompletas = int(
            (
                combinacoes_por_uf
                != (
                    self.QUANTIDADE_ANOS
                    * self.QUANTIDADE_LOCALIZACOES
                    * self.QUANTIDADE_DOMICILIOS
                )
            ).sum()
        )

        fato_valida = (
            len(fato) == self.QUANTIDADE_ESPERADA_FATO
            and fato["uf_id"].nunique() == self.QUANTIDADE_UFS
            and duplicacoes == 0
            and valores_nulos == 0
            and valores_negativos == 0
            and combinacoes_incompletas == 0
            and pd.api.types.is_integer_dtype(fato["populacao_indigena"])
        )

        resultado = {
            "linhas_fato": len(fato),
            "ufs_fato": fato["uf_id"].nunique(),
            "duplicacoes_chave": duplicacoes,
            "valores_nulos": valores_nulos,
            "valores_negativos": valores_negativos,
            "ufs_combinacoes_incompletas": combinacoes_incompletas,
            "fato_valida": fato_valida,
        }

        if not fato_valida:
            raise ValueError(f"Tabela fato inconsistente: {resultado}")

        return resultado

    def _fato_enriquecida(self) -> pd.DataFrame:
        """Acrescenta UF e região à fato exclusivamente para validação."""

        if self.fact_population is None or self.dim_geography is None:
            raise RuntimeError("A tabela fato e a dimensão geográfica são necessárias.")

        return self.fact_population.merge(
            self.dim_geography[["uf_id", "uf", "regiao"]],
            on="uf_id",
            how="left",
            validate="many_to_one",
        )

    def validar_totais_estaduais(self) -> dict[str, int | bool]:
        """Compara agregações atômicas aos totais publicados para cada UF."""

        if self.base_estados is None:
            raise RuntimeError("A base estadual é necessária para a validação.")

        fato = self._fato_enriquecida()
        divergencias: list[dict[str, int | str]] = []
        comparacoes = 0

        for _, linha in self.base_estados.iterrows():
            uf = linha["Localidade"]

            for ano in self.ANOS:
                recorte = fato.loc[(fato["uf"] == uf) & (fato["ano"] == ano)]

                observados = {
                    "Total": int(recorte["populacao_indigena"].sum()),
                    "Urbano": int(
                        recorte.loc[
                            recorte["domicilio_id"] == 1,
                            "populacao_indigena",
                        ].sum()
                    ),
                    "Rural": int(
                        recorte.loc[
                            recorte["domicilio_id"] == 2,
                            "populacao_indigena",
                        ].sum()
                    ),
                    "TI Total": int(
                        recorte.loc[
                            recorte["localizacao_id"] == 1,
                            "populacao_indigena",
                        ].sum()
                    ),
                    "Fora TI Total": int(
                        recorte.loc[
                            recorte["localizacao_id"] == 2,
                            "populacao_indigena",
                        ].sum()
                    ),
                }

                for sufixo, observado in observados.items():
                    esperado = int(linha[f"Indígenas {ano} {sufixo}"])
                    comparacoes += 1

                    if observado != esperado:
                        divergencias.append(
                            {
                                "uf": uf,
                                "ano": ano,
                                "indicador": sufixo,
                                "observado": observado,
                                "esperado": esperado,
                            }
                        )

        if divergencias:
            raise ValueError(
                "Os totais estaduais divergiram da tabela fato: " f"{divergencias[:10]}"
            )

        return {
            "comparacoes_estaduais": comparacoes,
            "divergencias_estaduais": 0,
            "totais_estaduais_validos": True,
        }

    def validar_referencias_agregadas(self) -> dict[str, int | bool]:
        """Compara Brasil e regiões agregados às tabelas oficiais processadas."""

        if self.base_pais is None or self.base_regioes is None:
            raise RuntimeError("As referências nacional e regional são necessárias.")

        fato = self._fato_enriquecida()
        divergencias: list[dict[str, int | str]] = []
        comparacoes_nacionais = 0
        comparacoes_regionais = 0

        referencia_pais = self.base_pais.iloc[0]
        referencias_regioes = self.base_regioes.set_index("Localidade")

        for ano in self.ANOS:
            for localizacao_id in self.LOCALIZACOES:
                for domicilio_id in self.DOMICILIOS:
                    coluna = self._coluna_atomica(
                        ano,
                        localizacao_id,
                        domicilio_id,
                    )
                    recorte = fato.loc[
                        (fato["ano"] == ano)
                        & (fato["localizacao_id"] == localizacao_id)
                        & (fato["domicilio_id"] == domicilio_id)
                    ]

                    observado_pais = int(recorte["populacao_indigena"].sum())
                    esperado_pais = int(referencia_pais[coluna])
                    comparacoes_nacionais += 1

                    if observado_pais != esperado_pais:
                        divergencias.append(
                            {
                                "nivel": "Brasil",
                                "indicador": coluna,
                                "observado": observado_pais,
                                "esperado": esperado_pais,
                            }
                        )

                    observados_regioes = recorte.groupby(
                        "regiao",
                        observed=True,
                    )["populacao_indigena"].sum()

                    for regiao, observado in observados_regioes.items():
                        esperado = int(referencias_regioes.loc[regiao, coluna])
                        comparacoes_regionais += 1

                        if int(observado) != esperado:
                            divergencias.append(
                                {
                                    "nivel": regiao,
                                    "indicador": coluna,
                                    "observado": int(observado),
                                    "esperado": esperado,
                                }
                            )

        if divergencias:
            raise ValueError(
                "As referências agregadas divergiram da tabela fato: "
                f"{divergencias[:10]}"
            )

        return {
            "comparacoes_nacionais": comparacoes_nacionais,
            "comparacoes_regionais": comparacoes_regionais,
            "divergencias_agregadas": 0,
            "referencias_agregadas_validas": True,
        }

    def validar_todas_bases(self) -> dict[str, int | bool]:
        """Executa todas as validações contratuais da camada analítica."""

        return {
            **self.validar_dimensoes(),
            **self.validar_tabela_fato(),
            **self.validar_totais_estaduais(),
            **self.validar_referencias_agregadas(),
        }

    def salvar_bases(self) -> dict[str, Path]:
        """Salva as tabelas nos formatos destinados a Python e Power BI."""

        if any(
            tabela is None
            for tabela in [
                self.fact_population,
                self.dim_geography,
                self.dim_year,
                self.dim_location,
                self.dim_domicile,
            ]
        ):
            raise RuntimeError("Crie a tabela fato e as dimensões antes de salvar.")

        assert self.fact_population is not None
        assert self.dim_geography is not None
        assert self.dim_year is not None
        assert self.dim_location is not None
        assert self.dim_domicile is not None

        self.diretorio_saida.mkdir(parents=True, exist_ok=True)

        caminhos = {
            "fact_population_parquet": (
                self.diretorio_saida / "fact_population.parquet"
            ),
            "fact_population_csv": self.diretorio_saida / "fact_population.csv",
            "dim_geography_parquet": (self.diretorio_saida / "dim_geography.parquet"),
            "dim_geography_csv": self.diretorio_saida / "dim_geography.csv",
            "dim_year_csv": self.diretorio_saida / "dim_year.csv",
            "dim_location_csv": self.diretorio_saida / "dim_location.csv",
            "dim_domicile_csv": self.diretorio_saida / "dim_domicile.csv",
        }

        self.fact_population.to_parquet(
            caminhos["fact_population_parquet"],
            index=False,
        )
        self.fact_population.to_csv(
            caminhos["fact_population_csv"],
            index=False,
            encoding="utf-8-sig",
        )
        self.dim_geography.to_parquet(
            caminhos["dim_geography_parquet"],
            index=False,
        )
        self.dim_geography.to_csv(
            caminhos["dim_geography_csv"],
            index=False,
            encoding="utf-8-sig",
        )
        self.dim_year.to_csv(
            caminhos["dim_year_csv"],
            index=False,
            encoding="utf-8-sig",
        )
        self.dim_location.to_csv(
            caminhos["dim_location_csv"],
            index=False,
            encoding="utf-8-sig",
        )
        self.dim_domicile.to_csv(
            caminhos["dim_domicile_csv"],
            index=False,
            encoding="utf-8-sig",
        )

        return caminhos

    def executar(self) -> tuple[dict[str, int | bool], dict[str, Path]]:
        """Executa carregamento, transformação, validação e persistência."""

        self.carregar_bases()
        self.criar_dimensoes()
        self.criar_tabela_fato()
        relatorio = self.validar_todas_bases()
        caminhos = self.salvar_bases()

        return relatorio, caminhos


def main() -> None:
    """Gera a camada tabular do dashboard a partir da raiz do projeto."""

    raiz_projeto = Path(__file__).resolve().parents[2]
    preparador = PrepararDadosDashboard.criar_com_caminhos_padrao(raiz_projeto)
    relatorio, caminhos = preparador.executar()

    print("Camada analítica do dashboard gerada com sucesso.")
    print(f"Linhas da tabela fato: {relatorio['linhas_fato']}")
    print(f"Comparações estaduais: {relatorio['comparacoes_estaduais']}")
    print(
        f"Comparações agregadas: {relatorio['comparacoes_regionais'] + relatorio['comparacoes_nacionais']}"
    )
    print("Arquivos:")

    for caminho in caminhos.values():
        print(f"- {caminho.relative_to(raiz_projeto)}")


if __name__ == "__main__":
    main()
