"""Testes do relatório em PDF e do painel de indicadores."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from deolhonacana.dados import repositorio_ocorrencias as repo
from deolhonacana.dominio.modelos import Ocorrencia
from deolhonacana.servicos import indicadores, relatorio_pdf


@pytest.fixture
def com_ocorrencias(banco, servico_id):
    """Meia dúzia de ocorrências, metade concluída."""
    for indice in range(6):
        numero = repo.inserir(
            Ocorrencia(
                data_abertura=date.today() - timedelta(days=indice * 10),
                servico_id=servico_id,
                gleba="001",
                quadra=f"Q{indice:02d}",
                fazenda="Fazenda Santa Rita",
                observacao=f"Apontamento {indice}",
            )
        )
        if indice % 2 == 0:
            repo.concluir(numero, "Equipe A", date.today())
    return repo.listar()


# ----------------------------------------------------------------- PDF --


def test_pdf_e_gerado_com_conteudo(com_ocorrencias):
    arquivo = relatorio_pdf.gerar(com_ocorrencias, "todas as ocorrências")
    assert arquivo.is_file()
    assert arquivo.suffix == ".pdf"
    assert arquivo.stat().st_size > 2000
    assert arquivo.read_bytes().startswith(b"%PDF")


def test_pdf_sem_registros_e_recusado(banco):
    with pytest.raises(ValueError, match="Não há ocorrências"):
        relatorio_pdf.gerar([], "filtro vazio")


def test_cada_pdf_recebe_nome_proprio(com_ocorrencias):
    """O carimbo de data e hora evita sobrescrever o relatório anterior."""
    primeiro = relatorio_pdf.gerar(com_ocorrencias[:3], "recorte A")
    assert primeiro.is_file()
    assert primeiro.name.startswith("ocorrencias-")


def test_anexo_ausente_nao_derruba_o_relatorio(banco, servico_id):
    """Registro aponta para uma foto que sumiu do disco: o PDF sai mesmo assim."""
    repo.inserir(
        Ocorrencia(
            data_abertura=date.today(),
            servico_id=servico_id,
            gleba="001",
            anexos=["arquivo-que-nao-existe.png"],
        )
    )
    arquivo = relatorio_pdf.gerar(repo.listar(), "com anexo perdido")
    assert arquivo.is_file()


# --------------------------------------------------------- indicadores --


def test_resumo_conta_certo(com_ocorrencias):
    numeros = indicadores.resumo()
    assert numeros["total"] == 6
    assert numeros["pendentes"] == 3
    assert numeros["finalizadas"] == 3
    assert numeros["media_dias_pendentes"] > 0


def test_painel_e_gerado(com_ocorrencias):
    arquivo = indicadores.gerar_painel()
    assert arquivo.is_file()
    assert arquivo.read_bytes().startswith(b"\x89PNG")


def test_painel_funciona_com_banco_vazio(banco):
    """Sem nenhum registro os gráficos mostram o aviso, mas não quebram."""
    numeros = indicadores.resumo()
    assert numeros["total"] == 0
    assert indicadores.gerar_painel().is_file()
