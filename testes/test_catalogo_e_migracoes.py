"""Testes do catálogo de serviços e da criação do banco."""

from __future__ import annotations

import pytest

from deolhonacana.dados import migracoes, repositorio_catalogo
from deolhonacana.dados.conexao import conectar
from deolhonacana.dominio import catalogo


def test_catalogo_tem_o_conteudo_esperado():
    """27 categorias — a numeração original pula o 21."""
    assert len(catalogo.categorias()) == 27
    assert catalogo.total_servicos() == 134


def test_toda_categoria_tem_ao_menos_um_servico():
    for categoria in catalogo.categorias():
        assert catalogo.servicos_de(categoria), f"{categoria} está sem serviços"


@pytest.mark.parametrize(
    ("rotulo", "esperado"),
    [
        ("4-ESTRADA", ("4", "ESTRADA")),
        ("16-MEIO AMBIENTE (ANIMAIS SILVESTRES)", ("16", "MEIO AMBIENTE (ANIMAIS SILVESTRES)")),
        ("4.1 - Buracos", ("4.1", "Buracos")),
        ("19.10 - Grama-Seda", ("19.10", "Grama-Seda")),
        ("sem numero", ("", "sem numero")),
    ],
)
def test_separacao_de_codigo_e_nome(rotulo, esperado):
    assert catalogo.separar_codigo(rotulo) == esperado


def test_categoria_desconhecida_devolve_lista_vazia():
    assert catalogo.servicos_de("99-INEXISTENTE") == []


# ------------------------------------------------------------ migrações --


def test_banco_nasce_com_o_catalogo_semeado(banco):
    assert len(repositorio_catalogo.listar_categorias()) == 27
    with conectar() as conexao:
        total = conexao.execute("SELECT COUNT(*) AS n FROM servicos").fetchone()["n"]
    assert total == catalogo.total_servicos()


def test_inicializar_duas_vezes_nao_duplica(banco):
    migracoes.inicializar()
    migracoes.inicializar()
    with conectar() as conexao:
        categorias = conexao.execute("SELECT COUNT(*) AS n FROM categorias").fetchone()["n"]
        servicos = conexao.execute("SELECT COUNT(*) AS n FROM servicos").fetchone()["n"]
        usuarios = conexao.execute("SELECT COUNT(*) AS n FROM usuarios").fetchone()["n"]
    assert categorias == 27
    assert servicos == catalogo.total_servicos()
    assert usuarios == 1


def test_glebas_de_exemplo_ficam_disponiveis(banco):
    glebas = repositorio_catalogo.listar_glebas()
    assert len(glebas) == len(migracoes.GLEBAS_EXEMPLO)
    assert repositorio_catalogo.buscar_gleba("001")["fazenda"] == "Fazenda Santa Rita"
    assert repositorio_catalogo.buscar_gleba("999") is None


def test_servico_pode_ser_resolvido_pelo_rotulo(banco):
    identificador = repositorio_catalogo.id_do_servico("4.1 - Buracos")
    assert identificador is not None
    assert repositorio_catalogo.id_do_servico("nao existe") is None


def test_chaves_estrangeiras_estao_ligadas(banco):
    with conectar() as conexao:
        ligadas = conexao.execute("PRAGMA foreign_keys").fetchone()[0]
    assert ligadas == 1
