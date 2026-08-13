"""Preparação da base analítica do Estudo 6 — Análise Estatística."""

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_samples,
    silhouette_score,
)
from sklearn.preprocessing import RobustScaler
from threadpoolctl import threadpool_limits

REGIOES_ESPERADAS = {
    "Norte",
    "Nordeste",
    "Centro-Oeste",
    "Sudeste",
    "Sul",
}

COLUNAS_FONTE = [
    "Localidade",
    "Região",
    "Indígenas 2010 Total",
    "Indígenas 2010 Urbano",
    "Indígenas 2010 Rural",
    "Indígenas 2010 TI Total",
    "Indígenas 2010 Fora TI Total",
    "Indígenas 2022 Total",
    "Indígenas 2022 Urbano",
    "Indígenas 2022 Rural",
    "Indígenas 2022 TI Total",
    "Indígenas 2022 Fora TI Total",
    "Crescimento absoluto",
    "Crescimento relativo (%)",
    "Urbanização 2010 (%)",
    "Urbanização 2022 (%)",
    "Mudança na urbanização (p.p.)",
    "% Indígenas 2022 em TI",
    "TI urbano (%)",
    "Fora TI urbano (%)",
]

COLUNAS_BASE_ESTATISTICA = [
    "Localidade",
    "Região",
    "Indígenas 2010 Total",
    "Indígenas 2022 Total",
    "População 2010 (log10)",
    "População 2022 (log10)",
    "Crescimento absoluto",
    "Crescimento relativo (%)",
    "Fator de crescimento (2022/2010)",
    "Crescimento logarítmico",
    "Urbanização 2010 (%)",
    "Urbanização 2022 (%)",
    "Mudança na urbanização (p.p.)",
    "Presença em TI 2010 (%)",
    "Presença em TI 2022 (%)",
    "Mudança na presença em TI (p.p.)",
    "TI urbano (%)",
    "Fora TI urbano (%)",
]

COLUNAS_SEM_AUSENCIAS = [
    coluna for coluna in COLUNAS_BASE_ESTATISTICA if coluna != "TI urbano (%)"
]

INDICADORES_DISTRIBUICAO = [
    "Indígenas 2022 Total",
    "Crescimento relativo (%)",
    "Urbanização 2022 (%)",
    "Mudança na urbanização (p.p.)",
    "Presença em TI 2022 (%)",
    "Mudança na presença em TI (p.p.)",
]

INDICADORES_ATIPICIDADE = INDICADORES_DISTRIBUICAO.copy()

PARES_SENSIBILIDADE_ESCALA = [
    (
        "Magnitude populacional",
        "Indígenas 2022 Total",
        "População 2022 (log10)",
    ),
    (
        "Crescimento populacional",
        "Crescimento relativo (%)",
        "Crescimento logarítmico",
    ),
]

PARES_CORRELACAO = [
    {
        "relacao": "Persistência da magnitude populacional",
        "variavel_x": "Indígenas 2010 Total",
        "variavel_y": "Indígenas 2022 Total",
    },
    {
        "relacao": "Magnitude populacional × urbanização em 2022",
        "variavel_x": "Indígenas 2022 Total",
        "variavel_y": "Urbanização 2022 (%)",
    },
    {
        "relacao": "Magnitude populacional × presença em TI em 2022",
        "variavel_x": "Indígenas 2022 Total",
        "variavel_y": "Presença em TI 2022 (%)",
    },
    {
        "relacao": "Crescimento × mudança da urbanização",
        "variavel_x": "Crescimento relativo (%)",
        "variavel_y": "Mudança na urbanização (p.p.)",
    },
    {
        "relacao": "Crescimento × mudança da presença em TI",
        "variavel_x": "Crescimento relativo (%)",
        "variavel_y": "Mudança na presença em TI (p.p.)",
    },
    {
        "relacao": "Urbanização × presença em TI em 2022",
        "variavel_x": "Urbanização 2022 (%)",
        "variavel_y": "Presença em TI 2022 (%)",
    },
    {
        "relacao": "Urbanização em TI × fora de TI em 2022",
        "variavel_x": "TI urbano (%)",
        "variavel_y": "Fora TI urbano (%)",
    },
]

CONSTANTE_ESCORE_MAD = 0.6744897501960817

VARIAVEIS_MULTIVARIADAS = [
    "População 2022 (log10)",
    "Crescimento logarítmico",
    "Urbanização 2022 (%)",
    "Mudança na urbanização (p.p.)",
    "Presença em TI 2022 (%)",
    "Mudança na presença em TI (p.p.)",
]

INTERVALO_K_AGRUPAMENTOS = tuple(range(2, 7))
LIMIAR_VARIANCIA_PCA = 0.80
SEMENTE_ANALISE_MULTIVARIADA = 42

# Limiares conservadores definidos para este estudo exploratório. Não são
# apresentados como regras universais para análise de agrupamentos.
CRITERIOS_ACEITACAO_AGRUPAMENTOS = {
    "Silhouette médio": 0.50,
    "Menor agrupamento (UFs)": 3,
    "ARI mediano — reinicializações": 0.90,
    "ARI mínimo — retirada de UF": 0.50,
    "ARI mínimo — retirada de variável": 0.50,
    "ARI P10 — subamostras": 0.50,
}


def _validar_base_fonte(df: pd.DataFrame) -> None:
    """Valida integridade, granularidade e identidades da base de entrada."""

    if not isinstance(df, pd.DataFrame):
        raise TypeError("A base de entrada deve ser um DataFrame.")

    if df.empty:
        raise ValueError("A base estadual está vazia.")

    colunas_ausentes = sorted(set(COLUNAS_FONTE) - set(df.columns))
    if colunas_ausentes:
        raise KeyError(f"Colunas obrigatórias ausentes: {colunas_ausentes}")

    if len(df) != 27:
        raise ValueError("A base deve conter exatamente as 27 UFs.")

    if df["Localidade"].duplicated().any():
        duplicadas = sorted(
            df.loc[df["Localidade"].duplicated(keep=False), "Localidade"]
            .astype(str)
            .unique()
        )
        raise ValueError(f"A base contém UFs duplicadas: {duplicadas}")

    regioes_encontradas = set(df["Região"].dropna().astype(str))
    if regioes_encontradas != REGIOES_ESPERADAS:
        raise ValueError(
            "A base deve representar as cinco Grandes Regiões. "
            f"Encontradas: {sorted(regioes_encontradas)}"
        )

    colunas_numericas = [
        coluna for coluna in COLUNAS_FONTE if coluna not in {"Localidade", "Região"}
    ]
    nao_numericas = [
        coluna
        for coluna in colunas_numericas
        if not pd.api.types.is_numeric_dtype(df[coluna])
    ]
    if nao_numericas:
        raise TypeError(f"Colunas que deveriam ser numéricas: {nao_numericas}")

    for ano in (2010, 2022):
        total = df[f"Indígenas {ano} Total"]
        urbano_rural = df[f"Indígenas {ano} Urbano"] + df[f"Indígenas {ano} Rural"]
        ti_fora_ti = (
            df[f"Indígenas {ano} TI Total"] + df[f"Indígenas {ano} Fora TI Total"]
        )

        if not total.eq(urbano_rural).all():
            raise ValueError(f"Total diferente de urbano + rural em {ano}.")

        if not total.eq(ti_fora_ti).all():
            raise ValueError(f"Total diferente de em TI + fora de TI em {ano}.")

        if not total.gt(0).all():
            raise ValueError(f"Existem denominadores não positivos em {ano}.")


def preparar_base_estatistica(df: pd.DataFrame) -> pd.DataFrame:
    """Seleciona dimensões não redundantes e calcula indicadores do Estudo 6."""

    _validar_base_fonte(df)

    base = df[
        [
            "Localidade",
            "Região",
            "Indígenas 2010 Total",
            "Indígenas 2022 Total",
            "Crescimento absoluto",
            "Crescimento relativo (%)",
            "Urbanização 2010 (%)",
            "Urbanização 2022 (%)",
            "Mudança na urbanização (p.p.)",
            "TI urbano (%)",
            "Fora TI urbano (%)",
        ]
    ].copy()

    total_2010 = df["Indígenas 2010 Total"].astype(float)
    total_2022 = df["Indígenas 2022 Total"].astype(float)

    base["População 2010 (log10)"] = np.log10(total_2010)
    base["População 2022 (log10)"] = np.log10(total_2022)
    base["Fator de crescimento (2022/2010)"] = total_2022.div(total_2010)
    base["Crescimento logarítmico"] = np.log(base["Fator de crescimento (2022/2010)"])

    base["Presença em TI 2010 (%)"] = (
        df["Indígenas 2010 TI Total"].div(total_2010).mul(100)
    )
    base["Presença em TI 2022 (%)"] = (
        df["Indígenas 2022 TI Total"].div(total_2022).mul(100)
    )
    base["Mudança na presença em TI (p.p.)"] = (
        base["Presença em TI 2022 (%)"] - base["Presença em TI 2010 (%)"]
    )

    base = base[COLUNAS_BASE_ESTATISTICA]
    validar_base_estatistica(base, referencia=df)

    return base


def validar_base_estatistica(
    base: pd.DataFrame,
    referencia: pd.DataFrame | None = None,
) -> dict[str, bool]:
    """Valida o contrato da base estatística e retorna cada verificação."""

    colunas_ausentes = sorted(set(COLUNAS_BASE_ESTATISTICA) - set(base.columns))
    if colunas_ausentes:
        raise KeyError(f"Colunas da base estatística ausentes: {colunas_ausentes}")

    proporcoes = [
        "Urbanização 2010 (%)",
        "Urbanização 2022 (%)",
        "Presença em TI 2010 (%)",
        "Presença em TI 2022 (%)",
        "TI urbano (%)",
        "Fora TI urbano (%)",
    ]

    resultados = {
        "A base contém 27 UFs": len(base) == 27,
        "As UFs são únicas": not base["Localidade"].duplicated().any(),
        "As cinco regiões estão representadas": (
            set(base["Região"].astype(str)) == REGIOES_ESPERADAS
        ),
        "Os indicadores centrais não possuem ausências": (
            base[COLUNAS_SEM_AUSENCIAS].notna().all().all()
        ),
        "As proporções pertencem ao intervalo de 0% a 100%": all(
            base[coluna].dropna().between(0, 100).all() for coluna in proporcoes
        ),
        "Os fatores de crescimento são positivos": (
            base["Fator de crescimento (2022/2010)"].gt(0).all()
        ),
        "Os logaritmos são finitos": np.isfinite(
            base[
                [
                    "População 2010 (log10)",
                    "População 2022 (log10)",
                    "Crescimento logarítmico",
                ]
            ].to_numpy()
        ).all(),
        "A mudança urbana está em pontos percentuais": np.allclose(
            base["Mudança na urbanização (p.p.)"],
            base["Urbanização 2022 (%)"] - base["Urbanização 2010 (%)"],
        ),
        "A mudança em TI está em pontos percentuais": np.allclose(
            base["Mudança na presença em TI (p.p.)"],
            base["Presença em TI 2022 (%)"] - base["Presença em TI 2010 (%)"],
        ),
        "O log do crescimento corresponde ao fator": np.allclose(
            np.exp(base["Crescimento logarítmico"]),
            base["Fator de crescimento (2022/2010)"],
        ),
    }

    if referencia is not None:
        resultados.update(
            {
                "A presença em TI de 2022 coincide com a base de referência": (
                    np.allclose(
                        base["Presença em TI 2022 (%)"],
                        referencia["% Indígenas 2022 em TI"],
                    )
                ),
                "O crescimento relativo coincide com a base de referência": (
                    np.allclose(
                        base["Crescimento relativo (%)"],
                        referencia["Crescimento relativo (%)"],
                    )
                ),
            }
        )

    falhas = [nome for nome, aprovado in resultados.items() if not aprovado]
    if falhas:
        raise ValueError(f"Falhas na validação da base estatística: {falhas}")

    return resultados


def calcular_resumo_distribuicoes(
    base: pd.DataFrame,
    indicadores: list[str] | None = None,
) -> pd.DataFrame:
    """Calcula medidas clássicas e robustas para indicadores estaduais."""

    validar_base_estatistica(base)

    colunas = indicadores or INDICADORES_DISTRIBUICAO
    colunas_ausentes = sorted(set(colunas) - set(base.columns))
    if colunas_ausentes:
        raise KeyError(f"Indicadores ausentes na base: {colunas_ausentes}")

    nao_numericos = [
        coluna for coluna in colunas if not pd.api.types.is_numeric_dtype(base[coluna])
    ]
    if nao_numericos:
        raise TypeError(f"Indicadores que deveriam ser numéricos: {nao_numericos}")

    registros = []

    for indicador in colunas:
        serie = base[indicador].dropna().astype(float)

        if len(serie) < 3:
            raise ValueError(
                f"O indicador '{indicador}' precisa de ao menos três valores."
            )

        q1, mediana, q3 = serie.quantile([0.25, 0.50, 0.75])
        iqr = q3 - q1
        mad = float(np.median(np.abs(serie.to_numpy() - mediana)))

        registros.append(
            {
                "Indicador": indicador,
                "N": int(serie.size),
                "Ausentes": int(base[indicador].isna().sum()),
                "Média": float(serie.mean()),
                "Desvio-padrão": float(serie.std(ddof=1)),
                "Mínimo": float(serie.min()),
                "Q1": float(q1),
                "Mediana": float(mediana),
                "Q3": float(q3),
                "Máximo": float(serie.max()),
                "IQR": float(iqr),
                "MAD": mad,
                "Assimetria": float(serie.skew()),
            }
        )

    return pd.DataFrame(registros)


def _validar_valores_concentracao(valores: pd.Series) -> pd.Series:
    """Valida os valores utilizados nas medidas de concentração."""

    if not isinstance(valores, pd.Series):
        raise TypeError("Os valores de concentração devem formar uma Series.")

    if valores.empty:
        raise ValueError("A série de concentração está vazia.")

    if not pd.api.types.is_numeric_dtype(valores):
        raise TypeError("Os valores de concentração devem ser numéricos.")

    if valores.isna().any():
        raise ValueError("Os valores de concentração não podem conter ausências.")

    serie = valores.astype(float)

    if serie.lt(0).any():
        raise ValueError("Os valores de concentração não podem ser negativos.")

    if not serie.sum() > 0:
        raise ValueError("A soma dos valores de concentração deve ser positiva.")

    return serie


def calcular_curva_lorenz(valores: pd.Series) -> pd.DataFrame:
    """Retorna a proporção acumulada de unidades e valores da curva de Lorenz."""

    serie = _validar_valores_concentracao(valores)
    valores_ordenados = np.sort(serie.to_numpy())
    proporcao_acumulada = np.insert(
        np.cumsum(valores_ordenados) / valores_ordenados.sum(),
        0,
        0.0,
    )
    proporcao_unidades = np.linspace(0.0, 1.0, len(valores_ordenados) + 1)

    return pd.DataFrame(
        {
            "Proporção acumulada de UFs": proporcao_unidades,
            "Proporção acumulada da população": proporcao_acumulada,
        }
    )


def calcular_medidas_concentracao(
    base: pd.DataFrame,
    coluna: str = "Indígenas 2022 Total",
) -> pd.DataFrame:
    """Calcula Gini, HHI e razões de concentração para uma variável estadual."""

    if coluna not in base.columns:
        raise KeyError(f"A coluna '{coluna}' não existe na base.")

    valores = _validar_valores_concentracao(base[coluna])
    total = float(valores.sum())
    participacoes = valores.div(total)
    curva_lorenz = calcular_curva_lorenz(valores)

    eixo_ufs = curva_lorenz["Proporção acumulada de UFs"].to_numpy()
    eixo_populacao = curva_lorenz["Proporção acumulada da população"].to_numpy()
    gini = 1.0 - 2.0 * float(np.trapezoid(eixo_populacao, eixo_ufs))

    hhi = float(participacoes.pow(2).sum())
    numero_efetivo_ufs = 1.0 / hhi
    participacoes_decrescentes = participacoes.sort_values(ascending=False)
    acumulado_decrescente = participacoes_decrescentes.cumsum()
    ufs_para_metade = int(np.searchsorted(acumulado_decrescente, 0.50) + 1)

    return pd.DataFrame(
        [
            {
                "Indicador": coluna,
                "Total de UFs": int(valores.size),
                "População total": int(total),
                "Gini": gini,
                "HHI": hhi,
                "Número efetivo de UFs": numero_efetivo_ufs,
                "CR3 (%)": float(participacoes_decrescentes.head(3).sum() * 100),
                "CR5 (%)": float(participacoes_decrescentes.head(5).sum() * 100),
                "UFs para alcançar 50%": ufs_para_metade,
            }
        ]
    )


def detectar_valores_atipicos(
    base: pd.DataFrame,
    indicadores: list[str] | None = None,
    fator_iqr: float = 1.5,
    limite_escore_robusto: float = 3.5,
) -> pd.DataFrame:
    """Sinaliza valores atípicos pelos critérios de Tukey e mediana/MAD.

    Os resultados são diagnósticos descritivos. Uma sinalização não implica erro
    nem autoriza a exclusão automática da observação.
    """

    validar_base_estatistica(base)

    if fator_iqr <= 0:
        raise ValueError("O fator do IQR deve ser positivo.")
    if limite_escore_robusto <= 0:
        raise ValueError("O limite do escore robusto deve ser positivo.")

    colunas = indicadores or INDICADORES_ATIPICIDADE
    colunas_ausentes = sorted(set(colunas) - set(base.columns))
    if colunas_ausentes:
        raise KeyError(f"Indicadores ausentes na base: {colunas_ausentes}")

    nao_numericos = [
        coluna for coluna in colunas if not pd.api.types.is_numeric_dtype(base[coluna])
    ]
    if nao_numericos:
        raise TypeError(f"Indicadores que deveriam ser numéricos: {nao_numericos}")

    registros: list[dict[str, object]] = []

    for ordem, indicador in enumerate(colunas, start=1):
        dados = base[["Localidade", "Região", indicador]].dropna().copy()
        serie = dados[indicador].astype(float)

        if len(serie) < 3:
            raise ValueError(
                f"O indicador '{indicador}' precisa de ao menos três valores."
            )

        q1, mediana, q3 = serie.quantile([0.25, 0.50, 0.75])
        iqr = float(q3 - q1)
        limite_inferior = float(q1 - fator_iqr * iqr)
        limite_superior = float(q3 + fator_iqr * iqr)
        mad = float(np.median(np.abs(serie.to_numpy() - mediana)))

        if mad > 0:
            escores_robustos = CONSTANTE_ESCORE_MAD * (serie - mediana) / mad
            sinal_mad = escores_robustos.abs().gt(limite_escore_robusto)
        else:
            escores_robustos = pd.Series(np.nan, index=serie.index, dtype=float)
            sinal_mad = pd.Series(False, index=serie.index, dtype=bool)

        sinal_tukey = serie.lt(limite_inferior) | serie.gt(limite_superior)
        sinal_uniao = sinal_tukey | sinal_mad

        for indice in dados.index:
            tukey = bool(sinal_tukey.loc[indice])
            criterio_mad = bool(sinal_mad.loc[indice])
            sinalizada = bool(sinal_uniao.loc[indice])

            if tukey and criterio_mad:
                concordancia = "Ambos os critérios"
            elif tukey:
                concordancia = "Somente Tukey"
            elif criterio_mad:
                concordancia = "Somente MAD"
            else:
                concordancia = "Não sinalizada"

            if not sinalizada:
                direcao = "Não sinalizada"
            elif float(serie.loc[indice]) < float(mediana):
                direcao = "Inferior"
            else:
                direcao = "Superior"

            registros.append(
                {
                    "Ordem do indicador": ordem,
                    "Indicador": indicador,
                    "Localidade": dados.loc[indice, "Localidade"],
                    "Região": dados.loc[indice, "Região"],
                    "Valor": float(serie.loc[indice]),
                    "Q1": float(q1),
                    "Mediana": float(mediana),
                    "Q3": float(q3),
                    "IQR": iqr,
                    "Fator IQR": float(fator_iqr),
                    "Limite inferior de Tukey": limite_inferior,
                    "Limite superior de Tukey": limite_superior,
                    "MAD": mad,
                    "Escore robusto": float(escores_robustos.loc[indice]),
                    "Limite do escore robusto": float(limite_escore_robusto),
                    "Sinalizada por Tukey": tukey,
                    "Sinalizada por MAD": criterio_mad,
                    "Sinalizada": sinalizada,
                    "Concordância": concordancia,
                    "Direção": direcao,
                }
            )

    resultado = pd.DataFrame(registros)
    resultado["Magnitude do escore robusto"] = resultado["Escore robusto"].abs()
    resultado = resultado.sort_values(
        ["Ordem do indicador", "Magnitude do escore robusto", "Localidade"],
        ascending=[True, False, True],
        na_position="last",
    ).reset_index(drop=True)

    return resultado


def resumir_valores_atipicos(diagnostico: pd.DataFrame) -> pd.DataFrame:
    """Resume a concordância dos critérios e lista as UFs sinalizadas."""

    colunas_obrigatorias = {
        "Ordem do indicador",
        "Indicador",
        "Localidade",
        "Sinalizada por Tukey",
        "Sinalizada por MAD",
        "Sinalizada",
    }
    colunas_ausentes = sorted(colunas_obrigatorias - set(diagnostico.columns))
    if colunas_ausentes:
        raise KeyError(f"Colunas ausentes no diagnóstico: {colunas_ausentes}")

    registros = []
    for (ordem, indicador), grupo in diagnostico.groupby(
        ["Ordem do indicador", "Indicador"],
        sort=True,
    ):
        tukey = grupo["Sinalizada por Tukey"].astype(bool)
        mad = grupo["Sinalizada por MAD"].astype(bool)
        uniao = grupo["Sinalizada"].astype(bool)
        ufs = grupo.loc[uniao, "Localidade"].astype(str).tolist()

        registros.append(
            {
                "Ordem do indicador": int(ordem),
                "Indicador": indicador,
                "N": len(grupo),
                "Sinalizadas por Tukey": int(tukey.sum()),
                "Sinalizadas por MAD": int(mad.sum()),
                "Sinalizadas por ambos": int((tukey & mad).sum()),
                "Sinalizadas pela união": int(uniao.sum()),
                "UFs sinalizadas": "; ".join(ufs) if ufs else "Nenhuma",
            }
        )

    return (
        pd.DataFrame(registros).sort_values("Ordem do indicador").reset_index(drop=True)
    )


def comparar_sensibilidade_escala(
    base: pd.DataFrame,
) -> pd.DataFrame:
    """Compara sinalizações nas escalas original e transformada."""

    validar_base_estatistica(base)
    registros = []

    for (
        dimensao,
        indicador_original,
        indicador_transformado,
    ) in PARES_SENSIBILIDADE_ESCALA:
        diagnostico = detectar_valores_atipicos(
            base,
            indicadores=[indicador_original, indicador_transformado],
        )
        original = diagnostico.loc[
            diagnostico["Indicador"].eq(indicador_original),
            ["Localidade", "Região", "Sinalizada"],
        ].rename(columns={"Sinalizada": "Sinalizada na escala original"})
        transformada = diagnostico.loc[
            diagnostico["Indicador"].eq(indicador_transformado),
            ["Localidade", "Sinalizada"],
        ].rename(columns={"Sinalizada": "Sinalizada na escala transformada"})
        comparacao = original.merge(transformada, on="Localidade", how="inner")

        for linha in comparacao.itertuples(index=False):
            sinal_original = bool(linha[2])
            sinal_transformado = bool(linha[3])
            if sinal_original and sinal_transformado:
                resultado = "Permaneceu sinalizada"
            elif sinal_original:
                resultado = "Deixou de ser sinalizada"
            elif sinal_transformado:
                resultado = "Passou a ser sinalizada"
            else:
                resultado = "Não sinalizada nas duas escalas"

            registros.append(
                {
                    "Dimensão": dimensao,
                    "Localidade": linha.Localidade,
                    "Região": linha.Região,
                    "Indicador original": indicador_original,
                    "Indicador transformado": indicador_transformado,
                    "Sinalizada na escala original": sinal_original,
                    "Sinalizada na escala transformada": sinal_transformado,
                    "Mudou com a transformação": sinal_original != sinal_transformado,
                    "Resultado": resultado,
                }
            )

    return pd.DataFrame(registros)


def _variacao_relativa(valor_novo: float, valor_referencia: float) -> float:
    """Calcula variação percentual, preservando o caso de referência nula."""

    if np.isclose(valor_referencia, 0.0):
        return float("nan")
    return 100.0 * (valor_novo / valor_referencia - 1.0)


def calcular_influencia_leave_one_out(base: pd.DataFrame) -> pd.DataFrame:
    """Quantifica a influência de cada UF por exclusões unitárias hipotéticas."""

    validar_base_estatistica(base)
    coluna = "Indígenas 2022 Total"
    valores = base[coluna].astype(float)
    concentracao_referencia = calcular_medidas_concentracao(base, coluna).iloc[0]
    referencias = {
        "Média": float(valores.mean()),
        "Mediana": float(valores.median()),
        "Gini": float(concentracao_referencia["Gini"]),
        "HHI": float(concentracao_referencia["HHI"]),
        "CR3": float(concentracao_referencia["CR3 (%)"]),
    }
    total = float(valores.sum())
    registros = []

    for indice, linha in base.iterrows():
        base_sem_uf = base.drop(index=indice)
        valores_sem_uf = base_sem_uf[coluna].astype(float)
        concentracao = calcular_medidas_concentracao(base_sem_uf, coluna).iloc[0]
        resultados = {
            "Média": float(valores_sem_uf.mean()),
            "Mediana": float(valores_sem_uf.median()),
            "Gini": float(concentracao["Gini"]),
            "HHI": float(concentracao["HHI"]),
            "CR3": float(concentracao["CR3 (%)"]),
        }
        variacoes = {
            metrica: _variacao_relativa(resultados[metrica], referencias[metrica])
            for metrica in referencias
        }
        metrica_maior_variacao = max(
            variacoes,
            key=lambda metrica: abs(variacoes[metrica]),
        )

        registros.append(
            {
                "UF retirada hipoteticamente": linha["Localidade"],
                "Região": linha["Região"],
                "População da UF": int(linha[coluna]),
                "Participação da UF (%)": float(linha[coluna] / total * 100),
                "Média sem UF": resultados["Média"],
                "Variação da média (%)": variacoes["Média"],
                "Mediana sem UF": resultados["Mediana"],
                "Variação da mediana (%)": variacoes["Mediana"],
                "Gini sem UF": resultados["Gini"],
                "Variação do Gini (%)": variacoes["Gini"],
                "HHI sem UF": resultados["HHI"],
                "Variação do HHI (%)": variacoes["HHI"],
                "CR3 sem UF (%)": resultados["CR3"],
                "Variação do CR3 (%)": variacoes["CR3"],
                "Variação do CR3 (p.p.)": resultados["CR3"] - referencias["CR3"],
                "Variação máxima absoluta (%)": abs(variacoes[metrica_maior_variacao]),
                "Métrica de maior variação": metrica_maior_variacao,
            }
        )

    resultado = pd.DataFrame(registros)
    resultado["Rank de influência"] = (
        resultado["Variação máxima absoluta (%)"]
        .rank(method="first", ascending=False)
        .astype(int)
    )

    return resultado.sort_values("Rank de influência").reset_index(drop=True)


def calcular_sensibilidade_sem_sinalizadas(
    base: pd.DataFrame,
    diagnostico: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Contrasta medidas com e sem UFs sinalizadas, apenas como sensibilidade."""

    validar_base_estatistica(base)
    diagnostico_atipicidade = (
        detectar_valores_atipicos(base) if diagnostico is None else diagnostico.copy()
    )
    colunas_obrigatorias = {"Indicador", "Localidade", "Sinalizada"}
    colunas_ausentes = sorted(
        colunas_obrigatorias - set(diagnostico_atipicidade.columns)
    )
    if colunas_ausentes:
        raise KeyError(f"Colunas ausentes no diagnóstico: {colunas_ausentes}")

    registros = []
    ordem_indicadores = diagnostico_atipicidade["Indicador"].drop_duplicates()
    for ordem, indicador in enumerate(ordem_indicadores, start=1):
        if indicador not in base.columns:
            raise KeyError(f"O indicador '{indicador}' não existe na base.")

        grupo = diagnostico_atipicidade.loc[
            diagnostico_atipicidade["Indicador"].eq(indicador)
        ]
        ufs_sinalizadas = (
            grupo.loc[grupo["Sinalizada"].astype(bool), "Localidade"]
            .astype(str)
            .tolist()
        )
        serie_completa = base[indicador].dropna().astype(float)
        serie_restrita = (
            base.loc[~base["Localidade"].isin(ufs_sinalizadas), indicador]
            .dropna()
            .astype(float)
        )

        if serie_restrita.empty:
            raise ValueError(
                f"A análise de sensibilidade eliminaria todos os valores de '{indicador}'."
            )

        media_completa = float(serie_completa.mean())
        media_restrita = float(serie_restrita.mean())
        mediana_completa = float(serie_completa.median())
        mediana_restrita = float(serie_restrita.median())

        registros.append(
            {
                "Ordem do indicador": ordem,
                "Indicador": indicador,
                "N completo": int(serie_completa.size),
                "N sem sinalizadas": int(serie_restrita.size),
                "Quantidade de UFs sinalizadas": len(ufs_sinalizadas),
                "UFs retiradas hipoteticamente": (
                    "; ".join(ufs_sinalizadas) if ufs_sinalizadas else "Nenhuma"
                ),
                "Média completa": media_completa,
                "Média sem sinalizadas": media_restrita,
                "Variação da média (%)": _variacao_relativa(
                    media_restrita,
                    media_completa,
                ),
                "Mediana completa": mediana_completa,
                "Mediana sem sinalizadas": mediana_restrita,
                "Variação da mediana (%)": _variacao_relativa(
                    mediana_restrita,
                    mediana_completa,
                ),
            }
        )

    return pd.DataFrame(registros)


def _validar_pares_correlacao(
    base: pd.DataFrame,
    pares: list[dict[str, str]],
) -> None:
    """Valida a especificação dos pares usados nas correlações."""

    if not pares:
        raise ValueError("Ao menos um par de correlação deve ser informado.")

    chaves_obrigatorias = {"relacao", "variavel_x", "variavel_y"}
    relacoes = []
    for par in pares:
        chaves_ausentes = sorted(chaves_obrigatorias - set(par))
        if chaves_ausentes:
            raise KeyError(
                f"Chaves ausentes na especificação de correlação: {chaves_ausentes}"
            )

        relacao = str(par["relacao"])
        variavel_x = str(par["variavel_x"])
        variavel_y = str(par["variavel_y"])
        relacoes.append(relacao)

        if variavel_x == variavel_y:
            raise ValueError(
                f"A relação '{relacao}' repete a mesma variável nos dois eixos."
            )

        colunas_ausentes = sorted({variavel_x, variavel_y} - set(base.columns))
        if colunas_ausentes:
            raise KeyError(
                f"Colunas ausentes na relação '{relacao}': {colunas_ausentes}"
            )

        nao_numericas = [
            coluna
            for coluna in (variavel_x, variavel_y)
            if not pd.api.types.is_numeric_dtype(base[coluna])
        ]
        if nao_numericas:
            raise TypeError(
                f"Variáveis não numéricas na relação '{relacao}': {nao_numericas}"
            )

    if len(relacoes) != len(set(relacoes)):
        raise ValueError("Os nomes das relações de correlação devem ser únicos.")


def _calcular_spearman(
    dados: pd.DataFrame,
    variavel_x: str,
    variavel_y: str,
) -> float:
    """Calcula Spearman como a correlação de Pearson entre postos médios."""

    dados_completos = dados[[variavel_x, variavel_y]].dropna()
    if len(dados_completos) < 3:
        raise ValueError(
            "Cada correlação de Spearman precisa de ao menos três pares completos."
        )
    if dados_completos[variavel_x].nunique() < 2:
        raise ValueError(f"A variável '{variavel_x}' não apresenta variação.")
    if dados_completos[variavel_y].nunique() < 2:
        raise ValueError(f"A variável '{variavel_y}' não apresenta variação.")

    postos_x = dados_completos[variavel_x].rank(method="average")
    postos_y = dados_completos[variavel_y].rank(method="average")
    return float(postos_x.corr(postos_y))


def calcular_correlacoes_spearman(
    base: pd.DataFrame,
    pares: list[dict[str, str]] | None = None,
) -> pd.DataFrame:
    """Calcula associações monotônicas para pares selecionados.

    Os coeficientes descrevem o universo das 27 UFs. Por essa razão, a função
    não produz testes de significância ou valores-p amostrais.
    """

    validar_base_estatistica(base)
    pares_selecionados = PARES_CORRELACAO if pares is None else pares
    _validar_pares_correlacao(base, pares_selecionados)
    registros = []

    for ordem, par in enumerate(pares_selecionados, start=1):
        relacao = str(par["relacao"])
        variavel_x = str(par["variavel_x"])
        variavel_y = str(par["variavel_y"])
        dados = base[[variavel_x, variavel_y]].dropna()
        coeficiente = _calcular_spearman(dados, variavel_x, variavel_y)

        if np.isclose(coeficiente, 0.0, atol=1e-12):
            direcao = "Nula"
        elif coeficiente > 0:
            direcao = "Positiva"
        else:
            direcao = "Negativa"

        registros.append(
            {
                "Ordem da relação": ordem,
                "Relação": relacao,
                "Variável X": variavel_x,
                "Variável Y": variavel_y,
                "N": len(dados),
                "Ausentes pareados": int(len(base) - len(dados)),
                "Spearman (ρ)": coeficiente,
                "Magnitude absoluta (|ρ|)": abs(coeficiente),
                "Direção": direcao,
            }
        )

    return pd.DataFrame(registros)


def calcular_estabilidade_ranking_populacional(base: pd.DataFrame) -> pd.DataFrame:
    """Compara as posições estaduais por população total em 2010 e 2022."""

    validar_base_estatistica(base)
    ranking = base[
        [
            "Localidade",
            "Região",
            "Indígenas 2010 Total",
            "Indígenas 2022 Total",
        ]
    ].copy()

    if ranking["Indígenas 2010 Total"].duplicated().any():
        raise ValueError("A população de 2010 contém empates no ranking estadual.")
    if ranking["Indígenas 2022 Total"].duplicated().any():
        raise ValueError("A população de 2022 contém empates no ranking estadual.")

    ranking["Posição em 2010"] = (
        ranking["Indígenas 2010 Total"].rank(method="min", ascending=False).astype(int)
    )
    ranking["Posição em 2022"] = (
        ranking["Indígenas 2022 Total"].rank(method="min", ascending=False).astype(int)
    )
    ranking["Variação no ranking (posições)"] = (
        ranking["Posição em 2010"] - ranking["Posição em 2022"]
    )
    ranking["Mudança absoluta (posições)"] = ranking[
        "Variação no ranking (posições)"
    ].abs()
    ranking["Movimento"] = np.select(
        [
            ranking["Variação no ranking (posições)"].gt(0),
            ranking["Variação no ranking (posições)"].lt(0),
        ],
        ["Subiu", "Desceu"],
        default="Permaneceu",
    )

    return ranking.sort_values("Posição em 2022").reset_index(drop=True)


def resumir_estabilidade_ranking(ranking: pd.DataFrame) -> pd.DataFrame:
    """Resume a concordância entre os rankings populacionais dos dois censos."""

    colunas_obrigatorias = {
        "Localidade",
        "Posição em 2010",
        "Posição em 2022",
        "Variação no ranking (posições)",
        "Mudança absoluta (posições)",
    }
    colunas_ausentes = sorted(colunas_obrigatorias - set(ranking.columns))
    if colunas_ausentes:
        raise KeyError(f"Colunas ausentes no ranking: {colunas_ausentes}")
    if ranking.empty:
        raise ValueError("O ranking populacional está vazio.")
    if ranking["Localidade"].duplicated().any():
        raise ValueError("O ranking contém UFs duplicadas.")

    rho = _calcular_spearman(ranking, "Posição em 2010", "Posição em 2022")
    mudanca = ranking["Variação no ranking (posições)"].astype(int)
    mudanca_absoluta = ranking["Mudança absoluta (posições)"].astype(int)
    maior_mudanca = int(mudanca_absoluta.max())
    ufs_maior_mudanca = sorted(
        ranking.loc[mudanca_absoluta.eq(maior_mudanca), "Localidade"].astype(str)
    )

    maior_subida = int(mudanca.max())
    maior_queda = int(mudanca.min())
    ufs_maior_subida = sorted(
        ranking.loc[mudanca.eq(maior_subida), "Localidade"].astype(str)
    )
    ufs_maior_queda = sorted(
        ranking.loc[mudanca.eq(maior_queda), "Localidade"].astype(str)
    )
    top_5_2010 = set(
        ranking.loc[ranking["Posição em 2010"].le(5), "Localidade"].astype(str)
    )
    top_5_2022 = set(
        ranking.loc[ranking["Posição em 2022"].le(5), "Localidade"].astype(str)
    )
    top_10_2010 = set(
        ranking.loc[ranking["Posição em 2010"].le(10), "Localidade"].astype(str)
    )
    top_10_2022 = set(
        ranking.loc[ranking["Posição em 2022"].le(10), "Localidade"].astype(str)
    )
    intersecao_top_5 = len(top_5_2010 & top_5_2022)
    intersecao_top_10 = len(top_10_2010 & top_10_2022)

    return pd.DataFrame(
        [
            {
                "Total de UFs": len(ranking),
                "Spearman entre rankings (ρ)": rho,
                "UFs na mesma posição": int(mudanca.eq(0).sum()),
                "Mediana da mudança absoluta": float(mudanca_absoluta.median()),
                "Média da mudança absoluta": float(mudanca_absoluta.mean()),
                "Máxima mudança absoluta": maior_mudanca,
                "UFs com maior mudança": "; ".join(ufs_maior_mudanca),
                "UFs que mais subiram": "; ".join(ufs_maior_subida),
                "Posições da maior subida": maior_subida,
                "UFs que mais desceram": "; ".join(ufs_maior_queda),
                "Posições da maior queda": abs(maior_queda),
                "Interseção Top 5": intersecao_top_5,
                "Retenção Top 5 (%)": 100.0 * intersecao_top_5 / 5,
                "Interseção Top 10": intersecao_top_10,
                "Retenção Top 10 (%)": 100.0 * intersecao_top_10 / 10,
            }
        ]
    )


def calcular_influencia_correlacoes_leave_one_out(
    base: pd.DataFrame,
    pares: list[dict[str, str]] | None = None,
) -> pd.DataFrame:
    """Mede quanto cada UF altera os coeficientes de Spearman selecionados."""

    validar_base_estatistica(base)
    pares_selecionados = PARES_CORRELACAO if pares is None else pares
    _validar_pares_correlacao(base, pares_selecionados)
    correlacoes = calcular_correlacoes_spearman(base, pares_selecionados)
    registros = []

    for ordem, par in enumerate(pares_selecionados, start=1):
        relacao = str(par["relacao"])
        variavel_x = str(par["variavel_x"])
        variavel_y = str(par["variavel_y"])
        dados = base[["Localidade", "Região", variavel_x, variavel_y]].dropna()
        rho_completo = float(
            correlacoes.loc[correlacoes["Relação"].eq(relacao), "Spearman (ρ)"].iloc[0]
        )

        registros_relacao = []
        for indice, linha in dados.iterrows():
            dados_sem_uf = dados.drop(index=indice)
            rho_sem_uf = _calcular_spearman(
                dados_sem_uf,
                variavel_x,
                variavel_y,
            )
            variacao = rho_sem_uf - rho_completo
            registros_relacao.append(
                {
                    "Ordem da relação": ordem,
                    "Relação": relacao,
                    "Variável X": variavel_x,
                    "Variável Y": variavel_y,
                    "UF retirada hipoteticamente": linha["Localidade"],
                    "Região": linha["Região"],
                    "N completo": len(dados),
                    "N sem UF": len(dados_sem_uf),
                    "Spearman completo (ρ)": rho_completo,
                    "Spearman sem UF (ρ)": rho_sem_uf,
                    "Variação de ρ": variacao,
                    "Variação absoluta de ρ": abs(variacao),
                }
            )

        registros_relacao.sort(
            key=lambda registro: (
                -float(registro["Variação absoluta de ρ"]),
                str(registro["UF retirada hipoteticamente"]),
            )
        )
        for rank, registro in enumerate(registros_relacao, start=1):
            registro["Rank de influência na relação"] = rank
            registros.append(registro)

    return pd.DataFrame(registros)


def _validar_variaveis_multivariadas(
    base: pd.DataFrame,
    variaveis: list[str],
) -> None:
    """Valida o conjunto de dimensões usado na análise multivariada."""

    if len(variaveis) < 2:
        raise ValueError("A análise multivariada exige ao menos duas variáveis.")
    if len(variaveis) != len(set(variaveis)):
        raise ValueError("As variáveis multivariadas devem ser únicas.")

    colunas_ausentes = sorted(set(variaveis) - set(base.columns))
    if colunas_ausentes:
        raise KeyError(f"Variáveis multivariadas ausentes: {colunas_ausentes}")

    nao_numericas = [
        coluna
        for coluna in variaveis
        if not pd.api.types.is_numeric_dtype(base[coluna])
    ]
    if nao_numericas:
        raise TypeError(f"Variáveis multivariadas não numéricas: {nao_numericas}")

    if base[variaveis].isna().any().any():
        raise ValueError("As variáveis multivariadas não podem conter ausências.")
    if not np.isfinite(base[variaveis].to_numpy(dtype=float)).all():
        raise ValueError("As variáveis multivariadas devem conter valores finitos.")

    amplitudes_interquartis = base[variaveis].quantile(0.75) - base[variaveis].quantile(
        0.25
    )
    sem_variacao_robusta = amplitudes_interquartis.index[
        amplitudes_interquartis.le(0)
    ].tolist()
    if sem_variacao_robusta:
        raise ValueError(
            f"Variáveis sem amplitude interquartil positiva: {sem_variacao_robusta}"
        )


def preparar_base_multivariada(
    base: pd.DataFrame,
    variaveis: list[str] | None = None,
) -> pd.DataFrame:
    """Aplica centralização pela mediana e escala pelo IQR às dimensões."""

    validar_base_estatistica(base)
    variaveis_selecionadas = (
        VARIAVEIS_MULTIVARIADAS if variaveis is None else list(variaveis)
    )
    _validar_variaveis_multivariadas(base, variaveis_selecionadas)

    escalador = RobustScaler(quantile_range=(25.0, 75.0))
    valores_padronizados = escalador.fit_transform(
        base[variaveis_selecionadas].astype(float)
    )
    colunas_padronizadas = [
        f"{variavel} — escala robusta" for variavel in variaveis_selecionadas
    ]

    resultado = base[["Localidade", "Região", *variaveis_selecionadas]].copy()
    resultado[colunas_padronizadas] = valores_padronizados
    return resultado


def _quantidade_componentes_para_limiar(
    proporcoes_variancia: np.ndarray,
    limiar_variancia: float,
) -> int:
    """Retorna o menor número de componentes que alcança o limiar informado."""

    if not 0 < limiar_variancia <= 1:
        raise ValueError("O limiar de variância da PCA deve pertencer a (0, 1].")
    acumulada = np.cumsum(proporcoes_variancia)
    return int(np.searchsorted(acumulada, limiar_variancia, side="left") + 1)


def calcular_pca_multivariada(
    base: pd.DataFrame,
    variaveis: list[str] | None = None,
    limiar_variancia: float = LIMIAR_VARIANCIA_PCA,
) -> dict[str, pd.DataFrame | int]:
    """Resume as dimensões estaduais com PCA após padronização robusta."""

    validar_base_estatistica(base)
    variaveis_selecionadas = (
        VARIAVEIS_MULTIVARIADAS if variaveis is None else list(variaveis)
    )
    _validar_variaveis_multivariadas(base, variaveis_selecionadas)

    base_padronizada = preparar_base_multivariada(base, variaveis_selecionadas)
    colunas_padronizadas = [
        f"{variavel} — escala robusta" for variavel in variaveis_selecionadas
    ]
    matriz_padronizada = base_padronizada[colunas_padronizadas].to_numpy()

    pca = PCA(svd_solver="full")
    escores_matriz = pca.fit_transform(matriz_padronizada)
    quantidade_retida = _quantidade_componentes_para_limiar(
        pca.explained_variance_ratio_,
        limiar_variancia,
    )
    nomes_componentes = [
        f"PC{indice}" for indice in range(1, len(variaveis_selecionadas) + 1)
    ]

    variancia = pd.DataFrame(
        {
            "Componente": nomes_componentes,
            "Autovalor": pca.explained_variance_,
            "Variância explicada (%)": pca.explained_variance_ratio_ * 100,
            "Variância acumulada (%)": (np.cumsum(pca.explained_variance_ratio_) * 100),
            "Componente retido": [
                indice <= quantidade_retida
                for indice in range(1, len(nomes_componentes) + 1)
            ],
        }
    )

    registros_cargas: list[dict[str, object]] = []
    for indice_componente, componente in enumerate(nomes_componentes):
        for indice_variavel, variavel in enumerate(variaveis_selecionadas):
            correlacao = float(
                np.corrcoef(
                    matriz_padronizada[:, indice_variavel],
                    escores_matriz[:, indice_componente],
                )[0, 1]
            )
            peso = float(pca.components_[indice_componente, indice_variavel])
            registros_cargas.append(
                {
                    "Componente": componente,
                    "Variável": variavel,
                    "Peso no vetor": peso,
                    "Correlação variável–componente": correlacao,
                    "Contribuição ao componente (%)": peso**2 * 100,
                    "Componente retido": (indice_componente + 1 <= quantidade_retida),
                }
            )
    cargas = pd.DataFrame(registros_cargas)

    escores = base[["Localidade", "Região"]].copy()
    escores[nomes_componentes] = escores_matriz

    return {
        "base_padronizada": base_padronizada,
        "variancia": variancia,
        "cargas": cargas,
        "escores": escores,
        "quantidade_componentes_retidos": quantidade_retida,
    }


def _ajustar_pipeline_agrupamento(
    base: pd.DataFrame,
    variaveis: list[str],
    k: int,
    random_state: int,
    n_init: int,
    limiar_variancia: float = LIMIAR_VARIANCIA_PCA,
) -> dict[str, object]:
    """Ajusta escala robusta, PCA e K-means para uma perturbação da base."""

    _validar_variaveis_multivariadas(base, variaveis)
    if not 2 <= k < len(base):
        raise ValueError("K deve ser ao menos 2 e menor que o número de UFs.")

    matriz = base[variaveis].to_numpy(dtype=float)
    escalador = RobustScaler(quantile_range=(25.0, 75.0)).fit(matriz)
    matriz_padronizada = escalador.transform(matriz)
    pca = PCA(svd_solver="full").fit(matriz_padronizada)
    quantidade_retida = _quantidade_componentes_para_limiar(
        pca.explained_variance_ratio_,
        limiar_variancia,
    )
    escores = pca.transform(matriz_padronizada)[:, :quantidade_retida]
    modelo = KMeans(
        n_clusters=k,
        n_init=n_init,
        random_state=random_state,
        algorithm="lloyd",
    )
    with threadpool_limits(limits=1):
        modelo.fit(escores)

    return {
        "escalador": escalador,
        "pca": pca,
        "quantidade_componentes_retidos": quantidade_retida,
        "escores": escores,
        "modelo": modelo,
        "rotulos": modelo.labels_.copy(),
    }


def _predizer_pipeline_agrupamento(
    ajuste: dict[str, object],
    base: pd.DataFrame,
    variaveis: list[str],
) -> np.ndarray:
    """Projeta observações em um pipeline ajustado e prediz seus grupos."""

    escalador = ajuste["escalador"]
    pca = ajuste["pca"]
    modelo = ajuste["modelo"]
    quantidade_retida = int(ajuste["quantidade_componentes_retidos"])

    matriz = base[variaveis].to_numpy(dtype=float)
    matriz_padronizada = escalador.transform(matriz)
    escores = pca.transform(matriz_padronizada)[:, :quantidade_retida]
    with threadpool_limits(limits=1):
        return modelo.predict(escores)


def avaliar_agrupamentos_multivariados(
    base: pd.DataFrame,
    valores_k: tuple[int, ...] = INTERVALO_K_AGRUPAMENTOS,
    repeticoes_inicializacao: int = 100,
    repeticoes_subamostra: int = 100,
    fracao_subamostra: float = 0.80,
    random_state: int = SEMENTE_ANALISE_MULTIVARIADA,
) -> dict[str, pd.DataFrame | int]:
    """Avalia qualidade e estabilidade antes de aceitar qualquer segmentação.

    A função mantém a melhor solução interna apenas como diagnóstico. Uma
    segmentação somente recebe a decisão ``Aceita`` se cumprir simultaneamente
    todos os limiares conservadores definidos para o Estudo 6.
    """

    validar_base_estatistica(base)
    _validar_variaveis_multivariadas(base, VARIAVEIS_MULTIVARIADAS)

    if not valores_k or len(valores_k) != len(set(valores_k)):
        raise ValueError(
            "Os valores de K devem formar uma sequência não vazia e única."
        )
    if any(not 2 <= k < len(base) for k in valores_k):
        raise ValueError("Cada K deve ser ao menos 2 e menor que o número de UFs.")
    if repeticoes_inicializacao < 10 or repeticoes_subamostra < 10:
        raise ValueError("As análises de estabilidade exigem ao menos 10 repetições.")
    if not 0.50 <= fracao_subamostra < 1:
        raise ValueError("A fração de subamostra deve pertencer a [0,50; 1).")

    avaliacoes: list[dict[str, object]] = []
    estabilidades: list[dict[str, object]] = []
    ajustes_referencia: dict[int, dict[str, object]] = {}
    total_subamostra = int(np.ceil(len(base) * fracao_subamostra))

    for k in valores_k:
        ajuste_referencia = _ajustar_pipeline_agrupamento(
            base,
            VARIAVEIS_MULTIVARIADAS,
            k,
            random_state,
            100,
        )
        ajustes_referencia[k] = ajuste_referencia
        escores_referencia = np.asarray(ajuste_referencia["escores"])
        rotulos_referencia = np.asarray(ajuste_referencia["rotulos"])
        tamanhos = np.bincount(rotulos_referencia, minlength=k)

        for repeticao in range(repeticoes_inicializacao):
            modelo_reinicializado = KMeans(
                n_clusters=k,
                n_init=1,
                random_state=random_state + repeticao,
                algorithm="lloyd",
            )
            with threadpool_limits(limits=1):
                modelo_reinicializado.fit(escores_referencia)
            estabilidades.append(
                {
                    "K": k,
                    "Procedimento": "Reinicialização",
                    "Repetição ou elemento": str(repeticao + 1),
                    "N UFs comparadas": len(base),
                    "ARI": adjusted_rand_score(
                        rotulos_referencia,
                        modelo_reinicializado.labels_,
                    ),
                }
            )

        for indice_uf, localidade in enumerate(base["Localidade"]):
            mascara = np.arange(len(base)) != indice_uf
            base_sem_uf = base.loc[mascara].reset_index(drop=True)
            ajuste_sem_uf = _ajustar_pipeline_agrupamento(
                base_sem_uf,
                VARIAVEIS_MULTIVARIADAS,
                k,
                random_state,
                100,
            )
            estabilidades.append(
                {
                    "K": k,
                    "Procedimento": "Retirada de UF",
                    "Repetição ou elemento": str(localidade),
                    "N UFs comparadas": len(base_sem_uf),
                    "ARI": adjusted_rand_score(
                        rotulos_referencia[mascara],
                        np.asarray(ajuste_sem_uf["rotulos"]),
                    ),
                }
            )

        for variavel_retirada in VARIAVEIS_MULTIVARIADAS:
            variaveis_reduzidas = [
                variavel
                for variavel in VARIAVEIS_MULTIVARIADAS
                if variavel != variavel_retirada
            ]
            ajuste_sem_variavel = _ajustar_pipeline_agrupamento(
                base,
                variaveis_reduzidas,
                k,
                random_state,
                100,
            )
            estabilidades.append(
                {
                    "K": k,
                    "Procedimento": "Retirada de variável",
                    "Repetição ou elemento": variavel_retirada,
                    "N UFs comparadas": len(base),
                    "ARI": adjusted_rand_score(
                        rotulos_referencia,
                        np.asarray(ajuste_sem_variavel["rotulos"]),
                    ),
                }
            )

        gerador = np.random.default_rng(random_state + k)
        for repeticao in range(repeticoes_subamostra):
            indices = np.sort(
                gerador.choice(len(base), size=total_subamostra, replace=False)
            )
            base_subamostra = base.iloc[indices].reset_index(drop=True)
            ajuste_subamostra = _ajustar_pipeline_agrupamento(
                base_subamostra,
                VARIAVEIS_MULTIVARIADAS,
                k,
                random_state,
                100,
            )
            rotulos_preditos = _predizer_pipeline_agrupamento(
                ajuste_subamostra,
                base,
                VARIAVEIS_MULTIVARIADAS,
            )
            estabilidades.append(
                {
                    "K": k,
                    "Procedimento": "Subamostra de 80%",
                    "Repetição ou elemento": str(repeticao + 1),
                    "N UFs comparadas": len(base),
                    "ARI": adjusted_rand_score(
                        rotulos_referencia,
                        rotulos_preditos,
                    ),
                }
            )

        estabilidade_k = pd.DataFrame(
            [registro for registro in estabilidades if registro["K"] == k]
        )
        ari_reinicializacao = estabilidade_k.loc[
            estabilidade_k["Procedimento"].eq("Reinicialização"), "ARI"
        ]
        ari_retirada_uf = estabilidade_k.loc[
            estabilidade_k["Procedimento"].eq("Retirada de UF"), "ARI"
        ]
        ari_retirada_variavel = estabilidade_k.loc[
            estabilidade_k["Procedimento"].eq("Retirada de variável"), "ARI"
        ]
        ari_subamostra = estabilidade_k.loc[
            estabilidade_k["Procedimento"].eq("Subamostra de 80%"), "ARI"
        ]

        silhouette_medio = float(
            silhouette_score(escores_referencia, rotulos_referencia)
        )
        ari_mediano_reinicializacoes = float(ari_reinicializacao.median())
        ari_minimo_retirada_uf = float(ari_retirada_uf.min())
        ari_minimo_retirada_variavel = float(ari_retirada_variavel.min())
        ari_p10_subamostras = float(ari_subamostra.quantile(0.10))

        criterios = {
            "Atende silhouette": (
                silhouette_medio >= CRITERIOS_ACEITACAO_AGRUPAMENTOS["Silhouette médio"]
            ),
            "Atende tamanho mínimo": (
                int(tamanhos.min())
                >= CRITERIOS_ACEITACAO_AGRUPAMENTOS["Menor agrupamento (UFs)"]
            ),
            "Atende reinicializações": (
                ari_mediano_reinicializacoes
                >= CRITERIOS_ACEITACAO_AGRUPAMENTOS["ARI mediano — reinicializações"]
            ),
            "Atende retirada de UF": (
                ari_minimo_retirada_uf
                >= CRITERIOS_ACEITACAO_AGRUPAMENTOS["ARI mínimo — retirada de UF"]
            ),
            "Atende retirada de variável": (
                ari_minimo_retirada_variavel
                >= CRITERIOS_ACEITACAO_AGRUPAMENTOS["ARI mínimo — retirada de variável"]
            ),
            "Atende subamostras": (
                ari_p10_subamostras
                >= CRITERIOS_ACEITACAO_AGRUPAMENTOS["ARI P10 — subamostras"]
            ),
        }
        avaliacoes.append(
            {
                "K": k,
                "Componentes PCA utilizadas": int(
                    ajuste_referencia["quantidade_componentes_retidos"]
                ),
                "Silhouette médio": silhouette_medio,
                "Calinski–Harabasz": float(
                    calinski_harabasz_score(
                        escores_referencia,
                        rotulos_referencia,
                    )
                ),
                "Davies–Bouldin": float(
                    davies_bouldin_score(escores_referencia, rotulos_referencia)
                ),
                "Tamanhos dos agrupamentos": "; ".join(
                    str(int(tamanho)) for tamanho in sorted(tamanhos, reverse=True)
                ),
                "Menor agrupamento (UFs)": int(tamanhos.min()),
                "ARI mediano — reinicializações": ari_mediano_reinicializacoes,
                "ARI mínimo — retirada de UF": ari_minimo_retirada_uf,
                "ARI mínimo — retirada de variável": ari_minimo_retirada_variavel,
                "ARI mediano — subamostras": float(ari_subamostra.median()),
                "ARI P10 — subamostras": ari_p10_subamostras,
                **criterios,
                "Critérios atendidos (de 6)": int(sum(criterios.values())),
                "Decisão": "Aceita" if all(criterios.values()) else "Rejeitada",
            }
        )

    avaliacao = pd.DataFrame(avaliacoes).sort_values("K").reset_index(drop=True)
    melhor_k = int(
        avaliacao.sort_values(
            ["Silhouette médio", "K"],
            ascending=[False, True],
        ).iloc[0]["K"]
    )
    avaliacao["Melhor silhouette"] = avaliacao["K"].eq(melhor_k)

    ajuste_diagnostico = ajustes_referencia[melhor_k]
    escores_diagnostico = np.asarray(ajuste_diagnostico["escores"])
    rotulos_diagnostico = np.asarray(ajuste_diagnostico["rotulos"])
    silhouettes_individuais = silhouette_samples(
        escores_diagnostico,
        rotulos_diagnostico,
    )
    centroides = pd.DataFrame(escores_diagnostico).groupby(rotulos_diagnostico).mean()
    ordem_rotulos = centroides.sort_values(
        list(centroides.columns),
        ascending=[False, *([True] * (centroides.shape[1] - 1))],
    ).index.tolist()
    mapa_rotulos = {
        rotulo: f"G{ordem + 1}" for ordem, rotulo in enumerate(ordem_rotulos)
    }
    tamanhos_diagnostico = pd.Series(rotulos_diagnostico).value_counts()
    ufs_sinalizadas = set(
        detectar_valores_atipicos(base)
        .loc[lambda dados: dados["Sinalizada"], "Localidade"]
        .astype(str)
    )

    atribuicoes = base[["Localidade", "Região"]].copy()
    atribuicoes["K diagnóstico"] = melhor_k
    atribuicoes["Agrupamento diagnóstico"] = [
        mapa_rotulos[rotulo] for rotulo in rotulos_diagnostico
    ]
    atribuicoes["Tamanho do agrupamento"] = [
        int(tamanhos_diagnostico.loc[rotulo]) for rotulo in rotulos_diagnostico
    ]
    for indice_componente in range(escores_diagnostico.shape[1]):
        atribuicoes[f"PC{indice_componente + 1}"] = escores_diagnostico[
            :, indice_componente
        ]
    atribuicoes["Silhouette individual"] = silhouettes_individuais
    atribuicoes["Sinalizada previamente como atípica"] = atribuicoes["Localidade"].isin(
        ufs_sinalizadas
    )
    atribuicoes["Solução aceita como segmentação"] = False
    atribuicoes = atribuicoes.sort_values(
        ["Agrupamento diagnóstico", "PC1", "Localidade"],
        ascending=[True, False, True],
    ).reset_index(drop=True)

    estabilidade = (
        pd.DataFrame(estabilidades)
        .sort_values(["K", "Procedimento", "Repetição ou elemento"])
        .reset_index(drop=True)
    )
    return {
        "avaliacao": avaliacao,
        "estabilidade": estabilidade,
        "atribuicoes_diagnosticas": atribuicoes,
        "k_diagnostico": melhor_k,
    }


def exportar_base_estatistica(
    base: pd.DataFrame,
    caminho_saida: str | Path,
) -> Path:
    """Valida e exporta a base estatística em CSV."""

    validar_base_estatistica(base)

    caminho = Path(caminho_saida)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    base.to_csv(caminho, index=False)

    return caminho
