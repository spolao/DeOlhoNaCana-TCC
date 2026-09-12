"""Leitura do catálogo de categorias e serviços já semeado no banco."""

from __future__ import annotations

from deolhonacana.dados.conexao import conectar
from deolhonacana.dominio.modelos import Servico


def listar_categorias() -> list[str]:
    """Rótulos das categorias, na ordem de exibição."""
    with conectar() as conexao:
        linhas = conexao.execute(
            "SELECT rotulo FROM categorias ORDER BY ordem"
        ).fetchall()
    return [linha["rotulo"] for linha in linhas]


def listar_servicos(rotulo_categoria: str) -> list[Servico]:
    """Serviços de uma categoria, na ordem de exibição."""
    with conectar() as conexao:
        linhas = conexao.execute(
            """
            SELECT s.id, s.codigo, s.nome, s.rotulo, c.rotulo AS categoria
              FROM servicos AS s
              JOIN categorias AS c ON c.id = s.categoria_id
             WHERE c.rotulo = ?
             ORDER BY s.ordem
            """,
            (rotulo_categoria,),
        ).fetchall()
    return [
        Servico(
            id=linha["id"],
            categoria=linha["categoria"],
            codigo=linha["codigo"],
            nome=linha["nome"],
            rotulo=linha["rotulo"],
        )
        for linha in linhas
    ]


def id_do_servico(rotulo_servico: str) -> int | None:
    """Chave do serviço a partir do rótulo exibido na tela."""
    with conectar() as conexao:
        linha = conexao.execute(
            "SELECT id FROM servicos WHERE rotulo = ?", (rotulo_servico,)
        ).fetchone()
    return linha["id"] if linha else None


def listar_glebas() -> list[dict[str, str]]:
    """Glebas cadastradas, com fazenda, município e administrador."""
    with conectar() as conexao:
        linhas = conexao.execute(
            "SELECT codigo, fazenda, municipio, administrador FROM glebas ORDER BY codigo"
        ).fetchall()
    return [dict(linha) for linha in linhas]


def buscar_gleba(codigo: str) -> dict[str, str] | None:
    """Dados de uma gleba, para preencher fazenda e município automaticamente."""
    with conectar() as conexao:
        linha = conexao.execute(
            "SELECT codigo, fazenda, municipio, administrador FROM glebas WHERE codigo = ?",
            (codigo.strip(),),
        ).fetchone()
    return dict(linha) if linha else None
