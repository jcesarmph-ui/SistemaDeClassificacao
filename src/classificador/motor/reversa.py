"""Pesquisa reversa: o que um grau exige de cada campo da tela, com ou sem espessura.

Usa `limites_efetivos`, a mesma função do classificador — os dois nunca discordam.
`pesquisar` aceita qualquer norma (NBR ou correlata, ex.: "DC04") via as normas correlatas.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal

from classificador.dominio.amostra import Acabamento
from classificador.dominio.formatacao import descrever_ajuste, num
from classificador.dominio.modelos import Correlatas, GrupoCorrelatas, Limite, Norma
from classificador.dominio.propriedades import Propriedade
from classificador.motor.limites import limites_efetivos


@dataclass(frozen=True)
class Requisito:
    propriedade: Propriedade
    limite: Limite

    @property
    def texto(self) -> str:
        """Ex.: "140 – 280 MPa", "≤ 0,12 %", "≥ 0,010 %"."""
        unidade = self.propriedade.unidade
        if self.limite.min is not None and self.limite.max is not None:
            return f"{num(self.limite.min)} – {num(self.limite.max)} {unidade}"
        if self.limite.max is not None:
            return f"≤ {num(self.limite.max)} {unidade}"
        return f"≥ {num(self.limite.min)} {unidade}"


@dataclass(frozen=True)
class Requisitos:
    norma: Norma
    sigla: str
    espessura: Decimal | None
    itens: list[Requisito]  # na ordem da tela: mecânicas, depois químicas
    somas: list[str] = field(default_factory=list)  # ex.: "Ti + Nb ≤ 0,20 %"
    notas: list[str] = field(default_factory=list)  # notas de rodapé que valem ou podem valer
    embutimento: str | None = None  # explicação do embutimento; None se o grau não tem
    avisos: list[str] = field(default_factory=list)


def requisitos(
    norma: Norma,
    sigla: str,
    espessura: Decimal | None = None,
    acabamento: Acabamento | None = None,
) -> Requisitos:
    grau = norma.grau(sigla)
    efetivos = limites_efetivos(norma, grau, espessura, acabamento)
    ordem = list(Propriedade)
    itens = [
        Requisito(prop, efetivos.limites[prop])
        for prop in sorted(efetivos.limites, key=ordem.index)
    ]
    somas = [
        f"{' + '.join(e.rotulo for e in s.elementos)} ≤ {num(s.max)} %" for s in grau.somas
    ]

    if espessura is None and acabamento is None:
        # Sem espessura: mostra as notas que valem para o grau, para o usuário saber que mudam
        notas = [
            f"{a.nota} — {descrever_ajuste(a)}"
            for a in norma.ajustes
            if a.graus is None or sigla in a.graus
        ]
    else:
        notas = [f"Aplicada: {nota}" for nota in efetivos.notas_aplicadas]

    return Requisitos(
        norma=norma,
        sigla=sigla,
        espessura=espessura,
        itens=itens,
        somas=somas,
        notas=notas,
        embutimento=_explicar_embutimento(norma, sigla, espessura, efetivos.espessura_embutimento),
        avisos=list(grau.avisos),
    )


def _explicar_embutimento(
    norma: Norma, sigla: str, espessura: Decimal | None, linha: Decimal | None
) -> str | None:
    tabela = norma.tabela_embutimento
    if tabela is None or not any(sigla in ln.minimos for ln in tabela.linhas):
        return None
    faixa = f"{num(tabela.linhas[0].espessura)} a {num(tabela.linhas[-1].espessura)} mm"
    if espessura is None:
        return f"Depende da espessura (tabela de {faixa})"
    if linha is None:
        return f"Não exigido: espessura fora da tabela ({faixa})"
    return f"Linha de {num(linha)} mm da tabela"


@dataclass(frozen=True)
class ResultadoPesquisa:
    grupo: GrupoCorrelatas  # grau NBR e suas equivalências
    requisitos: Requisitos | None  # None quando o programa não tem a norma (fora do escopo)


def pesquisar(
    texto: str,
    correlatas: Correlatas,
    normas: Mapping[str, Norma],
    espessura: Decimal | None = None,
    acabamento: Acabamento | None = None,
) -> list[ResultadoPesquisa]:
    """Pesquisa reversa por qualquer norma (NBR ou correlata), ex.: "DC04" → EEP G2."""
    resultados = []
    for grupo in correlatas.buscar(texto):
        norma = normas.get(grupo.norma) if grupo.norma else None
        exigido = requisitos(norma, grupo.grau, espessura, acabamento) if norma else None
        resultados.append(ResultadoPesquisa(grupo, exigido))
    return resultados
