"""Acesso ao banco SQLite local.

Uma única função abre conexões, sempre com chaves estrangeiras ligadas e
linhas acessíveis por nome de coluna. Não há servidor nem pool: o banco é um
arquivo no disco da própria máquina.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from deolhonacana import config

#: Sobrescrito pelos testes para apontar a um banco temporário ou em memória.
_caminho_forcado: Path | str | None = None


def definir_caminho(caminho: Path | str | None) -> None:
    """Força o caminho do banco. Passar ``None`` volta ao comportamento normal."""
    global _caminho_forcado
    _caminho_forcado = caminho


def caminho_atual() -> Path | str:
    """Caminho do arquivo de banco em uso."""
    return _caminho_forcado if _caminho_forcado is not None else config.caminho_banco()


def abrir() -> sqlite3.Connection:
    """Abre uma conexão configurada.

    Quem chama é responsável por fechar; prefira o gerenciador de contexto
    :func:`conectar`.
    """
    conexao = sqlite3.connect(caminho_atual())
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


@contextmanager
def conectar() -> Iterator[sqlite3.Connection]:
    """Conexão com commit ao final e rollback em caso de erro.

    >>> with conectar() as con:
    ...     con.execute("INSERT INTO glebas (codigo, fazenda) VALUES (?, ?)", ("001", "X"))
    """
    conexao = abrir()
    try:
        yield conexao
    except Exception:
        conexao.rollback()
        raise
    else:
        conexao.commit()
    finally:
        conexao.close()
