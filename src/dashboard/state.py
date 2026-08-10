"""Cálculos reutilizáveis da página de perfil estadual."""

from __future__ import annotations

import pandas as pd


def _normalizar_uf_id(valor: object) -> str:
    """Normaliza o código IBGE da UF para texto com dois dígitos."""

    return str(valor).strip().zfill(2)


def calcular_perfil_estadual(
    fato: pd.DataFrame,
    geografia: pd.DataFrame,
) -> pd.DataFrame:
    """Agrega a população por UF e ano, preservando região e ordem territorial."""

    fato_normalizado = fato.copy()
    geografia_normalizada = geografia.copy()
    fato_normalizado["uf_id"] = fato_normalizado["uf_id"].map(_normalizar_uf_id)
    geografia_normalizada["uf_id"] = geografia_normalizada["uf_id"].map(
        _normalizar_uf_id
    )

    dados = fato_normalizado.merge(
        geografia_normalizada[
            ["uf_id", "uf", "sigla_uf", "regiao_id", "regiao", "ordem_regiao"]
        ],
        on="uf_id",
        how="left",
        validate="many_to_one",
    )
    return (
        dados.groupby(
            ["uf_id", "uf", "sigla_uf", "regiao_id", "regiao", "ordem_regiao", "ano"],
            as_index=False,
            observed=True,
        )["populacao_indigena"]
        .sum()
        .sort_values(["uf", "ano"])
        .reset_index(drop=True)
    )


def calcular_indicadores_uf(
    perfil: pd.DataFrame,
    uf_id: str | int,
) -> dict[str, object]:
    """Calcula evolução, participação e posições nacional/regional de uma UF."""

    chave_uf = _normalizar_uf_id(uf_id)
    uf = perfil.loc[perfil["uf_id"] == chave_uf].sort_values("ano")
    if set(uf["ano"]) != {2010, 2022}:
        raise ValueError("A UF selecionada precisa possuir observações de 2010 e 2022.")

    linha_2010 = uf.loc[uf["ano"] == 2010].iloc[0]
    linha_2022 = uf.loc[uf["ano"] == 2022].iloc[0]
    pop_2010 = int(linha_2010["populacao_indigena"])
    pop_2022 = int(linha_2022["populacao_indigena"])
    crescimento_absoluto = pop_2022 - pop_2010
    crescimento_relativo = crescimento_absoluto / pop_2010 if pop_2010 else None

    ano_2022 = perfil.loc[perfil["ano"] == 2022].copy()
    ano_2022["ranking_brasil"] = ano_2022["populacao_indigena"].rank(
        method="min", ascending=False
    ).astype(int)
    ano_2022["ranking_regiao"] = (
        ano_2022.groupby("regiao_id")["populacao_indigena"]
        .rank(method="min", ascending=False)
        .astype(int)
    )
    selecionada = ano_2022.loc[ano_2022["uf_id"] == chave_uf].iloc[0]

    total_brasil = ano_2022["populacao_indigena"].sum()
    total_regiao = ano_2022.loc[
        ano_2022["regiao_id"] == selecionada["regiao_id"], "populacao_indigena"
    ].sum()

    return {
        "uf_id": chave_uf,
        "uf": str(selecionada["uf"]),
        "sigla_uf": str(selecionada["sigla_uf"]),
        "regiao": str(selecionada["regiao"]),
        "populacao_2010": pop_2010,
        "populacao_2022": pop_2022,
        "crescimento_absoluto": crescimento_absoluto,
        "crescimento_relativo": crescimento_relativo,
        "participacao_brasil": pop_2022 / total_brasil,
        "participacao_regiao": pop_2022 / total_regiao,
        "ranking_brasil": int(selecionada["ranking_brasil"]),
        "ranking_regiao": int(selecionada["ranking_regiao"]),
    }


def calcular_composicao_uf(
    fato: pd.DataFrame,
    uf_id: str | int,
    dimensao: str,
) -> pd.DataFrame:
    """Calcula a composição estadual por domicílio ou localização nos dois censos."""

    configuracoes = {
        "domicilio": ("domicilio_id", {1: "Urbana", 2: "Rural"}),
        "localizacao": ("localizacao_id", {1: "Em TI", 2: "Fora de TI"}),
    }
    if dimensao not in configuracoes:
        raise ValueError("dimensao deve ser 'domicilio' ou 'localizacao'.")

    coluna, rotulos = configuracoes[dimensao]
    chave_uf = _normalizar_uf_id(uf_id)
    dados = fato.copy()
    dados["uf_id"] = dados["uf_id"].map(_normalizar_uf_id)
    dados = dados.loc[dados["uf_id"] == chave_uf]
    agregado = (
        dados.groupby(["ano", coluna], as_index=False, observed=True)["populacao_indigena"]
        .sum()
    )
    agregado["categoria"] = agregado[coluna].map(rotulos)
    agregado["total_ano"] = agregado.groupby("ano")["populacao_indigena"].transform("sum")
    agregado["proporcao"] = agregado["populacao_indigena"] / agregado["total_ano"]
    return agregado.sort_values(["ano", coluna]).reset_index(drop=True)


def calcular_referencias_2022(
    perfil: pd.DataFrame,
    uf_id: str | int,
) -> pd.DataFrame:
    """Compara a população da UF com as médias de sua região e do Brasil em 2022."""

    chave_uf = _normalizar_uf_id(uf_id)
    dados = perfil.loc[perfil["ano"] == 2022]
    uf = dados.loc[dados["uf_id"] == chave_uf].iloc[0]
    regiao = dados.loc[dados["regiao_id"] == uf["regiao_id"]]

    return pd.DataFrame(
        {
            "referencia": [
                f"{uf['uf']} ({uf['sigla_uf']})",
                f"Média — {uf['regiao']}",
                "Média — Brasil",
            ],
            "populacao_indigena": [
                float(uf["populacao_indigena"]),
                float(regiao["populacao_indigena"].mean()),
                float(dados["populacao_indigena"].mean()),
            ],
        }
    )
