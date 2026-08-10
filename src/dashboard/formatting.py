"""Formatação textual em português do Brasil."""


def formatar_inteiro(valor: float, sinal: bool = False) -> str:
    """Formata um número inteiro com separador brasileiro de milhares."""

    numero = round(valor)
    prefixo = "+" if sinal and numero > 0 else ""

    return prefixo + f"{numero:,}".replace(",", ".")


def formatar_percentual(
    valor: float | None,
    casas: int = 1,
    sinal: bool = False,
) -> str:
    """Formata uma proporção como percentual em português."""

    if valor is None:
        return "n/d"

    percentual = valor * 100
    prefixo = "+" if sinal and percentual > 0 else ""

    return prefixo + f"{percentual:.{casas}f}%".replace(".", ",")


def formatar_pontos_percentuais(
    valor: float,
    casas: int = 1,
) -> str:
    """Formata uma diferença proporcional em pontos percentuais."""

    return f"{abs(valor) * 100:.{casas}f} p.p.".replace(".", ",")
