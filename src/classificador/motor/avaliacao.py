"""Avalia se uma amostra atende um grau: lista cada falha com valor e limite.

Regras de valores vazios (CLAUDE.md / ADR 0005):
- vazio vale zero e entra em `faltando`;
- embutimento vazio não é avaliado;
- Lo50 vazio com Lo80 preenchido (ou o contrário), quando o grau limita os dois: o vazio não é
  avaliado.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Literal

from classificador.dominio.amostra import Amostra
from classificador.dominio.formatacao import num
from classificador.dominio.modelos import Grau
from classificador.dominio.propriedades import Propriedade
from classificador.motor.limites import LimitesEfetivos

_ALONGAMENTOS = {Propriedade.AL_LO50: Propriedade.AL_LO80, Propriedade.AL_LO80: Propriedade.AL_LO50}


@dataclass(frozen=True)
class Falha:
    variavel: str  # rótulo da propriedade ou da soma, ex.: "LE", "Ti + Nb"
    valor: Decimal  # valor comparado (zero se estava vazio)
    limite: Decimal
    lado: Literal["min", "max"]
    vazio: bool = False
    propriedade: Propriedade | None = None  # None quando a falha é de uma soma

    @property
    def texto(self) -> str:
        valor = "vazio" if self.vazio else num(self.valor)
        sinal, nome = ("<", "mín") if self.lado == "min" else (">", "máx")
        return f"{self.variavel} ({valor} {sinal} {num(self.limite)} {nome})"


@dataclass(frozen=True)
class Avaliacao:
    grau: Grau
    falhas: list[Falha] = field(default_factory=list)
    faltando: list[Propriedade] = field(default_factory=list)  # vazios tratados como zero
    nao_avaliados: list[Propriedade] = field(default_factory=list)

    @property
    def atende(self) -> bool:
        return not self.falhas


def avaliar_grau(grau: Grau, efetivos: LimitesEfetivos, amostra: Amostra) -> Avaliacao:
    falhas: list[Falha] = []
    faltando: list[Propriedade] = []
    nao_avaliados: list[Propriedade] = []

    for prop, limite in efetivos.limites.items():
        if not amostra.preenchido(prop):
            if _pula_vazio(prop, efetivos, amostra):
                nao_avaliados.append(prop)
                continue
            faltando.append(prop)
        valor = amostra.valor(prop) or Decimal(0)
        vazio = not amostra.preenchido(prop)
        if limite.min is not None and valor < limite.min:
            falhas.append(Falha(prop.rotulo, valor, limite.min, "min", vazio, prop))
        if limite.max is not None and valor > limite.max:
            falhas.append(Falha(prop.rotulo, valor, limite.max, "max", vazio, prop))

    for soma in grau.somas:
        for elemento in soma.elementos:
            if not amostra.preenchido(elemento) and elemento not in faltando:
                faltando.append(elemento)
        total = sum((amostra.valor(e) or Decimal(0) for e in soma.elementos), Decimal(0))
        if total > soma.max:
            nome = " + ".join(e.rotulo for e in soma.elementos)
            falhas.append(Falha(nome, total, soma.max, "max"))

    return Avaliacao(grau, falhas, faltando, nao_avaliados)


def _pula_vazio(prop: Propriedade, efetivos: LimitesEfetivos, amostra: Amostra) -> bool:
    """True se o campo vazio não deve ser avaliado (em vez de valer zero)."""
    if prop == Propriedade.EMBUTIMENTO:
        return True
    outro = _ALONGAMENTOS.get(prop)
    return outro is not None and outro in efetivos.limites and amostra.preenchido(outro)
