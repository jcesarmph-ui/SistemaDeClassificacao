"""Limites que valem para um grau numa espessura: tabela + notas de rodapé + embutimento.

Usado pelo classificador e pela pesquisa reversa, para que os dois nunca discordem.
"""

from dataclasses import dataclass
from decimal import Decimal

from classificador.dominio.amostra import Acabamento
from classificador.dominio.modelos import Ajuste, Grau, Limite, Norma, TabelaEmbutimento
from classificador.dominio.propriedades import Propriedade


@dataclass(frozen=True)
class LimitesEfetivos:
    limites: dict[Propriedade, Limite]
    notas_aplicadas: list[str]  # referência das notas de rodapé que mudaram algum limite
    espessura_embutimento: Decimal | None = None  # linha da tabela de embutimento usada


def limites_efetivos(
    norma: Norma, grau: Grau, espessura: Decimal | None, acabamento: Acabamento | None = None
) -> LimitesEfetivos:
    """Limites do `grau` para a `espessura` nominal e o `acabamento` (None = não informado)."""
    limites = dict(grau.limites)

    # Para cada (propriedade, lado): a maior variação de cada motivo; motivos diferentes somam.
    escolhidas: dict[tuple[Propriedade, str], dict[str, tuple[Decimal, str]]] = {}
    removidas: dict[Propriedade, str] = {}
    for ajuste in norma.ajustes:
        if not _vale(ajuste, grau, espessura, acabamento):
            continue
        for prop in ajuste.remover:
            if prop in limites:
                removidas.setdefault(prop, ajuste.nota)
        for prop, variacao in ajuste.efeito.items():
            for lado in ("min", "max"):
                delta = getattr(variacao, lado)
                if delta is None or prop not in limites or getattr(limites[prop], lado) is None:
                    continue
                por_motivo = escolhidas.setdefault((prop, lado), {})
                atual = por_motivo.get(ajuste.motivo)
                if atual is None or abs(delta) > abs(atual[0]):
                    por_motivo[ajuste.motivo] = (delta, ajuste.nota)

    usadas: set[str] = set()
    for (prop, lado), por_motivo in escolhidas.items():
        if prop in removidas:
            continue
        campos = limites[prop].model_dump()
        campos[lado] += sum(delta for delta, _ in por_motivo.values())
        limites[prop] = Limite(**campos)  # revalida: uma nota não pode gerar mín > máx
        usadas |= {nota for _, nota in por_motivo.values()}
    for prop, nota in removidas.items():
        del limites[prop]
        usadas.add(nota)
    notas = list(dict.fromkeys(a.nota for a in norma.ajustes if a.nota in usadas))

    if espessura is None:
        return LimitesEfetivos(limites, notas)
    linha = _linha_embutimento(norma.tabela_embutimento, espessura)
    if linha is not None and grau.sigla in linha.minimos:
        limites[Propriedade.EMBUTIMENTO] = Limite(min=linha.minimos[grau.sigla])
        return LimitesEfetivos(limites, notas, linha.espessura)
    return LimitesEfetivos(limites, notas)


def _vale(
    ajuste: Ajuste, grau: Grau, espessura: Decimal | None, acabamento: Acabamento | None
) -> bool:
    """A nota vale para este grau, espessura e acabamento? (todas as condições dadas)"""
    if ajuste.graus is not None and grau.sigla not in ajuste.graus:
        return False
    if ajuste.quando is not None and (espessura is None or not ajuste.quando.contem(espessura)):
        return False
    return ajuste.acabamentos is None or acabamento in ajuste.acabamentos


def _linha_embutimento(tabela: TabelaEmbutimento | None, espessura: Decimal):
    """Linha mais próxima da espessura (empate → a maior); None fora da faixa da tabela."""
    if tabela is None:
        return None
    linhas = tabela.linhas
    if espessura < linhas[0].espessura or espessura > linhas[-1].espessura:
        return None
    # min() fica com o primeiro em caso de empate; percorrendo de trás para frente, é a linha maior
    return min(reversed(linhas), key=lambda linha: abs(linha.espessura - espessura))
