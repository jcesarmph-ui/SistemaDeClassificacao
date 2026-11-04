"""Junta os avisos do ML para a tela, a cada CLASSIFICAR (decisões do usuário, 2026-11-04).

- Aparecem na área de avisos (amarelo), começando com "Histórico:" para saber que vieram do ML e
  não da norma; primeiro o caso parecido com divergência, depois os valores fora do comum.
- Entram nos avisos da classificação e, se ela for salva, ficam gravados no registro (o "retrato"
  do que a tela mostrou).
- O ML **aprende na hora**: lê o histórico a cada classificação, então uma divergência
  registrada agora já vale na próxima classificação, sem mudar código.
- Se o histórico não puder ser lido (ex.: rede fora), simplesmente não há avisos do ML: a
  classificação pela norma nunca depende dele.
"""

import sqlite3
from collections.abc import Mapping

from classificador.aprendizado.dados import exemplos, numeros
from classificador.aprendizado.fora_do_comum import avisos_fora_do_comum
from classificador.aprendizado.semelhanca import caso_parecido
from classificador.historico.repositorio import ErroDeValidacao, RepositorioHistorico

PREFIXO = "Histórico: "


def avisos_do_historico(
    repositorio: RepositorioHistorico | None,
    acabamento: str,
    resultado: str | None,
    valores: Mapping[str, str],
) -> list[str]:
    if repositorio is None or resultado is None:
        return []
    try:
        aprendidos = exemplos(repositorio)
    except (sqlite3.Error, ErroDeValidacao):
        return []
    agora = numeros(valores)
    avisos = []
    parecido = caso_parecido(aprendidos, acabamento, resultado, agora)
    if parecido is not None:
        avisos.append(parecido.aviso)
    avisos += avisos_fora_do_comum(aprendidos, acabamento, resultado, agora)
    return [PREFIXO + a for a in avisos]
