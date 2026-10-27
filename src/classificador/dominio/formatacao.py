"""Formatação de números para o usuário (padrão brasileiro: vírgula decimal)."""

from decimal import Decimal


def num(valor: Decimal | int) -> str:
    """Número como foi escrito, com vírgula: Decimal("0.030") → "0,030"."""
    return str(valor).replace(".", ",")
