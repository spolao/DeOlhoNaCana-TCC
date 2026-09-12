"""Gravação e consulta das leituras meteorológicas.

As leituras são digitadas pelo operador a partir da fonte que ele consultou
(estação da fazenda, termômetro, boletim). O sistema não busca nada na
internet — ele é offline por requisito.
"""

from __future__ import annotations

import sqlite3
from datetime import date

from deolhonacana.dados.conexao import conectar
from deolhonacana.dominio.modelos import RegistroClima


def inserir(registro: RegistroClima) -> int:
    """Grava uma leitura e devolve o id gerado.

    Levanta :class:`ValueError` se já existir leitura da mesma fonte na mesma
    data e hora, o que a restrição UNIQUE do esquema impede.
    """
    try:
        with conectar() as conexao:
            cursor = conexao.execute(
                """
                INSERT INTO clima (
                    data, hora, fonte, temperatura, sensacao_termica,
                    umidade_relativa, vento, registrado_por
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    registro.data.isoformat(),
                    registro.hora.strip(),
                    registro.fonte.strip(),
                    registro.temperatura,
                    registro.sensacao_termica,
                    registro.umidade_relativa,
                    registro.vento,
                    registro.registrado_por,
                ),
            )
            return cursor.lastrowid
    except sqlite3.IntegrityError as erro:
        raise ValueError(
            "Já existe uma leitura dessa fonte para a mesma data e hora."
        ) from erro


def listar(
    data_inicio: date | None = None, data_fim: date | None = None
) -> list[dict]:
    """Leituras do período, da mais recente para a mais antiga."""
    condicoes: list[str] = []
    parametros: list[object] = []
    if data_inicio:
        condicoes.append("data >= ?")
        parametros.append(data_inicio.isoformat())
    if data_fim:
        condicoes.append("data <= ?")
        parametros.append(data_fim.isoformat())

    sql = "SELECT * FROM clima"
    if condicoes:
        sql += " WHERE " + " AND ".join(condicoes)
    sql += " ORDER BY data DESC, hora DESC"

    with conectar() as conexao:
        linhas = conexao.execute(sql, parametros).fetchall()
    return [dict(linha) for linha in linhas]


def ultima_leitura() -> dict | None:
    """Leitura mais recente, exibida como resumo na tela de clima."""
    with conectar() as conexao:
        linha = conexao.execute(
            "SELECT * FROM clima ORDER BY data DESC, hora DESC LIMIT 1"
        ).fetchone()
    return dict(linha) if linha else None


def excluir(registro_id: int) -> bool:
    """Remove uma leitura digitada por engano."""
    with conectar() as conexao:
        cursor = conexao.execute("DELETE FROM clima WHERE id = ?", (registro_id,))
    return cursor.rowcount > 0
