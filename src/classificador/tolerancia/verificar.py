"""Verifica se a espessura real está dentro da tolerância da nominal.

Tabela escolhida pelo LE mínimo do grau (quando a norma tem várias, como a NBR 7013); linha pela
espessura nominal; coluna pela largura. Limite inclusive. Sempre a coluna de tolerâncias normais.
"""

from dataclasses import dataclass
from decimal import Decimal

from classificador.dominio.amostra import Amostra
from classificador.dominio.formatacao import num
from classificador.dominio.modelos import Grau, NormaTolerancia
from classificador.dominio.propriedades import Propriedade


@dataclass(frozen=True)
class ResultadoTolerancia:
    dentro: bool | None  # None = não avaliada (o motivo está no texto)
    texto: str
    tolerancia: Decimal | None = None  # ± mm, já com acréscimos
    minimo: Decimal | None = None
    maximo: Decimal | None = None


def _nao_avaliada(motivo: str) -> ResultadoTolerancia:
    return ResultadoTolerancia(None, f"Tolerância não avaliada: {motivo}")


def verificar_tolerancia(
    amostra: Amostra, grau: Grau | None, norma: NormaTolerancia
) -> ResultadoTolerancia:
    faltando = [
        nome
        for nome, valor in (
            ("a espessura nominal", amostra.espessura_nominal),
            ("a espessura real", amostra.espessura_real),
            ("a largura", amostra.largura),
        )
        if valor is None
    ]
    if faltando:
        return _nao_avaliada(f"informe {', '.join(faltando)}")

    # Tabela: a única sem faixa de LE, ou a da faixa do LE mínimo do grau
    if all(t.le_min is None for t in norma.tabelas):
        tabela = norma.tabelas[0]
    else:
        limite_le = grau.limites.get(Propriedade.LE) if grau else None
        if limite_le is None or limite_le.min is None:
            # Grau sem LE definido, ou resultado fixo sem grau (ZC, 1006/08): a norma indica a
            # tabela (NBR 7013 → Tabela 2). Decisão do usuário (2026-10-28).
            if norma.tabela_sem_le is None:
                return _nao_avaliada(
                    f"o grau não tem LE mínimo para escolher a tabela da {norma.codigo}"
                )
            tabela = next(t for t in norma.tabelas if t.nome == norma.tabela_sem_le)
        else:
            le_min = limite_le.min
            tabela = next(
                (t for t in norma.tabelas if t.le_min and t.le_min.contem(le_min)), None
            )
            if tabela is None:
                return _nao_avaliada(
                    f"LE mínimo {num(le_min)} MPa fora das tabelas da {norma.codigo}"
                )

    nominal = amostra.espessura_nominal
    linha = next((ln for ln in tabela.linhas if ln.espessura.contem(nominal)), None)
    if linha is None:
        return _nao_avaliada(
            f"espessura nominal {num(nominal)} mm fora da {tabela.nome} da {norma.codigo}"
        )
    tolerancia = linha.tolerancias[norma.coluna(amostra.largura)]
    if tolerancia is None:
        return _nao_avaliada(
            f"tolerância não definida na norma para {num(nominal)} mm e largura "
            f"{num(amostra.largura)} mm ({norma.codigo}, {tabela.nome})"
        )

    detalhe = f"± {num(tolerancia)}"
    for acrescimo in norma.acrescimos:
        if (
            amostra.acabamento in acrescimo.acabamentos
            and amostra.camada is not None
            and amostra.camada >= acrescimo.camada_min
        ):
            tolerancia += acrescimo.valor
            detalhe = (
                f"± {num(tolerancia)}, com +{num(acrescimo.valor)} do revestimento "
                f"≥ {num(acrescimo.camada_min)} g/m²"
            )

    minimo, maximo = nominal - tolerancia, nominal + tolerancia
    dentro = minimo <= amostra.espessura_real <= maximo
    texto = (
        f"{'Dentro' if dentro else 'Fora'} da tolerância: {num(minimo)} a {num(maximo)} mm "
        f"({detalhe}) — {norma.codigo}, {tabela.nome}"
    )
    return ResultadoTolerancia(dentro, texto, tolerancia, minimo, maximo)
