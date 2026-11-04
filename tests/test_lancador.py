"""Lançador: cópia do programa para o PC, uma vez por versão (igual ao da calibração)."""

from classificador.lancador import (
    NOME_EXE,
    PRONTO,
    copia_pronta,
    copiar_para_o_pc,
    limpar_versoes_antigas,
    versao_da_rede,
)


def programa_na_rede(tmp_path, versao="0.7.0_20261104-150000"):
    programa = tmp_path / "rede" / "programa"
    (programa / "_internal").mkdir(parents=True)
    (programa / NOME_EXE).write_bytes(b"exe")
    (programa / "_internal" / "python.dll").write_bytes(b"dll")
    (programa / "versao.txt").write_text(versao + "\n", encoding="utf-8")
    return programa


def test_copia_uma_vez_por_versao(tmp_path):
    programa = programa_na_rede(tmp_path)
    cache = tmp_path / "cache"
    versao = versao_da_rede(programa)
    assert versao == "0.7.0_20261104-150000"
    assert not copia_pronta(cache, versao)
    destino = copiar_para_o_pc(programa, cache, versao)
    assert (destino / "_internal" / "python.dll").read_bytes() == b"dll"
    assert copia_pronta(cache, versao)
    (destino / NOME_EXE).write_bytes(b"usada")
    assert copiar_para_o_pc(programa, cache, versao) == destino  # já copiada: não copia de novo
    assert (destino / NOME_EXE).read_bytes() == b"usada"


def test_copia_interrompida_e_refeita(tmp_path):
    programa = programa_na_rede(tmp_path)
    cache = tmp_path / "cache"
    pela_metade = cache / "0.7.0_20261104-150000"
    pela_metade.mkdir(parents=True)  # sem o arquivo de "cópia completa"
    destino = copiar_para_o_pc(programa, cache, "0.7.0_20261104-150000")
    assert (destino / PRONTO).is_file()
    assert (destino / "_internal" / "python.dll").is_file()


def test_versao_nova_substitui_a_antiga(tmp_path):
    cache = tmp_path / "cache"
    copiar_para_o_pc(programa_na_rede(tmp_path), cache, "0.7.0_a")
    copiar_para_o_pc(programa_na_rede(tmp_path / "nova", "0.7.1_b"), cache, "0.7.1_b")
    limpar_versoes_antigas(cache, "0.7.1_b")
    assert [p.name for p in cache.iterdir()] == ["0.7.1_b"]


def test_copia_que_falha_nao_deixa_sobra_no_pc(tmp_path, monkeypatch):
    import shutil

    import pytest

    programa = programa_na_rede(tmp_path)
    cache = tmp_path / "cache"

    def rede_caiu(origem, destino):
        (destino / "_internal").mkdir(parents=True)  # copiou um pedaço e parou
        raise OSError("a rede caiu")

    monkeypatch.setattr(shutil, "copytree", rede_caiu)
    with pytest.raises(OSError):
        copiar_para_o_pc(programa, cache, "0.7.0_x")
    assert list(cache.iterdir()) == []  # nada de "…copiando-…" esquecido
