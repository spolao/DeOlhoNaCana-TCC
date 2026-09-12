"""Testes das ocorrências: gravação, filtros, conclusão e dias pendentes."""

from __future__ import annotations

import sqlite3
from datetime import date, timedelta

import pytest

from deolhonacana.dados import repositorio_ocorrencias as repo
from deolhonacana.dados.repositorio_ocorrencias import Filtro
from deolhonacana.dominio.modelos import Ocorrencia
from deolhonacana.servicos import registros


def criar(servico_id, dias_atras=0, **extras) -> int:
    """Insere uma ocorrência aberta há N dias."""
    dados = {
        "data_abertura": date.today() - timedelta(days=dias_atras),
        "servico_id": servico_id,
        "gleba": "001",
        "quadra": "Q01",
    }
    dados.update(extras)
    return repo.inserir(Ocorrencia(**dados))


# ------------------------------------------------------------- gravação --


def test_ocorrencia_gravada_pode_ser_lida(banco, servico_id):
    numero = criar(servico_id, observacao="Buraco na saída")
    registro = repo.obter(numero)
    assert registro["observacao"] == "Buraco na saída"
    assert registro["status"] == "Pendente"
    assert registro["categoria"] == "4-ESTRADA"


def test_anexos_acompanham_a_ocorrencia(banco, servico_id):
    numero = repo.inserir(
        Ocorrencia(
            data_abertura=date.today(),
            servico_id=servico_id,
            anexos=["a.jpg", "b.jpg"],
        )
    )
    assert repo.listar_anexos(numero) == ["a.jpg", "b.jpg"]
    assert repo.obter(numero)["qtd_anexos"] == 2


def test_excluir_ocorrencia_leva_os_anexos_junto(banco, servico_id):
    numero = repo.inserir(
        Ocorrencia(data_abertura=date.today(), servico_id=servico_id, anexos=["a.jpg"])
    )
    repo.excluir(numero)
    assert repo.obter(numero) is None
    assert repo.listar_anexos(numero) == []


# -------------------------------------------------------- dias pendentes --


def test_dias_pendentes_conta_ate_hoje(banco, servico_id):
    """O cálculo antigo subtraía strings e devolvia valor sem sentido."""
    numero = criar(servico_id, dias_atras=10)
    assert repo.obter(numero)["dias_pendentes"] == 10


def test_dias_pendentes_congela_na_conclusao(banco, servico_id):
    numero = criar(servico_id, dias_atras=30)
    repo.concluir(numero, "Equipe A", date.today() - timedelta(days=25))
    assert repo.obter(numero)["dias_pendentes"] == 5


def test_ocorrencia_aberta_hoje_tem_zero_dias(banco, servico_id):
    assert repo.obter(criar(servico_id))["dias_pendentes"] == 0


# ------------------------------------------------------------- conclusão --


def test_concluir_muda_status_e_grava_responsavel(banco, servico_id):
    numero = criar(servico_id, dias_atras=3)
    repo.concluir(numero, "Equipe de Estradas", date.today())
    registro = repo.obter(numero)
    assert registro["status"] == "Finalizado"
    assert registro["responsavel"] == "Equipe de Estradas"
    assert registro["data_conclusao"] == date.today().isoformat()


def test_reabrir_limpa_a_data_de_conclusao(banco, servico_id):
    numero = criar(servico_id, dias_atras=3)
    repo.concluir(numero, "Equipe A", date.today())
    repo.reabrir(numero)
    registro = repo.obter(numero)
    assert registro["status"] == "Pendente"
    assert registro["data_conclusao"] is None


def test_banco_recusa_finalizado_sem_data(banco, servico_id):
    """A restrição CHECK impede status e data ficarem incoerentes."""
    numero = criar(servico_id)
    with pytest.raises(sqlite3.IntegrityError):
        repo.atualizar(numero, {"status": "Finalizado"})


def test_banco_recusa_conclusao_antes_da_abertura(banco, servico_id):
    numero = criar(servico_id, dias_atras=5)
    ontem = (date.today() - timedelta(days=10)).isoformat()
    with pytest.raises(sqlite3.IntegrityError):
        repo.atualizar(numero, {"status": "Finalizado", "data_conclusao": ontem})


def test_atualizar_rejeita_coluna_desconhecida(banco, servico_id):
    """Nome de coluna nunca chega ao SQL vindo da interface."""
    numero = criar(servico_id)
    with pytest.raises(ValueError, match="inválidas"):
        repo.atualizar(numero, {"status; DROP TABLE ocorrencias": "x"})


# --------------------------------------------------------------- filtros --


def test_filtro_por_status(banco, servico_id):
    criar(servico_id)
    concluida = criar(servico_id, dias_atras=2)
    repo.concluir(concluida, "Equipe A", date.today())

    pendentes = repo.listar(Filtro(status="Pendente"))
    assert len(pendentes) == 1
    assert all(r["status"] == "Pendente" for r in pendentes)


def test_filtro_por_categoria(banco, servico_id):
    from deolhonacana.dados import repositorio_catalogo

    outro = repositorio_catalogo.listar_servicos("8-CERCA")[0].id
    criar(servico_id)
    criar(outro)

    resultado = repo.listar(Filtro(categoria="8-CERCA"))
    assert len(resultado) == 1
    assert resultado[0]["categoria"] == "8-CERCA"


def test_filtro_por_periodo(banco, servico_id):
    criar(servico_id, dias_atras=1)
    criar(servico_id, dias_atras=60)

    recentes = repo.listar(Filtro(data_inicio=date.today() - timedelta(days=7)))
    assert len(recentes) == 1


def test_filtro_vazio_devolve_tudo(banco, servico_id):
    criar(servico_id)
    criar(servico_id, dias_atras=5)
    assert len(repo.listar(Filtro())) == 2


def test_ordenacao_por_dias_pendentes(banco, servico_id):
    criar(servico_id, dias_atras=2)
    criar(servico_id, dias_atras=40)
    resultado = repo.listar(Filtro(ordenacao="Dias pendentes"))
    assert resultado[0]["dias_pendentes"] == 40


# ------------------------------------------------- regras da camada de serviço --


def test_servico_grava_a_partir_do_formulario(banco):
    numero = registros.salvar_ocorrencia(
        data_texto="01/09/2026",
        categoria="4-ESTRADA",
        servico="4.1 - Buracos",
        gleba="001",
        quadra="Q07",
        observacao="Teste",
    )
    registro = repo.obter(numero)
    assert registro["quadra"] == "Q07"
    # Fazenda e município vêm da gleba cadastrada, não são digitados.
    assert registro["fazenda"] == "Fazenda Santa Rita"
    assert registro["municipio"] == "Pradópolis - SP"


@pytest.mark.parametrize(
    ("campos", "trecho_do_erro"),
    [
        ({"data_texto": ""}, "data"),
        ({"data_texto": "31/12/2099"}, "futuro"),
        ({"categoria": registros.PLACEHOLDER_CATEGORIA}, "categoria"),
        ({"servico": registros.PLACEHOLDER_SERVICO}, "serviço"),
        ({"gleba": ""}, "gleba"),
        ({"quadra": ""}, "quadra"),
    ],
)
def test_formulario_incompleto_e_recusado(banco, campos, trecho_do_erro):
    argumentos = {
        "data_texto": "01/09/2026",
        "categoria": "4-ESTRADA",
        "servico": "4.1 - Buracos",
        "gleba": "001",
        "quadra": "Q07",
    }
    argumentos.update(campos)
    with pytest.raises(registros.ErroValidacao, match=trecho_do_erro):
        registros.salvar_ocorrencia(**argumentos)
    assert repo.listar() == []


def test_concluir_duas_vezes_e_recusado(banco, servico_id):
    numero = criar(servico_id, dias_atras=2)
    registros.concluir_ocorrencia(numero, "Equipe A")
    with pytest.raises(registros.ErroValidacao, match="já está finalizada"):
        registros.concluir_ocorrencia(numero, "Equipe B")


def test_conclusao_anterior_a_abertura_e_recusada(banco, servico_id):
    numero = criar(servico_id, dias_atras=2)
    anteontem = (date.today() - timedelta(days=20)).strftime("%d/%m/%Y")
    with pytest.raises(registros.ErroValidacao, match="anterior"):
        registros.concluir_ocorrencia(numero, "Equipe A", anteontem)


def test_concluir_ocorrencia_inexistente_e_recusado(banco):
    with pytest.raises(registros.ErroValidacao, match="Não existe"):
        registros.concluir_ocorrencia(9999, "Equipe A")
