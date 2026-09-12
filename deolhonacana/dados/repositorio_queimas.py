"""Gravação e consulta dos registros de combate a incêndio."""

from __future__ import annotations

from datetime import date, datetime

from deolhonacana.dados.conexao import conectar
from deolhonacana.dominio.modelos import Queima


def inserir(queima: Queima) -> int:
    """Grava um boletim de ocorrência de queima e devolve o id gerado."""
    with conectar() as conexao:
        cursor = conexao.execute(
            """
            INSERT INTO queimas (
                data, fazenda, gleba, quadra, viatura, hora_inicio, hora_fim,
                colaboradores, cana_ton, cana_ha, palha_ha, pasto_ha, mata_ha,
                app_ha, ja_colheu, observacao, registrado_por
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                queima.data.isoformat(),
                queima.fazenda.strip(),
                queima.gleba.strip(),
                queima.quadra.strip(),
                queima.viatura.strip(),
                queima.hora_inicio.strip(),
                queima.hora_fim.strip(),
                queima.colaboradores,
                queima.cana_ton,
                queima.cana_ha,
                queima.palha_ha,
                queima.pasto_ha,
                queima.mata_ha,
                queima.app_ha,
                queima.ja_colheu,
                queima.observacao.strip(),
                queima.registrado_por,
            ),
        )
        return cursor.lastrowid


def listar(
    data_inicio: date | None = None, data_fim: date | None = None
) -> list[dict]:
    """Registros de queima no período, do mais recente para o mais antigo."""
    condicoes: list[str] = []
    parametros: list[object] = []
    if data_inicio:
        condicoes.append("data >= ?")
        parametros.append(data_inicio.isoformat())
    if data_fim:
        condicoes.append("data <= ?")
        parametros.append(data_fim.isoformat())

    sql = "SELECT * FROM queimas"
    if condicoes:
        sql += " WHERE " + " AND ".join(condicoes)
    sql += " ORDER BY data DESC, id DESC"

    with conectar() as conexao:
        linhas = conexao.execute(sql, parametros).fetchall()

    registros = []
    for linha in linhas:
        registro = dict(linha)
        registro["area_total_ha"] = round(
            sum(
                registro[coluna] or 0
                for coluna in ("cana_ha", "palha_ha", "pasto_ha", "mata_ha", "app_ha")
            ),
            2,
        )
        registro["tempo_combate"] = calcular_tempo_combate(
            registro["hora_inicio"], registro["hora_fim"]
        )
        registros.append(registro)
    return registros


def calcular_tempo_combate(hora_inicio: str | None, hora_fim: str | None) -> str:
    """Duração entre duas horas no formato ``HH:MM``.

    O projeto antigo guardava esse valor numa coluna, o que permitia que ele
    divergisse das horas de início e fim. Aqui ele é sempre derivado. Combate
    que atravessa a meia-noite conta como no dia seguinte. Devolve string vazia
    quando alguma das horas estiver ausente ou malformada.
    """
    if not hora_inicio or not hora_fim:
        return ""
    try:
        inicio = datetime.strptime(hora_inicio.strip(), "%H:%M")
        fim = datetime.strptime(hora_fim.strip(), "%H:%M")
    except ValueError:
        return ""

    minutos = int((fim - inicio).total_seconds() // 60)
    if minutos < 0:
        minutos += 24 * 60
    return f"{minutos // 60:02d}:{minutos % 60:02d}"


def totais_por_periodo(
    data_inicio: date | None = None, data_fim: date | None = None
) -> dict[str, float]:
    """Somatórios de área e cana atingidas, para o painel de indicadores."""
    registros = listar(data_inicio, data_fim)
    return {
        "ocorrencias": len(registros),
        "cana_ton": round(sum(r["cana_ton"] or 0 for r in registros), 2),
        "area_total_ha": round(sum(r["area_total_ha"] for r in registros), 2),
        "colaboradores": sum(r["colaboradores"] or 0 for r in registros),
    }
