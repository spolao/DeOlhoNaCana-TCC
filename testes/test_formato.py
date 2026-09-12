"""Testes das conversões entre o texto da tela e os tipos do banco."""

from __future__ import annotations

from datetime import date

import pytest

from deolhonacana.servicos import formato


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("11/09/2026", date(2026, 9, 11)),
        ("2026-09-11", date(2026, 9, 11)),  # formato que o seletor do KivyMD devolve
        ("  01/01/2020  ", date(2020, 1, 1)),
        ("", None),
        (None, None),
        ("31/02/2026", None),  # dia inexistente
        ("amanhã", None),
    ],
)
def test_leitura_de_datas(entrada, esperado):
    assert formato.texto_para_data(entrada) == esperado


def test_data_para_texto_usa_padrao_brasileiro():
    assert formato.data_para_texto(date(2026, 9, 11)) == "11/09/2026"
    assert formato.data_para_texto("2026-09-11") == "11/09/2026"
    assert formato.data_para_texto(None) == ""


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("12.5", 12.5),   # teclado numérico do formulário
        ("12,5", 12.5),   # digitação no padrão brasileiro
        ("1.234,56", 1234.56),  # ponto como separador de milhar
        ("1234.56", 1234.56),
        ("0", 0.0),
        ("", 0.0),
        (None, 0.0),
        ("abc", 0.0),
    ],
)
def test_leitura_de_numeros(entrada, esperado):
    """Regressão: ``12.5`` já foi lido como 125 por descartar o ponto."""
    assert formato.para_numero(entrada) == pytest.approx(esperado)


def test_numero_para_texto_usa_virgula_decimal():
    assert formato.numero_para_texto(15.5) == "15,50"
    assert formato.numero_para_texto(1234.5) == "1.234,50"
    assert formato.numero_para_texto(None) == ""


@pytest.mark.parametrize(
    ("entrada", "valida"),
    [("14:20", True), ("00:00", True), ("23:59", True),
     ("24:00", False), ("14h20", False), ("", False), (None, False)],
)
def test_validacao_de_hora(entrada, valida):
    assert formato.hora_valida(entrada) is valida


def test_encurtar_respeita_o_limite():
    texto = "Bloqueia o acesso de caminhões carregados no carreador principal"
    curto = formato.encurtar(texto, 20)
    assert len(curto) <= 20
    assert curto.endswith("…")
    assert formato.encurtar("curto", 20) == "curto"
    assert formato.encurtar(None) == ""
