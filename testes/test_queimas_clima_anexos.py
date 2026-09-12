"""Testes de queimas, clima e anexos."""

from __future__ import annotations

from datetime import date

import pytest

from deolhonacana.dados import repositorio_clima, repositorio_queimas
from deolhonacana.servicos import anexos, registros


# ------------------------------------------------------------- queimas --


@pytest.mark.parametrize(
    ("inicio", "fim", "esperado"),
    [
        ("14:20", "17:05", "02:45"),
        ("08:00", "08:30", "00:30"),
        ("22:30", "01:15", "02:45"),  # combate que vira o dia
        ("10:00", "10:00", "00:00"),
        ("", "17:05", ""),
        ("14h20", "17:05", ""),
    ],
)
def test_tempo_de_combate(inicio, fim, esperado):
    """Derivado das horas, nunca armazenado — não há como divergir."""
    assert repositorio_queimas.calcular_tempo_combate(inicio, fim) == esperado


def test_queima_gravada_soma_a_area(banco):
    numero = registros.salvar_queima(
        data_texto="10/09/2026",
        fazenda="Fazenda Santa Rita",
        hora_inicio="14:20",
        hora_fim="17:05",
        cana_ha="12,5",
        palha_ha="3",
        mata_ha="1.25",
    )
    registro = next(r for r in repositorio_queimas.listar() if r["id"] == numero)
    assert registro["area_total_ha"] == pytest.approx(16.75)
    assert registro["tempo_combate"] == "02:45"


def test_queima_sem_fazenda_e_recusada(banco):
    with pytest.raises(registros.ErroValidacao, match="fazenda"):
        registros.salvar_queima(data_texto="10/09/2026", fazenda="", cana_ha="5")


def test_queima_sem_area_nem_cana_e_recusada(banco):
    with pytest.raises(registros.ErroValidacao, match="área atingida"):
        registros.salvar_queima(data_texto="10/09/2026", fazenda="Santa Rita")


def test_hora_malformada_e_recusada(banco):
    with pytest.raises(registros.ErroValidacao, match="HH:MM"):
        registros.salvar_queima(
            data_texto="10/09/2026",
            fazenda="Santa Rita",
            cana_ha="5",
            hora_inicio="14h",
        )


def test_totais_do_periodo(banco):
    for _ in range(3):
        registros.salvar_queima(
            data_texto="10/09/2026", fazenda="Santa Rita", cana_ha="10", cana_ton="100"
        )
    totais = repositorio_queimas.totais_por_periodo()
    assert totais["ocorrencias"] == 3
    assert totais["area_total_ha"] == pytest.approx(30.0)
    assert totais["cana_ton"] == pytest.approx(300.0)


# --------------------------------------------------------------- clima --


def test_leitura_gravada_vira_a_ultima(banco):
    registros.salvar_clima(
        data_texto="11/09/2026",
        hora="14:00",
        fonte="Estação da fazenda",
        temperatura="31,4",
        umidade="48",
        vento="12.5",
    )
    ultima = repositorio_clima.ultima_leitura()
    assert ultima["temperatura"] == pytest.approx(31.4)
    assert ultima["vento"] == pytest.approx(12.5)


@pytest.mark.parametrize("umidade", ["150", "-5"])
def test_umidade_fora_da_faixa_e_recusada(banco, umidade):
    with pytest.raises(registros.ErroValidacao, match="umidade"):
        registros.salvar_clima(data_texto="11/09/2026", hora="14:00", umidade=umidade)


def test_hora_invalida_no_clima(banco):
    with pytest.raises(registros.ErroValidacao, match="HH:MM"):
        registros.salvar_clima(data_texto="11/09/2026", hora="meio-dia")


def test_leitura_repetida_da_mesma_fonte_e_recusada(banco):
    argumentos = {
        "data_texto": "11/09/2026",
        "hora": "14:00",
        "fonte": "Estação da fazenda",
        "temperatura": "30",
    }
    registros.salvar_clima(**argumentos)
    with pytest.raises(registros.ErroValidacao, match="Já existe"):
        registros.salvar_clima(**argumentos)


# -------------------------------------------------------------- anexos --


def test_imagem_e_copiada_para_a_pasta_de_dados(banco, tmp_path):
    """O banco guarda o nome, não o caminho original que o usuário escolheu."""
    origem = tmp_path / "foto.png"
    origem.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 100)

    nome = anexos.guardar(origem)
    assert nome.endswith(".png")
    assert nome != "foto.png"  # renomeado para não colidir
    assert anexos.caminho_de(nome).is_file()

    # Apagar o original não afeta o anexo guardado.
    origem.unlink()
    assert anexos.caminho_para_exibir(nome) != ""


def test_dois_arquivos_de_mesmo_nome_nao_colidem(banco, tmp_path):
    primeiro = tmp_path / "a" / "foto.png"
    segundo = tmp_path / "b" / "foto.png"
    for caminho in (primeiro, segundo):
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 50)

    assert anexos.guardar(primeiro) != anexos.guardar(segundo)


def test_arquivo_que_nao_e_imagem_e_recusado(banco, tmp_path):
    documento = tmp_path / "planilha.xlsx"
    documento.write_bytes(b"0" * 20)
    with pytest.raises(anexos.ErroAnexo, match="Formato"):
        anexos.guardar(documento)


def test_arquivo_inexistente_e_recusado(banco, tmp_path):
    with pytest.raises(anexos.ErroAnexo, match="não encontrado"):
        anexos.guardar(tmp_path / "some.png")


def test_anexo_ausente_nao_quebra_a_exibicao(banco):
    assert anexos.caminho_para_exibir("nao-existe.png") == ""
    assert anexos.caminho_para_exibir(None) == ""
