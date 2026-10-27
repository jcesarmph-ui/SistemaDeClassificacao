"""Formatação de números e notas de rodapé para o usuário (padrão brasileiro: vírgula decimal)."""

from decimal import Decimal

from classificador.dominio.modelos import Ajuste, FaixaEspessura


def num(valor: Decimal | int) -> str:
    """Número como foi escrito, com vírgula: Decimal("0.030") → "0,030"."""
    return str(valor).replace(".", ",")


def sinal(valor: Decimal | int) -> str:
    """Variação com sinal: 40 → "+40", -4 → "-4"."""
    return ("+" if valor > 0 else "") + num(valor)


def descrever_faixa(faixa: FaixaEspessura) -> str:
    """Faixa de espessura em texto: "e < 0,50 mm", "0,50 ≤ e ≤ 0,70 mm"."""
    texto = "e"
    if faixa.min is not None:
        texto = f"{num(faixa.min)} {'≤' if faixa.min_inclusivo else '<'} e"
    if faixa.max is not None:
        texto += f" {'≤' if faixa.max_inclusivo else '<'} {num(faixa.max)}"
    return f"{texto} mm"


def descrever_ajuste(ajuste: Ajuste) -> str:
    """Nota de rodapé em texto: "e < 0,50 mm: LE máx +40, alongamento Lo50 mín -4"."""
    efeitos = []
    for prop, variacao in ajuste.efeito.items():
        if variacao.min is not None:
            efeitos.append(f"{prop.rotulo} mín {sinal(variacao.min)}")
        if variacao.max is not None:
            efeitos.append(f"{prop.rotulo} máx {sinal(variacao.max)}")
    return f"{descrever_faixa(ajuste.quando)}: {', '.join(efeitos)}"
