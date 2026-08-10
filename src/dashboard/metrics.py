"""Cálculos compartilhados e independentes da camada de interface."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import pandas as pd

ANOS = (2010, 2022)
LOCALIZACOES = (1, 2)
DOMICILIOS = (1, 2)


@dataclass(frozen=True)
class IndicadoresVisaoGeral:
    """Indicadores centrais da página de visão geral."""

    populacao_2010: int
    populacao_2022: int
    crescimento_absoluto: int
    crescimento_relativo: float | None
    proporcao_urbana_2022: float
    proporcao_ti_2022: float


def _normalizar_ids(
    valores: Iterable[int],
    dominio: tuple[int, ...],
    nome: str,
) -> tuple[int, ...]:
    """Normaliza e valida uma seleção de categorias."""

    ids = tuple(dict.fromkeys(int(valor) for valor in valores))

    if not ids:
        raise ValueError(f"O filtro '{nome}' não pode ser vazio.")

    invalidos = set(ids) - set(dominio)

    if invalidos:
        raise ValueError(
            f"O filtro '{nome}' contém identificadores inválidos: "
            f"{sorted(invalidos)}"
        )

    return ids


def filtrar_fato(
    fato: pd.DataFrame,
    localizacao_ids: Iterable[int] = LOCALIZACOES,
    domicilio_ids: Iterable[int] = DOMICILIOS,
) -> pd.DataFrame:
    """Aplica os filtros territoriais e domiciliares à tabela fato."""

    localizacoes = _normalizar_ids(
        localizacao_ids,
        LOCALIZACOES,
        "localização",
    )
    domicilios = _normalizar_ids(
        domicilio_ids,
        DOMICILIOS,
        "domicílio",
    )

    return fato.loc[
        fato["localizacao_id"].isin(localizacoes)
        & fato["domicilio_id"].isin(domicilios)
    ].copy()


def serie_populacao_por_ano(fato: pd.DataFrame) -> pd.DataFrame:
    """Agrega a população para os dois pontos censitários."""

    serie = (
        fato.groupby("ano", as_index=False, observed=True)["populacao_indigena"]
        .sum()
        .set_index("ano")
        .reindex(ANOS, fill_value=0)
        .rename_axis("ano")
        .reset_index()
    )
    serie["ano"] = serie["ano"].astype(int)
    serie["populacao_indigena"] = serie["populacao_indigena"].astype(int)

    return serie


def _proporcao(
    fato: pd.DataFrame,
    coluna: str,
    categoria: int,
    ano: int = 2022,
) -> float:
    """Calcula a participação de uma categoria em seu universo completo."""

    recorte = fato.loc[fato["ano"] == ano]
    total = int(recorte["populacao_indigena"].sum())

    if total == 0:
        return 0.0

    numerador = int(
        recorte.loc[
            recorte[coluna] == categoria,
            "populacao_indigena",
        ].sum()
    )

    return numerador / total


def calcular_indicadores_visao_geral(
    fato: pd.DataFrame,
    localizacao_ids: Iterable[int] = LOCALIZACOES,
    domicilio_ids: Iterable[int] = DOMICILIOS,
) -> IndicadoresVisaoGeral:
    """Calcula os KPIs, preservando denominadores analiticamente úteis.

    Os totais respeitam ambos os filtros. A parcela urbana preserva as duas
    situações do domicílio e respeita apenas a localização selecionada. A
    parcela em TI preserva as duas localizações e respeita apenas a situação
    do domicílio selecionada. Assim, os indicadores de composição não se
    tornam tautologicamente 0% ou 100%.
    """

    localizacoes = _normalizar_ids(
        localizacao_ids,
        LOCALIZACOES,
        "localização",
    )
    domicilios = _normalizar_ids(
        domicilio_ids,
        DOMICILIOS,
        "domicílio",
    )

    fato_selecionado = filtrar_fato(fato, localizacoes, domicilios)
    serie = serie_populacao_por_ano(fato_selecionado).set_index("ano")
    populacao_2010 = int(serie.loc[2010, "populacao_indigena"])
    populacao_2022 = int(serie.loc[2022, "populacao_indigena"])
    crescimento_absoluto = populacao_2022 - populacao_2010
    crescimento_relativo = (
        crescimento_absoluto / populacao_2010 if populacao_2010 != 0 else None
    )

    base_domiciliar = filtrar_fato(fato, localizacoes, DOMICILIOS)
    base_territorial = filtrar_fato(fato, LOCALIZACOES, domicilios)

    return IndicadoresVisaoGeral(
        populacao_2010=populacao_2010,
        populacao_2022=populacao_2022,
        crescimento_absoluto=crescimento_absoluto,
        crescimento_relativo=crescimento_relativo,
        proporcao_urbana_2022=_proporcao(
            base_domiciliar,
            "domicilio_id",
            1,
        ),
        proporcao_ti_2022=_proporcao(
            base_territorial,
            "localizacao_id",
            1,
        ),
    )


def _calcular_composicao(
    fato: pd.DataFrame,
    coluna_categoria: str,
    categorias: tuple[int, ...],
    rotulos: dict[int, str],
) -> pd.DataFrame:
    """Produz população e proporção de cada categoria por ano."""

    indice = pd.MultiIndex.from_product(
        [ANOS, categorias],
        names=["ano", coluna_categoria],
    )
    composicao = (
        fato.groupby(
            ["ano", coluna_categoria],
            observed=True,
        )["populacao_indigena"]
        .sum()
        .reindex(indice, fill_value=0)
        .rename("populacao_indigena")
        .reset_index()
    )
    totais = composicao.groupby("ano")["populacao_indigena"].transform("sum")
    composicao["proporcao"] = (
        composicao["populacao_indigena"].div(totais.where(totais != 0)).fillna(0)
    )
    composicao["categoria"] = composicao[coluna_categoria].map(rotulos)

    return composicao


def composicao_domiciliar_por_ano(
    fato: pd.DataFrame,
    localizacao_ids: Iterable[int] = LOCALIZACOES,
) -> pd.DataFrame:
    """Calcula a composição urbana-rural no recorte territorial."""

    base = filtrar_fato(fato, localizacao_ids, DOMICILIOS)

    return _calcular_composicao(
        base,
        "domicilio_id",
        DOMICILIOS,
        {1: "Urbana", 2: "Rural"},
    )


def composicao_territorial_por_ano(
    fato: pd.DataFrame,
    domicilio_ids: Iterable[int] = DOMICILIOS,
) -> pd.DataFrame:
    """Calcula a composição TI–fora de TI no recorte domiciliar."""

    base = filtrar_fato(fato, LOCALIZACOES, domicilio_ids)

    return _calcular_composicao(
        base,
        "localizacao_id",
        LOCALIZACOES,
        {1: "Em TI", 2: "Fora de TI"},
    )
