"""Repositório do histórico: o único lugar do programa que lê e grava no banco (ADR 0002).

A tela fala só com esta classe; se um dia o SQLite for trocado, só este pacote muda. Cada gravação
é uma transação curta (banco em pasta de rede, às vezes com 2–3 pessoas).
"""

import datetime
import functools
import json
import os
import platform
import sqlite3
import unicodedata
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

from classificador import __version__
from classificador.historico.backup import fazer_backup_diario
from classificador.historico.esquema import conectar

NOME_BANCO = "historico.db"
MENSAGEM_CONSULTA = "Modo consulta: outra pessoa está editando. Nada foi salvo."
MENSAGEM_OCUPADO = (
    "O banco de dados está ocupado por outro computador. Nada foi salvo: "
    "tente de novo em alguns segundos."
)


class ErroDeValidacao(Exception):
    """Gravação recusada; `mensagens` vão para a área de avisos da tela (em vermelho)."""

    def __init__(self, mensagens: list[str]):
        super().__init__("; ".join(mensagens))
        self.mensagens = mensagens


@dataclass(frozen=True)
class NovaClassificacao:
    """O que a tela manda salvar: o "retrato" da classificação como saiu na hora."""

    bobina: str
    acabamento: str
    valores: Mapping[str, str]  # campo da tela → texto digitado
    resultado: str | None
    norma: str | None
    correlatas: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)
    tolerancia: str | None = None
    tolerancia_dentro: bool | None = None


@dataclass(frozen=True)
class Registro(NovaClassificacao):
    id: int = 0
    criado_em: datetime.datetime | None = None
    usuario: str = ""
    computador: str = ""
    versao_programa: str = ""
    excluido_em: datetime.datetime | None = None
    excluido_por: str | None = None


@dataclass(frozen=True)
class Divergencia:
    id: int
    classificacao: Registro
    correta: str
    motivo: str
    criado_em: datetime.datetime
    usuario: str
    computador: str
    resolvida_em: datetime.datetime | None = None
    resolvida_por: str | None = None


def usuario_e_computador() -> tuple[str, str]:
    """Usuário do Windows e nome do PC (sem senha: só para saber quem fez)."""
    usuario = os.environ.get("USERNAME") or os.environ.get("USER") or "?"
    return usuario, os.environ.get("COMPUTERNAME") or platform.node() or "?"


def sem_acentos(texto: str) -> str:
    """Para a pesquisa: "Manganês" e "manganes" são iguais."""
    decomposto = unicodedata.normalize("NFKD", texto.casefold())
    return "".join(c for c in decomposto if not unicodedata.combining(c))


def _escrita(metodo):
    """Toda gravação: recusada no modo consulta; banco ocupado vira aviso na tela."""

    @functools.wraps(metodo)
    def envolto(self, *args, **kwargs):
        if self.modo_consulta:
            raise ErroDeValidacao([MENSAGEM_CONSULTA])
        try:
            return metodo(self, *args, **kwargs)
        except sqlite3.OperationalError as erro:
            if "locked" in str(erro) or "busy" in str(erro):
                raise ErroDeValidacao([MENSAGEM_OCUPADO]) from erro
            raise

    return envolto


class RepositorioHistorico:
    def __init__(
        self,
        conexao: sqlite3.Connection,
        agora: Callable[[], datetime.datetime] = datetime.datetime.now,
        quem: tuple[str, str] | None = None,
    ):
        self._conexao = conexao
        self._agora = agora
        self.usuario, self.computador = quem or usuario_e_computador()
        # Sem trava de edição (testes, fotos), pode gravar; a janela liga o modo consulta.
        self.modo_consulta = False

    @classmethod
    def abrir(cls, pasta: Path, **kwargs) -> "RepositorioHistorico":
        """Abre (ou cria) `historico.db` na pasta de dados e faz o backup do dia."""
        banco = pasta / NOME_BANCO
        repositorio = cls(conectar(banco), **kwargs)
        fazer_backup_diario(banco, repositorio._agora().date())
        return repositorio

    def fechar(self) -> None:
        self._conexao.close()

    def _carimbo(self) -> str:
        return self._agora().isoformat(timespec="seconds")

    # ------------------------------------------------------------------ classificações

    @_escrita
    def salvar(self, nova: NovaClassificacao) -> int:
        """Grava e devolve o número do registro. Bobina vazia → ErroDeValidacao."""
        bobina = nova.bobina.strip()
        erros = []
        if not bobina:
            erros.append("Informe o nº da bobina / lote para salvar")
        if not nova.resultado:
            erros.append("Não há resultado para salvar: classifique primeiro")
        if erros:
            raise ErroDeValidacao(erros)
        with self._conexao:
            cursor = self._conexao.execute(
                """INSERT INTO classificacao (criado_em, usuario, computador, versao_programa,
                       bobina, acabamento, valores, resultado, norma, correlatas, avisos,
                       tolerancia, tolerancia_dentro)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    self._carimbo(), self.usuario, self.computador, __version__,
                    bobina, nova.acabamento,
                    json.dumps(dict(nova.valores), ensure_ascii=False),
                    nova.resultado, nova.norma,
                    json.dumps(nova.correlatas, ensure_ascii=False),
                    json.dumps(nova.avisos, ensure_ascii=False),
                    nova.tolerancia,
                    None if nova.tolerancia_dentro is None else int(nova.tolerancia_dentro),
                ),
            )
        return cursor.lastrowid

    def obter(self, id_: int) -> Registro | None:
        linha = self._conexao.execute(
            "SELECT * FROM classificacao WHERE id = ?", (id_,)
        ).fetchone()
        return _registro(linha) if linha else None

    def listar(self, texto: str = "", lixeira: bool = False) -> list[Registro]:
        """Mais recentes primeiro. `texto`: cada palavra tem de aparecer em algum campo do
        registro (bobina, resultado, acabamento, norma, avisos, valores, usuário…), sem
        diferenciar maiúsculas nem acentos. `lixeira=True` lista só os excluídos."""
        condicao = "IS NOT NULL" if lixeira else "IS NULL"
        linhas = self._conexao.execute(
            f"SELECT * FROM classificacao WHERE excluido_em {condicao} "
            "ORDER BY criado_em DESC, id DESC"
        ).fetchall()
        palavras = sem_acentos(texto).split()
        registros = [_registro(linha) for linha in linhas]
        if not palavras:
            return registros
        return [r for r in registros if all(p in _texto_pesquisavel(r) for p in palavras)]

    @_escrita
    def excluir(self, id_: int) -> None:
        """Manda para a Lixeira (exclusão lógica)."""
        with self._conexao:
            self._conexao.execute(
                "UPDATE classificacao SET excluido_em = ?, excluido_por = ? "
                "WHERE id = ? AND excluido_em IS NULL",
                (self._carimbo(), self.usuario, id_),
            )

    @_escrita
    def restaurar(self, id_: int) -> None:
        """Tira da Lixeira e devolve ao Histórico."""
        with self._conexao:
            self._conexao.execute(
                "UPDATE classificacao SET excluido_em = NULL, excluido_por = NULL WHERE id = ?",
                (id_,),
            )

    @_escrita
    def excluir_permanentemente(self, id_: int) -> None:
        """Apaga de vez (com as divergências dele). Só vale para o que já está na Lixeira."""
        with self._conexao:
            apagados = self._conexao.execute(
                "DELETE FROM classificacao WHERE id = ? AND excluido_em IS NOT NULL", (id_,)
            ).rowcount
        if not apagados:
            raise ErroDeValidacao(["Só é possível excluir permanentemente o que está na Lixeira"])

    # ------------------------------------------------------------------ divergências

    @_escrita
    def registrar_divergencia(self, id_: int, correta: str, motivo: str) -> int:
        """ "A classificação correta era outra": correta e motivo são obrigatórios."""
        correta, motivo = correta.strip(), motivo.strip()
        erros = []
        if not correta:
            erros.append("Informe qual era a classificação correta")
        if not motivo:
            erros.append("Informe o motivo da divergência")
        registro = self.obter(id_)
        if registro is None or registro.excluido_em is not None:
            erros.append("Classificação não encontrada no Histórico")
        if erros:
            raise ErroDeValidacao(erros)
        with self._conexao:
            cursor = self._conexao.execute(
                """INSERT INTO divergencia (classificacao_id, correta, motivo, criado_em,
                       usuario, computador) VALUES (?, ?, ?, ?, ?, ?)""",
                (id_, correta, motivo, self._carimbo(), self.usuario, self.computador),
            )
        return cursor.lastrowid

    def listar_divergencias(self, resolvidas: bool = False) -> list[Divergencia]:
        """Pendentes (ou resolvidas), mais recentes primeiro. As de classificações que estão na
        Lixeira não aparecem (voltam se a classificação for restaurada)."""
        condicao = "IS NOT NULL" if resolvidas else "IS NULL"
        linhas = self._conexao.execute(
            f"""SELECT d.*, c.id AS c_id FROM divergencia d
                JOIN classificacao c ON c.id = d.classificacao_id
                WHERE d.resolvida_em {condicao} AND c.excluido_em IS NULL
                ORDER BY d.criado_em DESC, d.id DESC"""
        ).fetchall()
        return [
            Divergencia(
                id=linha["id"],
                classificacao=self.obter(linha["c_id"]),
                correta=linha["correta"],
                motivo=linha["motivo"],
                criado_em=datetime.datetime.fromisoformat(linha["criado_em"]),
                usuario=linha["usuario"],
                computador=linha["computador"],
                resolvida_em=_data(linha["resolvida_em"]),
                resolvida_por=linha["resolvida_por"],
            )
            for linha in linhas
        ]

    @_escrita
    def resolver_divergencia(self, id_: int) -> None:
        """Marca como resolvida (a correção já foi feita no YAML/regra + caso de teste)."""
        with self._conexao:
            self._conexao.execute(
                "UPDATE divergencia SET resolvida_em = ?, resolvida_por = ? "
                "WHERE id = ? AND resolvida_em IS NULL",
                (self._carimbo(), self.usuario, id_),
            )


def _data(texto: str | None) -> datetime.datetime | None:
    return datetime.datetime.fromisoformat(texto) if texto else None


def _registro(linha: sqlite3.Row) -> Registro:
    dentro = linha["tolerancia_dentro"]
    return Registro(
        id=linha["id"],
        criado_em=datetime.datetime.fromisoformat(linha["criado_em"]),
        usuario=linha["usuario"],
        computador=linha["computador"],
        versao_programa=linha["versao_programa"],
        bobina=linha["bobina"],
        acabamento=linha["acabamento"],
        valores=json.loads(linha["valores"]),
        resultado=linha["resultado"],
        norma=linha["norma"],
        correlatas=json.loads(linha["correlatas"]),
        avisos=json.loads(linha["avisos"]),
        tolerancia=linha["tolerancia"],
        tolerancia_dentro=None if dentro is None else bool(dentro),
        excluido_em=_data(linha["excluido_em"]),
        excluido_por=linha["excluido_por"],
    )


def _texto_pesquisavel(r: Registro) -> str:
    partes = [
        r.bobina, r.acabamento, r.resultado or "", r.norma or "", r.tolerancia or "",
        r.usuario, r.computador, r.criado_em.strftime("%d/%m/%Y") if r.criado_em else "",
        *r.correlatas, *r.avisos, *r.valores.values(),
    ]
    return sem_acentos(" ".join(partes))
