"""Formatação de números e notas de rodapé para o usuário (padrão brasileiro: vírgula decimal)."""

from decimal import Decimal

from classificador.dominio.modelos import Ajuste, Faixa


def num(valor: Decimal | int) -> str:
    """Número como foi escrito, com vírgula: Decimal("0.030") → "0,030"."""
    return str(valor).replace(".", ",")


def sinal(valor: Decimal | int) -> str:
    """Variação com sinal: 40 → "+40", -4 → "-4"."""
    return ("+" if valor > 0 else "") + num(valor)


def descrever_faixa(faixa: Faixa, variavel: str = "e", unidade: str = "mm") -> str:
    """Faixa em texto: "e < 0,50 mm", "0,50 ≤ e ≤ 0,70 mm", "e ≥ 3,0 mm", "LE ≤ 260 MPa"."""
    if faixa.max is None:
        return f"{variavel} {'≥' if faixa.min_inclusivo else '>'} {num(faixa.min)} {unidade}"
    texto = variavel
    if faixa.min is not None:
        texto = f"{num(faixa.min)} {'≤' if faixa.min_inclusivo else '<'} {variavel}"
    return f"{texto} {'≤' if faixa.max_inclusivo else '<'} {num(faixa.max)} {unidade}"


def descrever_ajuste(ajuste: Ajuste) -> str:
    """Nota de rodapé em texto: "e < 0,50 mm: LE máx +40, alongamento Lo50 mín -4"."""
    condicoes = []
    if ajuste.quando is not None:
        condicoes.append(descrever_faixa(ajuste.quando))
    if ajuste.acabamentos:
        condicoes.append(f"acabamento {', '.join(ajuste.acabamentos)}")
    efeitos = []
    for prop, variacao in ajuste.efeito.items():
        if variacao.min is not None:
            efeitos.append(f"{prop.rotulo} mín {sinal(variacao.min)}")
        if variacao.max is not None:
            efeitos.append(f"{prop.rotulo} máx {sinal(variacao.max)}")
    texto = f"{' e '.join(condicoes)}: {', '.join(efeitos)}"
    if ajuste.remover:
        sem = ", ".join(p.rotulo for p in ajuste.remover)
        texto += f"{'; ' if efeitos else ''}sem exigência de {sem}"
    return texto
