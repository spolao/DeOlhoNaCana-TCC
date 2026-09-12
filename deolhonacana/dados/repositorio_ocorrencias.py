"""Gravação e consulta de ocorrências e seus anexos."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from deolhonacana.dados.conexao import conectar
from deolhonacana.dominio.modelos import Ocorrencia

#: Colunas oferecidas na ordenação da tela de consulta.
ORDENACOES = {
    "Mais recentes": "o.data_abertura DESC, o.id DESC",
    "Mais antigas": "o.data_abertura ASC, o.id ASC",
    "Dias pendentes": "dias_pendentes DESC",
    "Categoria": "categoria_codigo, servico_codigo",
    "Gleba": "o.gleba, o.quadra",
}


@dataclass
class Filtro:
    """Critérios da tela de consulta. Campos vazios não restringem nada."""

    categoria: str = ""
    servico: str = ""
    status: str = ""
    gleba: str = ""
    data_inicio: date | None = None
    data_fim: date | None = None
    ordenacao: str = "Mais recentes"

    def condicoes(self) -> tuple[list[str], list[object]]:
        """Monta a cláusula WHERE como pedaços e os respectivos parâmetros."""
        condicoes: list[str] = []
        parametros: list[object] = []
        if self.categoria:
            condicoes.append("categoria = ?")
            parametros.append(self.categoria)
        if self.servico:
            condicoes.append("servico = ?")
            parametros.append(self.servico)
        if self.status:
            condicoes.append("o.status = ?")
            parametros.append(self.status)
        if self.gleba:
            condicoes.append("o.gleba = ?")
            parametros.append(self.gleba.strip())
        if self.data_inicio:
            condicoes.append("o.data_abertura >= ?")
            parametros.append(self.data_inicio.isoformat())
        if self.data_fim:
            condicoes.append("o.data_abertura <= ?")
            parametros.append(self.data_fim.isoformat())
        return condicoes, parametros


def inserir(ocorrencia: Ocorrencia) -> int:
    """Grava uma ocorrência e seus anexos numa única transação.

    Devolve o id gerado. Os anexos já devem ter sido copiados para a pasta de
    dados por :mod:`deolhonacana.servicos.anexos`; aqui guarda-se só o nome.
    """
    with conectar() as conexao:
        cursor = conexao.execute(
            """
            INSERT INTO ocorrencias (
                data_abertura, data_conclusao, gleba, quadra, fazenda, municipio,
                administrador, servico_id, observacao, status, responsavel,
                registrado_por
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ocorrencia.data_abertura.isoformat(),
                ocorrencia.data_conclusao.isoformat()
                if ocorrencia.data_conclusao
                else None,
                ocorrencia.gleba.strip(),
                ocorrencia.quadra.strip(),
                ocorrencia.fazenda.strip(),
                ocorrencia.municipio.strip(),
                ocorrencia.administrador.strip(),
                ocorrencia.servico_id,
                ocorrencia.observacao.strip(),
                ocorrencia.status,
                ocorrencia.responsavel.strip(),
                ocorrencia.registrado_por,
            ),
        )
        novo_id = cursor.lastrowid
        if ocorrencia.anexos:
            conexao.executemany(
                "INSERT INTO anexos (ocorrencia_id, arquivo) VALUES (?, ?)",
                [(novo_id, arquivo) for arquivo in ocorrencia.anexos],
            )
    return novo_id


#: Colunas que a interface pode alterar. Serve de lista de permissão para que
#: nome de coluna nunca chegue ao SQL vindo direto da tela.
COLUNAS_EDITAVEIS = frozenset(
    {
        "data_abertura",
        "data_conclusao",
        "gleba",
        "quadra",
        "fazenda",
        "municipio",
        "administrador",
        "servico_id",
        "observacao",
        "status",
        "responsavel",
    }
)


def atualizar(ocorrencia_id: int, campos: dict[str, object]) -> bool:
    """Atualiza as colunas informadas de uma ocorrência."""
    desconhecidas = set(campos) - COLUNAS_EDITAVEIS
    if desconhecidas:
        nomes = ", ".join(sorted(desconhecidas))
        raise ValueError(f"Colunas inválidas: {nomes}")
    if not campos:
        return False

    atribuicoes = ", ".join(f"{coluna} = ?" for coluna in campos)
    valores = list(campos.values())
    valores.append(ocorrencia_id)
    sql = (
        f"UPDATE ocorrencias SET {atribuicoes}, "
        f"atualizado_em = datetime('now', 'localtime') WHERE id = ?"
    )
    with conectar() as conexao:
        cursor = conexao.execute(sql, valores)
    return cursor.rowcount > 0


def concluir(ocorrencia_id: int, responsavel: str, quando: date) -> bool:
    """Marca a ocorrência como finalizada na data informada."""
    return atualizar(
        ocorrencia_id,
        {
            "status": "Finalizado",
            "data_conclusao": quando.isoformat(),
            "responsavel": responsavel.strip(),
        },
    )


def reabrir(ocorrencia_id: int) -> bool:
    """Devolve a ocorrência para pendente, limpando a data de conclusão."""
    return atualizar(ocorrencia_id, {"status": "Pendente", "data_conclusao": None})


def excluir(ocorrencia_id: int) -> bool:
    """Remove a ocorrência; os anexos saem junto por ON DELETE CASCADE."""
    with conectar() as conexao:
        cursor = conexao.execute(
            "DELETE FROM ocorrencias WHERE id = ?", (ocorrencia_id,)
        )
    return cursor.rowcount > 0


def obter(ocorrencia_id: int) -> dict[str, object] | None:
    """Uma ocorrência, já com categoria, serviço e dias pendentes resolvidos."""
    with conectar() as conexao:
        linha = conexao.execute(
            "SELECT * FROM vw_ocorrencias AS o WHERE o.id = ?", (ocorrencia_id,)
        ).fetchone()
    return dict(linha) if linha else None


def listar(filtro: Filtro | None = None, limite: int | None = None) -> list[dict]:
    """Ocorrências que atendem ao filtro, já ordenadas."""
    filtro = filtro or Filtro()
    condicoes, parametros = filtro.condicoes()

    sql = "SELECT * FROM vw_ocorrencias AS o"
    if condicoes:
        sql += " WHERE " + " AND ".join(condicoes)
    sql += " ORDER BY " + ORDENACOES.get(filtro.ordenacao, ORDENACOES["Mais recentes"])
    if limite:
        sql += " LIMIT ?"
        parametros.append(limite)

    with conectar() as conexao:
        linhas = conexao.execute(sql, parametros).fetchall()
    return [dict(linha) for linha in linhas]


def listar_anexos(ocorrencia_id: int) -> list[str]:
    """Nomes dos arquivos anexados a uma ocorrência."""
    with conectar() as conexao:
        linhas = conexao.execute(
            "SELECT arquivo FROM anexos WHERE ocorrencia_id = ? ORDER BY id",
            (ocorrencia_id,),
        ).fetchall()
    return [linha["arquivo"] for linha in linhas]


def adicionar_anexo(ocorrencia_id: int, arquivo: str) -> None:
    """Vincula mais um arquivo a uma ocorrência já gravada."""
    with conectar() as conexao:
        conexao.execute(
            "INSERT INTO anexos (ocorrencia_id, arquivo) VALUES (?, ?)",
            (ocorrencia_id, arquivo),
        )


def contar_por_status() -> dict[str, int]:
    """Quantidade de ocorrências em cada status."""
    with conectar() as conexao:
        linhas = conexao.execute(
            "SELECT status, COUNT(*) AS total FROM ocorrencias GROUP BY status"
        ).fetchall()
    return {linha["status"]: linha["total"] for linha in linhas}


def glebas_utilizadas() -> list[str]:
    """Glebas que já aparecem em alguma ocorrência, para alimentar o filtro."""
    with conectar() as conexao:
        linhas = conexao.execute(
            """
            SELECT DISTINCT gleba FROM ocorrencias
             WHERE gleba IS NOT NULL AND gleba <> ''
             ORDER BY gleba
            """
        ).fetchall()
    return [linha["gleba"] for linha in linhas]
