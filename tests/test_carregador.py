"""Testes do carregador: leitura do YAML, números exatos e mensagens de erro claras."""

from decimal import Decimal
from pathlib import Path

import pytest

from classificador.dominio.propriedades import Propriedade
from classificador.normas.carregador import ErroNorma, carregar_norma

NORMA_FICTICIA = Path(__file__).parent / "dados" / "norma-ficticia.yaml"


def escrever(tmp_path: Path, texto: str) -> Path:
    arquivo = tmp_path / "teste.yaml"
    arquivo.write_text(texto, encoding="utf-8")
    return arquivo


def test_carrega_norma_ficticia():
    norma = carregar_norma(NORMA_FICTICIA)
    assert norma.codigo == "NBR 0000-1:2026"
    assert [g.sigla for g in norma.graus] == ["AAA", "BBB G1"]
    assert norma.ajustes[0].efeito[Propriedade.LE].max == 40


def test_numeros_viram_decimal_exato_sem_passar_por_float():
    norma = carregar_norma(NORMA_FICTICIA)
    c_max = norma.grau("BBB G1").limites[Propriedade.C].max
    assert isinstance(c_max, Decimal)
    assert c_max == Decimal("0.007")
    # Decimal guarda a escrita original: 0.30 continua com duas casas
    assert str(norma.tabela_embutimento.linhas[0].espessura) == "0.30"


def test_arquivo_inexistente(tmp_path):
    with pytest.raises(ErroNorma, match="não encontrado"):
        carregar_norma(tmp_path / "nao-existe.yaml")


def test_erro_de_sintaxe_informa_a_linha(tmp_path):
    arquivo = escrever(tmp_path, "codigo: X\ngraus:\n  - sigla: [AAA\n")
    with pytest.raises(ErroNorma, match=r"teste\.yaml.*linha"):
        carregar_norma(arquivo)


def test_chave_repetida_e_recusada(tmp_path):
    texto = """\
codigo: X
titulo: Y
graus:
  - sigla: AAA
    nome_na_norma: AAA
    limites:
      C: {max: 0.10}
      C: {max: 0.20}
"""
    with pytest.raises(ErroNorma, match=r"linha 8.*'C' repetida"):
        carregar_norma(escrever(tmp_path, texto))


def test_valor_invalido_informa_linha_e_campo(tmp_path):
    texto = """\
codigo: X
titulo: Y
graus:
  - sigla: AAA
    nome_na_norma: AAA
    limites:
      LE: {min: 300, max: 200}
"""
    with pytest.raises(ErroNorma) as erro:
        carregar_norma(escrever(tmp_path, texto))
    mensagem = str(erro.value)
    assert "linha 7" in mensagem
    assert "graus → 1 → limites → LE" in mensagem
    assert "maior que o máximo" in mensagem


def test_campo_com_nome_errado_e_propriedade_desconhecida(tmp_path):
    texto = """\
codigo: X
titulo: Y
graus:
  - sigla: AAA
    nome_na_norma: AAA
    limites:
      Mb: {maximo: 0.10}
"""
    with pytest.raises(ErroNorma) as erro:
        carregar_norma(escrever(tmp_path, texto))
    mensagem = str(erro.value)
    assert "propriedade desconhecida" in mensagem
    assert "campo não reconhecido" in mensagem
