"""Cálculos estaduais usados pela página de distribuição espacial."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

from dashboard.metrics import DOMICILIOS, LOCALIZACOES, filtrar_fato

INDICADORES_ESPACIAIS = {
    "População indígena": "populacao",
    "Participação no Brasil": "participacao_brasil",
    "Parcela urbana": "proporcao_urbana",
    "Parcela em TI": "proporcao_ti",
}

RECORTES_TEMPORAIS = ("2010", "2022", "Variação 2010–2022")


def _agregar_populacao_uf(fato: pd.DataFrame) -> pd.DataFrame:
    """Agrega a tabela fato para uma observação por UF e ano."""
    return (
        fato.groupby(["uf_id", "ano"], as_index=False, observed=True)["populacao_indigena"]
        .sum()
        .astype({"ano": "int64", "populacao_indigena": "int64"})
    )


def _proporcao_por_uf(
    fato: pd.DataFrame,
    coluna: str,
    categoria: int,
) -> pd.DataFrame:
    """Calcula a participação de uma categoria no total de cada UF e ano."""
    totais = _agregar_populacao_uf(fato).rename(columns={"populacao_indigena": "total"})
    numerador = _agregar_populacao_uf(fato.loc[fato[coluna] == categoria]).rename(
        columns={"populacao_indigena": "numerador"}
    )
    resultado = totais.merge(numerador, on=["uf_id", "ano"], how="left")
    resultado["numerador"] = resultado["numerador"].fillna(0)
    resultado["valor"] = resultado["numerador"].div(resultado["total"].where(resultado["total"] != 0)).fillna(0)
    return resultado[["uf_id", "ano", "valor"]]


def calcular_indicador_estadual(
    fato: pd.DataFrame,
    geografia: pd.DataFrame,
    indicador: str,
    localizacao_ids: Iterable[int] = LOCALIZACOES,
    domicilio_ids: Iterable[int] = DOMICILIOS,
) -> pd.DataFrame:
    """Produz valores estaduais de 2010 e 2022 para um indicador espacial.

    Os filtros são aplicados ao indicador de população e participação nacional.
    Para indicadores de composição, preserva-se o denominador completo da
    dimensão analisada, evitando proporções tautológicas de 0% ou 100%.
    """
    if indicador not in INDICADORES_ESPACIAIS:
        raise ValueError(f"Indicador espacial desconhecido: {indicador}")

    chave = INDICADORES_ESPACIAIS[indicador]
    localizacao_ids = tuple(int(v) for v in localizacao_ids)
    domicilio_ids = tuple(int(v) for v in domicilio_ids)

    if chave in {"populacao", "participacao_brasil"}:
        base = filtrar_fato(fato, localizacao_ids, domicilio_ids)
        resultado = _agregar_populacao_uf(base).rename(columns={"populacao_indigena": "valor"})
        if chave == "participacao_brasil":
            totais = resultado.groupby("ano")["valor"].transform("sum")
            resultado["valor"] = resultado["valor"].div(totais.where(totais != 0)).fillna(0)
    elif chave == "proporcao_urbana":
        base = filtrar_fato(fato, localizacao_ids, DOMICILIOS)
        resultado = _proporcao_por_uf(base, "domicilio_id", 1)
    else:
        base = filtrar_fato(fato, LOCALIZACOES, domicilio_ids)
        resultado = _proporcao_por_uf(base, "localizacao_id", 1)

    geografia_minima = geografia[["uf_id", "sigla_uf", "uf", "regiao"]].copy()
    geografia_minima["uf_id"] = geografia_minima["uf_id"].astype("string").str.zfill(2)
    resultado["uf_id"] = resultado["uf_id"].astype("string").str.zfill(2)
    return resultado.merge(geografia_minima, on="uf_id", how="left", validate="many_to_one")


def preparar_recorte_espacial(
    dados: pd.DataFrame,
    recorte: str,
    indicador: str,
) -> pd.DataFrame:
    """Converte a série estadual em 2010, 2022 ou variação intercensitária."""
    if recorte not in RECORTES_TEMPORAIS:
        raise ValueError(f"Recorte temporal desconhecido: {recorte}")

    if recorte in {"2010", "2022"}:
        resultado = dados.loc[dados["ano"] == int(recorte)].copy()
        resultado["valor_2010"] = pd.NA
        resultado["valor_2022"] = pd.NA
    else:
        indice = ["uf_id", "sigla_uf", "uf", "regiao"]
        pivot = dados.pivot(index=indice, columns="ano", values="valor").reset_index()
        pivot["valor_2010"] = pivot[2010]
        pivot["valor_2022"] = pivot[2022]
        if indicador == "População indígena":
            pivot["valor"] = pivot["valor_2022"] - pivot["valor_2010"]
        else:
            pivot["valor"] = pivot["valor_2022"] - pivot["valor_2010"]
        resultado = pivot[[*indice, "valor", "valor_2010", "valor_2022"]]

    crescente = True
    resultado = resultado.sort_values(["valor", "uf"], ascending=[not crescente, True]).reset_index(drop=True)
    resultado["posicao"] = resultado.index + 1
    return resultado
