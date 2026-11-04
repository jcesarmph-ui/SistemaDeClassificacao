"""Aviso de valor fora do comum: compara cada valor digitado com o que costuma aparecer nas
classificações salvas do **mesmo acabamento e mesmo grau** (decisões do usuário, 2026-11-04).

- Só avalia um valor quando o grupo tem pelo menos `MINIMO_NO_GRUPO` (20) desse valor preenchido.
- Sensibilidade "só muito fora": avisa quando o valor se afasta da **mediana** mais de
  `VEZES` (4) vezes a **faixa central** (distância entre os quartis, onde ficam os 50 % do meio).
  Mediana e quartis não se deixam levar por um erro antigo no histórico (ao contrário da média).
- A faixa central nunca é considerada menor que meia margem da semelhança (`MARGENS`): se todos
  os C salvos forem 0,002, um 0,003 não é motivo de alarme.
- A espessura nominal não entra: muda conforme o pedido, não indica erro.
- O grupo usa o grau **certo** (o da divergência, quando houver): não se aprende com o erro.

Por que não o IsolationForest do scikit-learn: ele marca sempre uma fração fixa dos registros
como estranhos (mesmo todos normais) e não diz qual valor está fora.

O aviso é só um alerta amarelo: **nunca muda o resultado**, que é sempre o da norma.
"""

import numpy as np

from classificador.aprendizado.dados import CAMPOS, Exemplo, grau
from classificador.aprendizado.semelhanca import MARGENS
from classificador.dominio.propriedades import Propriedade

MINIMO_NO_GRUPO = 20
VEZES = 4.0
IGNORADOS = {"espessura_nominal"}


def numero_br(valor: float) -> str:
    """0.0015 → "0,0015"; 185.0 → "185"."""
    texto = f"{valor:.4f}".rstrip("0").rstrip(".")
    return texto.replace(".", ",")


def numero_faixa(valor: float) -> str:
    """Número arredondado para a faixa "costuma ficar entre": fácil de ler de relance.

    ≥ 10 → inteiro (269,6 → "270"); menor → 2 algarismos significativos (0,0468 → "0,047").
    """
    if abs(valor) >= 10:
        return numero_br(round(valor))
    return numero_br(float(f"{valor:.2g}"))


def avisos_fora_do_comum(
    exemplos: list[Exemplo], acabamento: str, resultado: str | None, numeros: tuple[float, ...],
) -> list[str]:
    """Um aviso por valor muito fora do comum para o acabamento e o grau; lista vazia se nenhum."""
    grau_agora = grau(resultado)
    if grau_agora is None:
        return []
    grupo = [e.numeros for e in exemplos
             if e.acabamento == acabamento and e.grau_certo == grau_agora]
    if len(grupo) < MINIMO_NO_GRUPO:
        return []
    tabela = np.array(grupo, dtype=float)

    avisos = []
    for i, campo in enumerate(CAMPOS):
        valor = numeros[i]
        coluna = tabela[:, i][~np.isnan(tabela[:, i])]
        if campo in IGNORADOS or np.isnan(valor) or len(coluna) < MINIMO_NO_GRUPO:
            continue
        mediana = float(np.median(coluna))
        q1, q3 = np.percentile(coluna, [25, 75])
        faixa = max(float(q3 - q1), MARGENS[campo].para(mediana) / 2)
        if abs(valor - mediana) > VEZES * faixa:
            de, ate = np.percentile(coluna, [5, 95])
            nome = Propriedade(campo).rotulo
            normal = f"costuma ficar entre {numero_faixa(de)} e {numero_faixa(ate)}"
            avisos.append(
                f"{nome} ({numero_br(valor)}) fora do comum para {grau_agora} em {acabamento} "
                f"({normal}). Confira a digitação."
            )
    return avisos
