"""Cálculos reutilizáveis da página de perfil regional."""

from __future__ import annotations

import pandas as pd


def calcular_perfil_regional(
    fato: pd.DataFrame,
    geografia: pd.DataFrame,
    localizacao_id: int | None = None,
    domicilio_id: int | None = None,
) -> pd.DataFrame:
    """Agrega a população indígena por Grande Região e ano."""

    dados = fato.copy()
    if localizacao_id is not None:
        dados = dados.loc[dados["localizacao_id"] == localizacao_id]
    if domicilio_id is not None:
        dados = dados.loc[dados["domicilio_id"] == domicilio_id]

    dados = dados.merge(
        geografia[["uf_id", "regiao_id", "regiao", "ordem_regiao"]],
        on="uf_id",
        how="left",
        validate="many_to_one",
    )

    perfil = (
        dados.groupby(
            ["regiao_id", "regiao", "ordem_regiao", "ano"],
            as_index=False,
            observed=True,
        )["populacao_indigena"]
        .sum()
        .sort_values(["ordem_regiao", "ano"])
    )
    totais = perfil.groupby("ano")["populacao_indigena"].transform("sum")
    perfil["participacao_brasil"] = perfil["populacao_indigena"] / totais
    return perfil


def calcular_crescimento_regional(perfil: pd.DataFrame) -> pd.DataFrame:
    """Calcula crescimento absoluto e relativo entre 2010 e 2022."""

    tabela = perfil.pivot(
        index=["regiao_id", "regiao", "ordem_regiao"],
        columns="ano",
        values="populacao_indigena",
    ).reset_index()

    tabela["crescimento_absoluto"] = tabela[2022] - tabela[2010]
    tabela["crescimento_relativo"] = tabela["crescimento_absoluto"] / tabela[2010]
    return tabela.sort_values("crescimento_relativo", ascending=False).reset_index(drop=True)


def calcular_composicao_regional(
    fato: pd.DataFrame,
    geografia: pd.DataFrame,
    dimensao: str,
    ano: int = 2022,
) -> pd.DataFrame:
    """Calcula composição urbano-rural ou TI/fora de TI para cada região."""

    configuracoes = {
        "domicilio": ("domicilio_id", {1: "Rural", 2: "Urbana"}),
        "localizacao": ("localizacao_id", {1: "Em TI", 2: "Fora de TI"}),
    }
    if dimensao not in configuracoes:
        raise ValueError("dimensao deve ser 'domicilio' ou 'localizacao'.")

    coluna, rotulos = configuracoes[dimensao]
    dados = fato.loc[fato["ano"] == ano].merge(
        geografia[["uf_id", "regiao_id", "regiao", "ordem_regiao"]],
        on="uf_id",
        how="left",
        validate="many_to_one",
    )
    agregado = (
        dados.groupby(
            ["regiao_id", "regiao", "ordem_regiao", coluna],
            as_index=False,
            observed=True,
        )["populacao_indigena"]
        .sum()
    )
    agregado["categoria"] = agregado[coluna].map(rotulos)
    agregado["total_regiao"] = agregado.groupby("regiao_id")["populacao_indigena"].transform("sum")
    agregado["proporcao"] = agregado["populacao_indigena"] / agregado["total_regiao"]
    return agregado.sort_values(["ordem_regiao", coluna]).reset_index(drop=True)
