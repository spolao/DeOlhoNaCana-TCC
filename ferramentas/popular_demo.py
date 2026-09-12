"""Povoa o banco com dados sintéticos para demonstração e para a banca.

Nenhum dado real de empresa alguma: as fazendas são fictícias, os nomes de
responsável são genéricos e os números são sorteados dentro de faixas
plausíveis. Serve para a tela de indicadores e o relatório em PDF terem o que
mostrar sem precisar digitar cem apontamentos à mão.

    python ferramentas/popular_demo.py            # 120 ocorrências
    python ferramentas/popular_demo.py 300        # quantidade à escolha
    python ferramentas/popular_demo.py --limpar   # apaga o que foi gerado antes
"""

from __future__ import annotations

import random
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from deolhonacana.dados import (  # noqa: E402
    migracoes,
    repositorio_catalogo,
    repositorio_clima,
    repositorio_ocorrencias,
    repositorio_queimas,
)
from deolhonacana.dados.conexao import conectar  # noqa: E402
from deolhonacana.dominio.modelos import Ocorrencia, Queima, RegistroClima  # noqa: E402

QUANTIDADE_PADRAO = 120
DIAS_DE_HISTORICO = 270

RESPONSAVEIS = [
    "Equipe de Conservação",
    "Equipe de Estradas",
    "Equipe Agrícola A",
    "Equipe Agrícola B",
    "Manutenção Mecânica",
    "Meio Ambiente",
]

VIATURAS = ["ABT-01", "ABT-02", "CT-07", "CT-11", "Pipa 03"]

FONTES_CLIMA = [
    "Estação da fazenda",
    "Termômetro do escritório",
    "Boletim meteorológico",
]

OBSERVACOES = [
    "Identificado durante ronda de rotina.",
    "Apontado pelo operador da colhedora.",
    "Reincidência do mesmo ponto do mês passado.",
    "Necessita máquina pesada para correção.",
    "Agravado pelas chuvas da última semana.",
    "Sinalização provisória instalada no local.",
    "Sem risco imediato à operação.",
    "Bloqueia o acesso de caminhões carregados.",
]


def _data_aleatoria(sorteio: random.Random) -> date:
    return date.today() - timedelta(days=sorteio.randint(0, DIAS_DE_HISTORICO))


def gerar_ocorrencias(quantidade: int, sorteio: random.Random) -> int:
    """Cria ocorrências variadas, parte delas já concluída."""
    categorias = repositorio_catalogo.listar_categorias()
    glebas = repositorio_catalogo.listar_glebas()
    if not categorias or not glebas:
        raise RuntimeError("Catálogo vazio: rode o aplicativo uma vez antes.")

    criadas = 0
    for _ in range(quantidade):
        categoria = sorteio.choice(categorias)
        servicos = repositorio_catalogo.listar_servicos(categoria)
        if not servicos:
            continue
        servico = sorteio.choice(servicos)
        gleba = sorteio.choice(glebas)
        abertura = _data_aleatoria(sorteio)

        # Ocorrência antiga tem mais chance de já ter sido resolvida.
        idade = (date.today() - abertura).days
        concluida = sorteio.random() < min(0.85, 0.25 + idade / 400)
        conclusao = None
        if concluida:
            conclusao = min(
                abertura + timedelta(days=sorteio.randint(1, 45)), date.today()
            )

        repositorio_ocorrencias.inserir(
            Ocorrencia(
                data_abertura=abertura,
                data_conclusao=conclusao,
                status="Finalizado" if conclusao else "Pendente",
                servico_id=servico.id,
                gleba=gleba["codigo"],
                quadra=f"Q{sorteio.randint(1, 24):02d}",
                fazenda=gleba["fazenda"],
                municipio=gleba["municipio"],
                administrador=gleba["administrador"],
                observacao=sorteio.choice(OBSERVACOES),
                responsavel=sorteio.choice(RESPONSAVEIS) if conclusao else "",
            )
        )
        criadas += 1
    return criadas


def gerar_queimas(quantidade: int, sorteio: random.Random) -> int:
    """Cria boletins de combate a incêndio."""
    glebas = repositorio_catalogo.listar_glebas()
    for _ in range(quantidade):
        gleba = sorteio.choice(glebas)
        inicio = sorteio.randint(9, 20) * 60 + sorteio.randrange(0, 60, 5)
        duracao = sorteio.randint(40, 300)
        fim = (inicio + duracao) % (24 * 60)

        repositorio_queimas.inserir(
            Queima(
                data=_data_aleatoria(sorteio),
                fazenda=gleba["fazenda"],
                gleba=gleba["codigo"],
                quadra=f"Q{sorteio.randint(1, 24):02d}",
                viatura=sorteio.choice(VIATURAS),
                hora_inicio=f"{inicio // 60:02d}:{inicio % 60:02d}",
                hora_fim=f"{fim // 60:02d}:{fim % 60:02d}",
                colaboradores=sorteio.randint(2, 14),
                cana_ton=round(sorteio.uniform(0, 900), 2),
                cana_ha=round(sorteio.uniform(0, 18), 2),
                palha_ha=round(sorteio.uniform(0, 9), 2),
                pasto_ha=round(sorteio.uniform(0, 5), 2),
                mata_ha=round(sorteio.uniform(0, 3), 2),
                app_ha=round(sorteio.uniform(0, 2), 2),
                ja_colheu=sorteio.choice(["Sim", "Não"]),
                observacao="Combate concluído sem vítimas.",
            )
        )
    return quantidade


def gerar_clima(quantidade: int, sorteio: random.Random) -> int:
    """Cria leituras meteorológicas, uma por dia recente."""
    criadas = 0
    for indice in range(quantidade):
        dia = date.today() - timedelta(days=indice)
        temperatura = round(sorteio.uniform(16, 37), 1)
        try:
            repositorio_clima.inserir(
                RegistroClima(
                    data=dia,
                    hora=f"{sorteio.randint(7, 17):02d}:00",
                    fonte=sorteio.choice(FONTES_CLIMA),
                    temperatura=temperatura,
                    sensacao_termica=round(temperatura + sorteio.uniform(-2, 4), 1),
                    umidade_relativa=round(sorteio.uniform(22, 92), 0),
                    vento=round(sorteio.uniform(2, 28), 1),
                )
            )
            criadas += 1
        except ValueError:
            # Já havia leitura dessa fonte nesse dia e hora; segue adiante.
            continue
    return criadas


def limpar() -> None:
    """Apaga ocorrências, queimas e clima, preservando catálogo e usuários."""
    with conectar() as conexao:
        for tabela in ("anexos", "ocorrencias", "queimas", "clima"):
            conexao.execute(f"DELETE FROM {tabela}")
    print("Registros de demonstração removidos.")


def main(argumentos: list[str]) -> None:
    migracoes.inicializar()

    if "--limpar" in argumentos:
        limpar()
        return

    quantidade = QUANTIDADE_PADRAO
    for argumento in argumentos:
        if argumento.isdigit():
            quantidade = int(argumento)

    # Semente fixa: rodar duas vezes gera o mesmo conjunto, o que ajuda a
    # reproduzir prints e resultados na monografia.
    sorteio = random.Random(2026)

    ocorrencias = gerar_ocorrencias(quantidade, sorteio)
    queimas = gerar_queimas(max(6, quantidade // 10), sorteio)
    leituras = gerar_clima(30, sorteio)

    print(f"{ocorrencias} ocorrências, {queimas} queimas e {leituras} leituras criadas.")
    print("Situação atual:", repositorio_ocorrencias.contar_por_status())


if __name__ == "__main__":
    main(sys.argv[1:])
