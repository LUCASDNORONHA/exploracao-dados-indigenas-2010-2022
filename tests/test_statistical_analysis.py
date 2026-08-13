from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from analysis.statistical_analysis import (
    COLUNAS_BASE_ESTATISTICA,
    CRITERIOS_ACEITACAO_AGRUPAMENTOS,
    INDICADORES_ATIPICIDADE,
    INDICADORES_DISTRIBUICAO,
    PARES_CORRELACAO,
    VARIAVEIS_MULTIVARIADAS,
    avaliar_agrupamentos_multivariados,
    calcular_correlacoes_spearman,
    calcular_curva_lorenz,
    calcular_estabilidade_ranking_populacional,
    calcular_influencia_correlacoes_leave_one_out,
    calcular_influencia_leave_one_out,
    calcular_medidas_concentracao,
    calcular_pca_multivariada,
    calcular_resumo_distribuicoes,
    calcular_sensibilidade_sem_sinalizadas,
    comparar_sensibilidade_escala,
    detectar_valores_atipicos,
    exportar_base_estatistica,
    preparar_base_estatistica,
    preparar_base_multivariada,
    resumir_estabilidade_ranking,
    resumir_valores_atipicos,
    validar_base_estatistica,
)

ROOT = Path(__file__).resolve().parents[1]
CAMINHO_FONTE = ROOT / "data" / "processed" / "table" / "df_state_profile.csv"
CAMINHO_BASE_ESTATISTICA = (
    ROOT / "data" / "processed" / "table" / "df_statistical_analysis.csv"
)
CAMINHO_RESUMO_DISTRIBUICOES = (
    ROOT / "outputs" / "tables" / "resumo_distribuicoes_estaduais.csv"
)
CAMINHO_MEDIDAS_CONCENTRACAO = (
    ROOT / "outputs" / "tables" / "medidas_concentracao_estadual_2022.csv"
)
CAMINHO_CURVA_LORENZ = ROOT / "outputs" / "tables" / "curva_lorenz_estadual_2022.csv"
CAMINHO_DIAGNOSTICO_ATIPICOS = (
    ROOT / "outputs" / "tables" / "diagnostico_valores_atipicos_estaduais.csv"
)
CAMINHO_RESUMO_ATIPICOS = (
    ROOT / "outputs" / "tables" / "resumo_valores_atipicos_estaduais.csv"
)
CAMINHO_SENSIBILIDADE_ESCALA = (
    ROOT / "outputs" / "tables" / "sensibilidade_escala_valores_atipicos.csv"
)
CAMINHO_INFLUENCIA = (
    ROOT / "outputs" / "tables" / "influencia_leave_one_out_estadual_2022.csv"
)
CAMINHO_SENSIBILIDADE_SEM_SINALIZADAS = (
    ROOT / "outputs" / "tables" / "sensibilidade_sem_ufs_sinalizadas.csv"
)
CAMINHO_CORRELACOES_SPEARMAN = (
    ROOT / "outputs" / "tables" / "correlacoes_spearman_estaduais.csv"
)
CAMINHO_RANKING_POPULACIONAL = (
    ROOT / "outputs" / "tables" / "estabilidade_ranking_populacional_2010_2022.csv"
)
CAMINHO_RESUMO_RANKING = (
    ROOT / "outputs" / "tables" / "resumo_estabilidade_ranking_populacional.csv"
)
CAMINHO_INFLUENCIA_CORRELACOES = (
    ROOT / "outputs" / "tables" / "influencia_correlacoes_leave_one_out.csv"
)
CAMINHO_BASE_MULTIVARIADA = (
    ROOT / "outputs" / "tables" / "base_multivariada_padronizada.csv"
)
CAMINHO_PCA_VARIANCIA = ROOT / "outputs" / "tables" / "pca_variancia_explicada.csv"
CAMINHO_PCA_CARGAS = ROOT / "outputs" / "tables" / "pca_cargas_variaveis.csv"
CAMINHO_PCA_ESCORES = ROOT / "outputs" / "tables" / "pca_escores_estaduais.csv"
CAMINHO_AVALIACAO_AGRUPAMENTOS = (
    ROOT / "outputs" / "tables" / "avaliacao_agrupamentos_estaduais.csv"
)
CAMINHO_ESTABILIDADE_AGRUPAMENTOS = (
    ROOT / "outputs" / "tables" / "estabilidade_agrupamentos_estaduais.csv"
)
CAMINHO_ATRIBUICOES_DIAGNOSTICAS = (
    ROOT / "outputs" / "tables" / "atribuicoes_agrupamento_diagnostico.csv"
)


@pytest.fixture(scope="module")
def fonte() -> pd.DataFrame:
    return pd.read_csv(CAMINHO_FONTE)


@pytest.fixture(scope="module")
def base(fonte: pd.DataFrame) -> pd.DataFrame:
    return preparar_base_estatistica(fonte)


@pytest.fixture(scope="module")
def resultado_pca(base: pd.DataFrame) -> dict[str, pd.DataFrame | int]:
    return calcular_pca_multivariada(base)


@pytest.fixture(scope="module")
def resultado_agrupamentos(
    base: pd.DataFrame,
) -> dict[str, pd.DataFrame | int]:
    return avaliar_agrupamentos_multivariados(base)


def test_base_estatistica_respeita_contrato(base: pd.DataFrame) -> None:
    assert base.shape == (27, len(COLUNAS_BASE_ESTATISTICA))
    assert base.columns.tolist() == COLUNAS_BASE_ESTATISTICA
    assert base["Localidade"].nunique() == 27
    assert set(base["Região"]) == {
        "Norte",
        "Nordeste",
        "Centro-Oeste",
        "Sudeste",
        "Sul",
    }


def test_indicadores_derivados_preservam_identidades(
    base: pd.DataFrame,
) -> None:
    resultados = validar_base_estatistica(base)

    assert all(resultados.values())
    np.testing.assert_allclose(
        np.exp(base["Crescimento logarítmico"]),
        base["Fator de crescimento (2022/2010)"],
    )
    np.testing.assert_allclose(
        base["Mudança na presença em TI (p.p.)"],
        base["Presença em TI 2022 (%)"] - base["Presença em TI 2010 (%)"],
    )


def test_ausencias_em_ti_sao_estruturais(base: pd.DataFrame) -> None:
    ufs_sem_composicao_ti = set(base.loc[base["TI urbano (%)"].isna(), "Localidade"])

    assert ufs_sem_composicao_ti == {"Rio Grande do Norte", "Distrito Federal"}
    assert base.drop(columns="TI urbano (%)").notna().all().all()


def test_indicadores_de_referencia_permanecem_estaveis(
    base: pd.DataFrame,
) -> None:
    amazonas = base.loc[base["Localidade"] == "Amazonas"].iloc[0]

    assert amazonas["Indígenas 2022 Total"] == 490_935
    assert amazonas["Crescimento relativo (%)"] == pytest.approx(167.5191)
    assert amazonas["Presença em TI 2010 (%)"] == pytest.approx(70.5826)
    assert amazonas["Mudança na presença em TI (p.p.)"] == pytest.approx(
        -40.2161,
        abs=1e-4,
    )


def test_exportacao_preserva_a_base(
    base: pd.DataFrame,
    tmp_path: Path,
) -> None:
    caminho = exportar_base_estatistica(
        base,
        tmp_path / "df_statistical_analysis.csv",
    )
    recarregada = pd.read_csv(caminho)

    pd.testing.assert_frame_equal(recarregada, base, check_dtype=False)


def test_base_versionada_corresponde_ao_processamento(
    base: pd.DataFrame,
) -> None:
    publicada = pd.read_csv(CAMINHO_BASE_ESTATISTICA)

    pd.testing.assert_frame_equal(publicada, base, check_dtype=False)


def test_preparacao_rejeita_uf_duplicada(fonte: pd.DataFrame) -> None:
    invalida = pd.concat([fonte.iloc[:-1], fonte.iloc[[0]]], ignore_index=True)

    with pytest.raises(ValueError, match="UFs duplicadas"):
        preparar_base_estatistica(invalida)


def test_resumo_distribuicoes_calcula_medidas_robustas(
    base: pd.DataFrame,
) -> None:
    resumo = calcular_resumo_distribuicoes(base)
    populacao = resumo.set_index("Indicador").loc["Indígenas 2022 Total"]

    assert resumo["Indicador"].tolist() == INDICADORES_DISTRIBUICAO
    assert resumo.shape == (6, 13)
    assert populacao["N"] == 27
    assert populacao["Ausentes"] == 0
    assert populacao["Mediana"] == pytest.approx(30_466)
    assert populacao["IQR"] == pytest.approx(39_505.5)
    assert populacao["MAD"] == pytest.approx(19_132)
    assert populacao["Assimetria"] == pytest.approx(3.6090, abs=1e-4)


def test_curva_lorenz_respeita_limites_e_monotonicidade(
    base: pd.DataFrame,
) -> None:
    curva = calcular_curva_lorenz(base["Indígenas 2022 Total"])

    assert curva.shape == (28, 2)
    np.testing.assert_allclose(curva.iloc[0].to_numpy(), [0.0, 0.0])
    np.testing.assert_allclose(curva.iloc[-1].to_numpy(), [1.0, 1.0])
    assert curva.diff().dropna().ge(0).all().all()


def test_medidas_concentracao_permanecem_estaveis(
    base: pd.DataFrame,
) -> None:
    medidas = calcular_medidas_concentracao(base).iloc[0]

    assert medidas["Total de UFs"] == 27
    assert medidas["População total"] == 1_694_836
    assert medidas["Gini"] == pytest.approx(0.584198, abs=1e-6)
    assert medidas["HHI"] == pytest.approx(0.124052, abs=1e-6)
    assert medidas["Número efetivo de UFs"] == pytest.approx(8.061138, abs=1e-6)
    assert medidas["CR3 (%)"] == pytest.approx(49.376282, abs=1e-6)
    assert medidas["CR5 (%)"] == pytest.approx(61.431372, abs=1e-6)
    assert medidas["UFs para alcançar 50%"] == 4


def test_distribuicao_igual_produz_gini_zero(base: pd.DataFrame) -> None:
    igual = base.copy()
    igual["Indígenas 2022 Total"] = 100
    medidas = calcular_medidas_concentracao(igual).iloc[0]

    assert medidas["Gini"] == pytest.approx(0.0, abs=1e-12)
    assert medidas["HHI"] == pytest.approx(1 / 27)
    assert medidas["Número efetivo de UFs"] == pytest.approx(27.0)
    assert medidas["UFs para alcançar 50%"] == 14


def test_concentracao_rejeita_valores_negativos(base: pd.DataFrame) -> None:
    invalida = base.copy()
    invalida.loc[0, "Indígenas 2022 Total"] = -1

    with pytest.raises(ValueError, match="não podem ser negativos"):
        calcular_medidas_concentracao(invalida)


def test_tabelas_versionadas_correspondem_aos_calculos(
    base: pd.DataFrame,
) -> None:
    resumo_publicado = pd.read_csv(CAMINHO_RESUMO_DISTRIBUICOES)
    concentracao_publicada = pd.read_csv(CAMINHO_MEDIDAS_CONCENTRACAO)
    lorenz_publicada = pd.read_csv(CAMINHO_CURVA_LORENZ)

    pd.testing.assert_frame_equal(
        resumo_publicado,
        calcular_resumo_distribuicoes(base),
        check_dtype=False,
    )
    pd.testing.assert_frame_equal(
        concentracao_publicada,
        calcular_medidas_concentracao(base),
        check_dtype=False,
    )
    pd.testing.assert_frame_equal(
        lorenz_publicada,
        calcular_curva_lorenz(base["Indígenas 2022 Total"]),
        check_dtype=False,
    )


def test_diagnostico_atipicidade_combina_tukey_e_mad(
    base: pd.DataFrame,
) -> None:
    diagnostico = detectar_valores_atipicos(base)
    resumo = resumir_valores_atipicos(diagnostico).set_index("Indicador")

    assert diagnostico.shape == (27 * len(INDICADORES_ATIPICIDADE), 21)
    assert set(diagnostico["Indicador"]) == set(INDICADORES_ATIPICIDADE)
    assert resumo.loc["Indígenas 2022 Total", "UFs sinalizadas"] == ("Amazonas; Bahia")
    assert resumo.loc["Crescimento relativo (%)", "Sinalizadas por Tukey"] == 4
    assert resumo.loc["Crescimento relativo (%)", "Sinalizadas por MAD"] == 2
    assert resumo.loc["Urbanização 2022 (%)", "Sinalizadas pela união"] == 0
    assert (
        resumo.loc["Mudança na presença em TI (p.p.)", "UFs sinalizadas"] == "Amazonas"
    )


def test_sinalizacao_nao_altera_base_e_classifica_concordancia(
    base: pd.DataFrame,
) -> None:
    original = base.copy(deep=True)
    diagnostico = detectar_valores_atipicos(base)
    crescimento = diagnostico.loc[
        diagnostico["Indicador"].eq("Crescimento relativo (%)")
        & diagnostico["Sinalizada"]
    ].set_index("Localidade")

    assert crescimento.loc["Bahia", "Concordância"] == "Ambos os critérios"
    assert crescimento.loc["Rio Grande do Norte", "Concordância"] == (
        "Ambos os critérios"
    )
    assert crescimento.loc["Ceará", "Concordância"] == "Somente Tukey"
    assert crescimento.loc["Amazonas", "Concordância"] == "Somente Tukey"
    pd.testing.assert_frame_equal(base, original)


def test_sensibilidade_de_escala_explicita_mudancas_de_classificacao(
    base: pd.DataFrame,
) -> None:
    comparacao = comparar_sensibilidade_escala(base)
    mudancas = comparacao.loc[
        comparacao["Mudou com a transformação"],
        ["Dimensão", "Localidade"],
    ]

    assert comparacao.shape == (54, 9)
    assert set(map(tuple, mudancas.to_numpy())) == {
        ("Magnitude populacional", "Bahia"),
        ("Crescimento populacional", "Ceará"),
        ("Crescimento populacional", "Amazonas"),
    }


def test_influencia_leave_one_out_identifica_amazonas(
    base: pd.DataFrame,
) -> None:
    influencia = calcular_influencia_leave_one_out(base)
    amazonas = influencia.iloc[0]

    assert influencia.shape == (27, 18)
    assert amazonas["UF retirada hipoteticamente"] == "Amazonas"
    assert amazonas["Rank de influência"] == 1
    assert amazonas["Métrica de maior variação"] == "HHI"
    assert amazonas["Variação da média (%)"] == pytest.approx(-26.234463)
    assert amazonas["Variação da mediana (%)"] == pytest.approx(-0.535023)
    assert amazonas["Variação do HHI (%)"] == pytest.approx(-35.862373)


def test_sensibilidade_sem_sinalizadas_contrasta_media_e_mediana(
    base: pd.DataFrame,
) -> None:
    diagnostico = detectar_valores_atipicos(base)
    sensibilidade = calcular_sensibilidade_sem_sinalizadas(
        base,
        diagnostico,
    ).set_index("Indicador")
    populacao = sensibilidade.loc["Indígenas 2022 Total"]

    assert populacao["Quantidade de UFs sinalizadas"] == 2
    assert populacao["Variação da média (%)"] == pytest.approx(-37.904633)
    assert populacao["Variação da mediana (%)"] == pytest.approx(-1.070045)
    assert (
        sensibilidade.loc["Urbanização 2022 (%)", "Quantidade de UFs sinalizadas"] == 0
    )


def test_tabelas_de_atipicidade_versionadas_correspondem_aos_calculos(
    base: pd.DataFrame,
) -> None:
    diagnostico = detectar_valores_atipicos(base)
    tabelas = {
        CAMINHO_DIAGNOSTICO_ATIPICOS: diagnostico,
        CAMINHO_RESUMO_ATIPICOS: resumir_valores_atipicos(diagnostico),
        CAMINHO_SENSIBILIDADE_ESCALA: comparar_sensibilidade_escala(base),
        CAMINHO_INFLUENCIA: calcular_influencia_leave_one_out(base),
        CAMINHO_SENSIBILIDADE_SEM_SINALIZADAS: (
            calcular_sensibilidade_sem_sinalizadas(base, diagnostico)
        ),
    }

    for caminho, calculada in tabelas.items():
        publicada = pd.read_csv(caminho)
        pd.testing.assert_frame_equal(publicada, calculada, check_dtype=False)


def test_correlacoes_spearman_preservam_pares_justificados(
    base: pd.DataFrame,
) -> None:
    correlacoes = calcular_correlacoes_spearman(base).set_index("Relação")

    assert len(correlacoes) == len(PARES_CORRELACAO) == 7
    assert "Valor-p" not in correlacoes.columns
    assert correlacoes.loc[
        "Persistência da magnitude populacional", "Spearman (ρ)"
    ] == pytest.approx(0.967033, abs=1e-6)
    assert correlacoes.loc[
        "Urbanização × presença em TI em 2022", "Spearman (ρ)"
    ] == pytest.approx(-0.831934, abs=1e-6)
    assert correlacoes.loc["Urbanização em TI × fora de TI em 2022", "N"] == 25
    assert (
        correlacoes.loc["Urbanização em TI × fora de TI em 2022", "Ausentes pareados"]
        == 2
    )


def test_spearman_corresponde_a_correlacao_entre_postos(
    base: pd.DataFrame,
) -> None:
    correlacoes = calcular_correlacoes_spearman(base)
    persistencia = correlacoes.loc[
        correlacoes["Relação"].eq("Persistência da magnitude populacional")
    ].iloc[0]
    rho_esperado = (
        base["Indígenas 2010 Total"].rank().corr(base["Indígenas 2022 Total"].rank())
    )

    assert persistencia["Spearman (ρ)"] == pytest.approx(rho_esperado)


def test_estabilidade_do_ranking_identifica_movimentos_principais(
    base: pd.DataFrame,
) -> None:
    ranking = calcular_estabilidade_ranking_populacional(base).set_index("Localidade")
    resumo = resumir_estabilidade_ranking(ranking.reset_index()).iloc[0]

    assert ranking.shape == (27, 8)
    assert ranking.loc["Ceará", "Posição em 2010"] == 14
    assert ranking.loc["Ceará", "Posição em 2022"] == 9
    assert ranking.loc["Ceará", "Variação no ranking (posições)"] == 5
    assert ranking.loc["Rio de Janeiro", "Movimento"] == "Desceu"
    assert resumo["Spearman entre rankings (ρ)"] == pytest.approx(0.967033)
    assert resumo["Mediana da mudança absoluta"] == pytest.approx(2.0)
    assert resumo["UFs que mais subiram"] == "Ceará"
    assert resumo["Retenção Top 5 (%)"] == pytest.approx(100.0)
    assert resumo["Retenção Top 10 (%)"] == pytest.approx(90.0)


def test_influencia_das_correlacoes_nao_remove_ufs(
    base: pd.DataFrame,
) -> None:
    original = base.copy(deep=True)
    influencia = calcular_influencia_correlacoes_leave_one_out(base)
    crescimento_urbanizacao = influencia.loc[
        influencia["Relação"].eq("Crescimento × mudança da urbanização")
        & influencia["Rank de influência na relação"].eq(1)
    ].iloc[0]

    assert influencia.shape == (187, 13)
    assert crescimento_urbanizacao["UF retirada hipoteticamente"] == (
        "Rio Grande do Norte"
    )
    assert crescimento_urbanizacao["Variação de ρ"] == pytest.approx(
        0.160147,
        abs=1e-6,
    )
    pd.testing.assert_frame_equal(base, original)


def test_tabelas_de_relacoes_versionadas_correspondem_aos_calculos(
    base: pd.DataFrame,
) -> None:
    ranking = calcular_estabilidade_ranking_populacional(base)
    tabelas = {
        CAMINHO_CORRELACOES_SPEARMAN: calcular_correlacoes_spearman(base),
        CAMINHO_RANKING_POPULACIONAL: ranking,
        CAMINHO_RESUMO_RANKING: resumir_estabilidade_ranking(ranking),
        CAMINHO_INFLUENCIA_CORRELACOES: (
            calcular_influencia_correlacoes_leave_one_out(base)
        ),
    }

    for caminho, calculada in tabelas.items():
        publicada = pd.read_csv(caminho)
        pd.testing.assert_frame_equal(publicada, calculada, check_dtype=False)


def test_padronizacao_multivariada_usa_mediana_e_iqr(
    base: pd.DataFrame,
) -> None:
    original = base.copy(deep=True)
    padronizada = preparar_base_multivariada(base)
    colunas_robustas = [
        f"{variavel} — escala robusta" for variavel in VARIAVEIS_MULTIVARIADAS
    ]

    assert padronizada.shape == (27, 14)
    np.testing.assert_allclose(
        padronizada[colunas_robustas].median().to_numpy(),
        np.zeros(len(colunas_robustas)),
        atol=1e-12,
    )
    np.testing.assert_allclose(
        (
            padronizada[colunas_robustas].quantile(0.75)
            - padronizada[colunas_robustas].quantile(0.25)
        ).to_numpy(),
        np.ones(len(colunas_robustas)),
        atol=1e-12,
    )
    pd.testing.assert_frame_equal(base, original)


def test_pca_retem_tres_componentes_e_preserva_variacao(
    resultado_pca: dict[str, pd.DataFrame | int],
) -> None:
    variancia = resultado_pca["variancia"]
    cargas = resultado_pca["cargas"]

    assert resultado_pca["quantidade_componentes_retidos"] == 3
    assert variancia["Componente retido"].tolist() == [
        True,
        True,
        True,
        False,
        False,
        False,
    ]
    assert variancia.loc[
        variancia["Componente retido"], "Variância explicada (%)"
    ].sum() == pytest.approx(91.862469, abs=1e-6)
    contribuicoes = cargas.groupby("Componente")["Contribuição ao componente (%)"].sum()
    np.testing.assert_allclose(contribuicoes.to_numpy(), np.full(6, 100.0))


def test_pca_explicita_as_dimensoes_dominantes(
    resultado_pca: dict[str, pd.DataFrame | int],
) -> None:
    cargas = resultado_pca["cargas"].set_index(["Componente", "Variável"])

    assert cargas.loc[
        ("PC1", "Mudança na presença em TI (p.p.)"),
        "Correlação variável–componente",
    ] == pytest.approx(-0.904074, abs=1e-6)
    assert cargas.loc[
        ("PC2", "Crescimento logarítmico"),
        "Correlação variável–componente",
    ] == pytest.approx(0.905750, abs=1e-6)
    assert cargas.loc[
        ("PC3", "Urbanização 2022 (%)"),
        "Correlação variável–componente",
    ] == pytest.approx(0.865095, abs=1e-6)


def test_agrupamentos_sao_rejeitados_pelo_protocolo_conservador(
    resultado_agrupamentos: dict[str, pd.DataFrame | int],
) -> None:
    avaliacao = resultado_agrupamentos["avaliacao"].set_index("K")

    assert resultado_agrupamentos["k_diagnostico"] == 4
    assert avaliacao.index.tolist() == [2, 3, 4, 5, 6]
    assert avaliacao["Decisão"].eq("Rejeitada").all()
    assert not avaliacao["Atende silhouette"].any()
    assert avaliacao.loc[4, "Silhouette médio"] == pytest.approx(0.406583)
    assert avaliacao.loc[4, "Menor agrupamento (UFs)"] == 2
    assert (
        avaliacao.loc[4, "ARI mínimo — retirada de variável"]
        < (CRITERIOS_ACEITACAO_AGRUPAMENTOS["ARI mínimo — retirada de variável"])
    )


def test_estabilidade_documenta_todas_as_perturbacoes(
    resultado_agrupamentos: dict[str, pd.DataFrame | int],
) -> None:
    estabilidade = resultado_agrupamentos["estabilidade"]
    contagens = estabilidade.groupby(["K", "Procedimento"]).size().unstack()

    assert estabilidade.shape == (1165, 5)
    assert (contagens["Reinicialização"] == 100).all()
    assert (contagens["Retirada de UF"] == 27).all()
    assert (contagens["Retirada de variável"] == 6).all()
    assert (contagens["Subamostra de 80%"] == 100).all()
    assert estabilidade["ARI"].between(-1, 1).all()


def test_solucao_diagnostica_isola_extremos_sem_virar_segmentacao(
    resultado_agrupamentos: dict[str, pd.DataFrame | int],
) -> None:
    atribuicoes = resultado_agrupamentos["atribuicoes_diagnosticas"]
    grupos = {
        frozenset(grupo["Localidade"])
        for _, grupo in atribuicoes.groupby("Agrupamento diagnóstico")
    }

    assert atribuicoes.shape == (27, 11)
    assert frozenset({"Amazonas", "Bahia"}) in grupos
    assert frozenset({"Rio Grande do Norte", "Piauí", "Ceará"}) in grupos
    assert not atribuicoes["Solução aceita como segmentação"].any()
    assert atribuicoes.loc[
        atribuicoes["Localidade"].eq("Amazonas"),
        "Sinalizada previamente como atípica",
    ].item()


def test_tabelas_multivariadas_versionadas_correspondem_aos_calculos(
    resultado_pca: dict[str, pd.DataFrame | int],
    resultado_agrupamentos: dict[str, pd.DataFrame | int],
) -> None:
    tabelas_deterministicas = {
        CAMINHO_BASE_MULTIVARIADA: resultado_pca["base_padronizada"],
        CAMINHO_PCA_VARIANCIA: resultado_pca["variancia"],
        CAMINHO_PCA_CARGAS: resultado_pca["cargas"],
        CAMINHO_PCA_ESCORES: resultado_pca["escores"],
    }

    for caminho, calculada in tabelas_deterministicas.items():
        publicada = pd.read_csv(caminho)
        pd.testing.assert_frame_equal(publicada, calculada, check_dtype=False)

    avaliacao_publicada = pd.read_csv(CAMINHO_AVALIACAO_AGRUPAMENTOS)
    avaliacao_calculada = resultado_agrupamentos["avaliacao"]
    colunas_decisao = [
        "K",
        "Componentes PCA utilizadas",
        "Tamanhos dos agrupamentos",
        "Menor agrupamento (UFs)",
        "Atende silhouette",
        "Atende tamanho mínimo",
        "Atende reinicializações",
        "Atende retirada de UF",
        "Atende retirada de variável",
        "Atende subamostras",
        "Critérios atendidos (de 6)",
        "Decisão",
        "Melhor silhouette",
    ]
    pd.testing.assert_frame_equal(
        avaliacao_publicada[colunas_decisao],
        avaliacao_calculada[colunas_decisao],
        check_dtype=False,
    )
    np.testing.assert_allclose(
        avaliacao_publicada["Silhouette médio"],
        avaliacao_calculada["Silhouette médio"],
        atol=1e-12,
    )

    estabilidade_publicada = pd.read_csv(CAMINHO_ESTABILIDADE_AGRUPAMENTOS)
    estabilidade_calculada = resultado_agrupamentos["estabilidade"]
    chaves_estabilidade = [
        "K",
        "Procedimento",
        "Repetição ou elemento",
        "N UFs comparadas",
    ]
    pd.testing.assert_frame_equal(
        estabilidade_publicada[chaves_estabilidade],
        estabilidade_calculada[chaves_estabilidade],
        check_dtype=False,
    )
    resumo_publicado = estabilidade_publicada.groupby(["K", "Procedimento"])[
        "ARI"
    ].median()
    resumo_calculado = estabilidade_calculada.groupby(["K", "Procedimento"])[
        "ARI"
    ].median()
    np.testing.assert_allclose(
        resumo_publicado,
        resumo_calculado,
        atol=0.01,
    )

    atribuicoes_publicadas = pd.read_csv(CAMINHO_ATRIBUICOES_DIAGNOSTICAS)
    pd.testing.assert_frame_equal(
        atribuicoes_publicadas,
        resultado_agrupamentos["atribuicoes_diagnosticas"],
        check_dtype=False,
    )
