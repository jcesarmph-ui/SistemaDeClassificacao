"""Transforma a classificação nos textos da tela: RESULTADO (sigla + camada), norma e avisos."""

from dataclasses import dataclass, field
from decimal import Decimal

from classificador.dominio.amostra import Amostra
from classificador.dominio.formatacao import num
from classificador.motor.sequencia import Classificacao


@dataclass(frozen=True)
class Saida:
    resultado: str | None  # ex.: "ZEE G2 - Z275"; None quando não há grau nem resultado padrão
    norma: str | None  # ex.: "De acordo com a norma NBR 5915-2:2013"
    avisos: list[str] = field(default_factory=list)
    correlatas: list[str] = field(default_factory=list)  # preenchidas a partir da Fase 3


def formatar(classificacao: Classificacao, amostra: Amostra) -> Saida:
    detalhe = classificacao.detalhe
    grau = classificacao.grau
    base = grau.sigla if grau else classificacao.resultado_padrao
    resultado = _com_camada(base, amostra) if base else None
    norma = f"De acordo com a norma {classificacao.norma.codigo}" if classificacao.norma else None

    avisos: list[str] = []
    if classificacao.aviso_sem_grau:
        avisos.append(classificacao.aviso_sem_grau)
    elif grau is None:
        avisos.append(f"Nenhum grau da {detalhe.norma.codigo} atendido")
    if detalhe.quase_passou:
        avisos.append(detalhe.quase_passou.texto)
    if detalhe.rebaixado_de and grau:
        avisos.append(
            f"Atende {detalhe.rebaixado_de.sigla}, que não existe para {amostra.acabamento}; "
            f"resultado no mais nobre disponível ({grau.sigla})"
        )
    if detalhe.faltando:
        nomes = ", ".join(p.rotulo for p in detalhe.faltando)
        avisos.append(f"Valores não informados (considerados zero): {nomes}")
    avaliacao = next((a for a in detalhe.avaliacoes if a.grau == grau), None)
    if avaliacao and avaliacao.nao_avaliados:
        nomes = ", ".join(p.rotulo for p in avaliacao.nao_avaliados)
        avisos.append(f"Não avaliado (outro campo preenchido / vazio): {nomes}")
    if amostra.espessura_nominal is None and (
        detalhe.norma.ajustes or detalhe.norma.tabela_embutimento
    ):
        avisos.append(
            "Espessura nominal não informada: notas de rodapé e embutimento não aplicados"
        )
    if detalhe.notas_aplicadas:
        avisos.append(f"Limites ajustados pela espessura: {', '.join(detalhe.notas_aplicadas)}")
    if grau:
        avisos += grau.avisos

    return Saida(resultado, norma, avisos)


def _com_camada(base: str, amostra: Amostra) -> str:
    revestimento = amostra.acabamento.revestimento
    if revestimento == "EG":
        if not amostra.tem_camada:
            return f"{base} EG"
        por_face = _camada(amostra.camada)
        return f"{base} EG {por_face}/{por_face}"
    if not amostra.tem_camada:
        return base
    if revestimento == "GI":
        return f"{base} - Z{_camada(amostra.camada)}"
    if revestimento == "GA":
        return f"{base} - ZF{_camada(amostra.camada)}"
    return base  # sem revestimento (FF, FQ, FQ DO): camada ignorada


def _camada(valor: Decimal) -> str:
    """Camada como digitada, sem zeros decimais à toa: 275.0 → "275", 7.5 → "7,5"."""
    return str(int(valor)) if valor == valor.to_integral_value() else num(valor.normalize())
