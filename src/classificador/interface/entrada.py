"""Converte o texto digitado na tela em números exatos e na `Amostra` do motor (sem Qt).

Vírgula ou ponto são separador decimal; "%" no fim é aceito e ignorado; não há separador de
milhar (largura 1244, não "1.244").
"""

import re
from collections.abc import Mapping
from decimal import Decimal

from classificador.dominio.amostra import Acabamento, Amostra
from classificador.dominio.propriedades import Propriedade

_NUMERO = re.compile(r"-?(\d+([.,]\d+)?|[.,]\d+)")  # o "-" é lido para avisar "negativo"

# Campos da tela que não são propriedades das normas
_OUTROS = {
    "espessura_nominal": "Espessura nominal",
    "espessura_real": "Espessura real",
    "largura": "Largura",
    "camada": "Camada",
}


class ErroEntrada(ValueError):
    """Valores digitados inválidos; a mensagem lista todos, um por linha."""


def ler_numero(texto: str) -> Decimal | None:
    """Texto da tela → Decimal exato; vazio → None. Aceita "46,7", "46.7" e "46,7 %"."""
    limpo = texto.strip().removesuffix("%").strip()
    if not limpo:
        return None
    if not _NUMERO.fullmatch(limpo):
        raise ValueError(f"'{texto.strip()}' não é um número")
    return Decimal(limpo.replace(",", "."))


def montar_amostra(acabamento: str, campos: Mapping[str, str]) -> Amostra:
    """Monta a Amostra a partir dos textos da tela; junta todos os erros numa mensagem só.

    `campos`: nome da propriedade (ex.: "LE", "Mn") ou de um dos campos extras
    (espessura_nominal, espessura_real, largura, camada) → texto digitado.
    """
    try:
        acabamento_ok = Acabamento(acabamento)
    except ValueError:
        raise ErroEntrada(f"acabamento '{acabamento}' desconhecido") from None

    erros: list[str] = []
    valores: dict[Propriedade, Decimal | None] = {}
    extras: dict[str, Decimal | None] = {}
    for nome, texto in campos.items():
        if nome in _OUTROS:
            rotulo, destino, chave = _OUTROS[nome], extras, nome
        else:
            prop = Propriedade(nome) if nome in Propriedade.__members__ else None
            if prop is None:
                raise KeyError(f"campo desconhecido na tela: {nome}")
            rotulo, destino, chave = prop.nome_extenso, valores, prop
        try:
            numero = ler_numero(texto)
        except ValueError as erro:
            erros.append(f"{rotulo}: {erro}")
            continue
        if numero is not None and numero < 0:
            erros.append(f"{rotulo}: não pode ser negativo")
            continue
        destino[chave] = numero

    if erros:
        raise ErroEntrada("\n".join(erros))
    return Amostra(acabamento=acabamento_ok, valores=valores, **extras)
