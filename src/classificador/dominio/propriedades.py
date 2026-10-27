"""Propriedades que o usuário digita na tela e que as normas podem limitar.

O valor de cada item (ex.: "Mn") é o nome usado nos arquivos YAML das normas.
"""

from enum import StrEnum


class Propriedade(StrEnum):
    # Mecânicas
    LE = "LE"
    LR = "LR"
    AL_LO50 = "AL_LO50"
    AL_LO80 = "AL_LO80"
    EMBUTIMENTO = "EMBUTIMENTO"
    # Químicas — na ordem em que aparecem na tela
    C = "C"
    Mn = "Mn"
    P = "P"
    S = "S"
    Al = "Al"
    Ni = "Ni"
    Ti = "Ti"
    V = "V"
    Nb = "Nb"
    Cr = "Cr"
    Si = "Si"
    B = "B"
    Mo = "Mo"

    @property
    def nome_extenso(self) -> str:
        return _NOMES[self]

    @property
    def rotulo(self) -> str:
        """Nome curto usado nos avisos, ex.: "alongamento Lo50" ou "Mn"."""
        return _ROTULOS.get(self, self.value)

    @property
    def unidade(self) -> str:
        return _UNIDADES.get(self, "%")

    @classmethod
    def quimicas(cls) -> list["Propriedade"]:
        return [p for p in cls if p not in _MECANICAS]


_MECANICAS = {
    Propriedade.LE,
    Propriedade.LR,
    Propriedade.AL_LO50,
    Propriedade.AL_LO80,
    Propriedade.EMBUTIMENTO,
}

_ROTULOS = {
    Propriedade.AL_LO50: "alongamento Lo50",
    Propriedade.AL_LO80: "alongamento Lo80",
    Propriedade.EMBUTIMENTO: "embutimento",
}

_UNIDADES = {
    Propriedade.LE: "MPa",
    Propriedade.LR: "MPa",
    Propriedade.AL_LO50: "%",
    Propriedade.AL_LO80: "%",
    Propriedade.EMBUTIMENTO: "mm",
}

_NOMES = {
    Propriedade.LE: "Limite de escoamento",
    Propriedade.LR: "Limite de resistência",
    Propriedade.AL_LO50: "Alongamento (Lo = 50 mm)",
    Propriedade.AL_LO80: "Alongamento (Lo = 80 mm)",
    Propriedade.EMBUTIMENTO: "Embutimento Erichsen",
    Propriedade.C: "Carbono",
    Propriedade.Mn: "Manganês",
    Propriedade.P: "Fósforo",
    Propriedade.S: "Enxofre",
    Propriedade.Al: "Alumínio",
    Propriedade.Ni: "Níquel",
    Propriedade.Ti: "Titânio",
    Propriedade.V: "Vanádio",
    Propriedade.Nb: "Nióbio",
    Propriedade.Cr: "Cromo",
    Propriedade.Si: "Silício",
    Propriedade.B: "Boro",
    Propriedade.Mo: "Molibdênio",
}
