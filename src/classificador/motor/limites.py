"""Limites que valem para um grau numa espessura: tabela + notas de rodapé + embutimento.

Usado pelo classificador e pela pesquisa reversa, para que os dois nunca discordem.
"""

from dataclasses import dataclass
from decimal import Decimal

from classificador.dominio.modelos import Grau, Limite, Norma, TabelaEmbutimento
from classificador.dominio.propriedades import Propriedade


@dataclass(frozen=True)
class LimitesEfetivos:
    limites: dict[Propriedade, Limite]
    notas_aplicadas: list[str]  # referência das notas de rodapé que mudaram algum limite
    espessura_embutimento: Decimal | None = None  # linha da tabela de embutimento usada


def limites_efetivos(norma: Norma, grau: Grau, espessura: Decimal | None) -> LimitesEfetivos:
    """Limites do `grau` para a `espessura` nominal (None = só os limites da tabela)."""
    limites = dict(grau.limites)
    if espessura is None:
        return LimitesEfetivos(limites, [])

    # Variação escolhida para cada (propriedade, lado): a de maior valor absoluto, sem acumular.
    escolhidas: dict[tuple[Propriedade, str], tuple[Decimal, str]] = {}
    for ajuste in norma.ajustes:
        if ajuste.graus is not None and grau.sigla not in ajuste.graus:
            continue
        if not ajuste.quando.contem(espessura):
            continue
        for prop, variacao in ajuste.efeito.items():
            for lado in ("min", "max"):
                delta = getattr(variacao, lado)
                if delta is None or prop not in limites or getattr(limites[prop], lado) is None:
                    continue
                atual = escolhidas.get((prop, lado))
                if atual is None or abs(delta) > abs(atual[0]):
                    escolhidas[(prop, lado)] = (delta, ajuste.nota)

    for (prop, lado), (delta, _) in escolhidas.items():
        campos = limites[prop].model_dump()
        campos[lado] += delta
        limites[prop] = Limite(**campos)  # revalida: uma nota não pode gerar mín > máx

    notas = list(dict.fromkeys(nota for _, nota in escolhidas.values()))

    linha = _linha_embutimento(norma.tabela_embutimento, espessura)
    if linha is not None and grau.sigla in linha.minimos:
        limites[Propriedade.EMBUTIMENTO] = Limite(min=linha.minimos[grau.sigla])
        return LimitesEfetivos(limites, notas, linha.espessura)
    return LimitesEfetivos(limites, notas)


def _linha_embutimento(tabela: TabelaEmbutimento | None, espessura: Decimal):
    """Linha mais próxima da espessura (empate → a maior); None fora da faixa da tabela."""
    if tabela is None:
        return None
    linhas = tabela.linhas
    if espessura < linhas[0].espessura or espessura > linhas[-1].espessura:
        return None
    # min() fica com o primeiro em caso de empate; percorrendo de trás para frente, é a linha maior
    return min(reversed(linhas), key=lambda linha: abs(linha.espessura - espessura))
