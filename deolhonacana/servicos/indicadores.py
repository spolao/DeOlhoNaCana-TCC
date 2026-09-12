"""Painel de indicadores gerado localmente.

Substitui o botão que abria um relatório do Power BI num navegador
automatizado por Selenium — o que exigia internet, credencial corporativa e
uma versão específica do ChromeDriver. Aqui os mesmos números saem do próprio
banco e viram uma imagem, sem sair da máquina.

O backend ``Agg`` é obrigatório: o matplotlib não pode tentar abrir uma janela
própria enquanto o Kivy é dono do laço gráfico.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402  (precisa vir depois de use)

from collections import Counter, defaultdict  # noqa: E402
from datetime import date  # noqa: E402
from pathlib import Path  # noqa: E402

from deolhonacana import config  # noqa: E402
from deolhonacana.dados import repositorio_ocorrencias, repositorio_queimas  # noqa: E402

#: Nome do arquivo gerado dentro da pasta de dados.
ARQUIVO_PAINEL = "indicadores.png"

#: Paleta em tons que funcionam sobre o tema escuro da interface.
COR_PENDENTE = "#e8833a"
COR_FINALIZADO = "#4c9f70"
COR_BARRA = "#5b8def"
COR_LINHA = "#e8833a"
COR_TEXTO = "#e6e6e6"
COR_FUNDO = "#1e1e1e"
COR_GRADE = "#3a3a3a"


def _estilizar(eixo, titulo: str) -> None:
    """Aplica o mesmo visual escuro a todos os gráficos."""
    eixo.set_title(titulo, color=COR_TEXTO, fontsize=11, pad=10)
    eixo.set_facecolor(COR_FUNDO)
    eixo.tick_params(colors=COR_TEXTO, labelsize=8)
    for borda in eixo.spines.values():
        borda.set_color(COR_GRADE)
    eixo.grid(True, color=COR_GRADE, linewidth=0.5, alpha=0.6)
    eixo.set_axisbelow(True)


def _sem_dados(eixo, titulo: str) -> None:
    """Mostra um aviso no lugar do gráfico quando não há o que plotar."""
    _estilizar(eixo, titulo)
    eixo.text(
        0.5,
        0.5,
        "Sem dados no período",
        ha="center",
        va="center",
        color=COR_GRADE,
        fontsize=10,
        transform=eixo.transAxes,
    )
    eixo.set_xticks([])
    eixo.set_yticks([])
    eixo.grid(False)


def resumo() -> dict[str, object]:
    """Números do cabeçalho do painel."""
    por_status = repositorio_ocorrencias.contar_por_status()
    pendentes = por_status.get("Pendente", 0)
    finalizadas = por_status.get("Finalizado", 0)
    registros = repositorio_ocorrencias.listar()
    abertas = [r for r in registros if r["status"] == "Pendente"]
    media = (
        round(sum(r["dias_pendentes"] or 0 for r in abertas) / len(abertas), 1)
        if abertas
        else 0.0
    )
    queimas = repositorio_queimas.totais_por_periodo()
    return {
        "total": pendentes + finalizadas,
        "pendentes": pendentes,
        "finalizadas": finalizadas,
        "media_dias_pendentes": media,
        "mais_antiga": max((r["dias_pendentes"] or 0 for r in abertas), default=0),
        "queimas": queimas["ocorrencias"],
        "area_queimada_ha": queimas["area_total_ha"],
    }


def _grafico_status(eixo, registros: list[dict]) -> None:
    contagem = Counter(r["status"] for r in registros)
    if not contagem:
        _sem_dados(eixo, "Ocorrências por status")
        return
    _estilizar(eixo, "Ocorrências por status")
    rotulos = list(contagem)
    valores = [contagem[r] for r in rotulos]
    cores = [COR_PENDENTE if r == "Pendente" else COR_FINALIZADO for r in rotulos]
    barras = eixo.bar(rotulos, valores, color=cores, width=0.55)
    eixo.bar_label(barras, color=COR_TEXTO, fontsize=9, padding=2)
    eixo.set_ylim(0, max(valores) * 1.2)


def _grafico_categorias(eixo, registros: list[dict], quantas: int = 8) -> None:
    contagem = Counter(r["categoria"] or "Sem categoria" for r in registros)
    if not contagem:
        _sem_dados(eixo, f"Categorias mais frequentes (top {quantas})")
        return
    _estilizar(eixo, f"Categorias mais frequentes (top {quantas})")
    itens = contagem.most_common(quantas)[::-1]
    rotulos = [nome[:28] for nome, _ in itens]
    valores = [total for _, total in itens]
    barras = eixo.barh(rotulos, valores, color=COR_BARRA, height=0.6)
    eixo.bar_label(barras, color=COR_TEXTO, fontsize=8, padding=2)
    eixo.set_xlim(0, max(valores) * 1.18)


def _grafico_evolucao(eixo, registros: list[dict]) -> None:
    por_mes: defaultdict[str, int] = defaultdict(int)
    for registro in registros:
        data_abertura = str(registro["data_abertura"] or "")
        if len(data_abertura) >= 7:
            por_mes[data_abertura[:7]] += 1
    if not por_mes:
        _sem_dados(eixo, "Aberturas por mês")
        return
    _estilizar(eixo, "Aberturas por mês")
    meses = sorted(por_mes)[-12:]
    valores = [por_mes[mes] for mes in meses]
    rotulos = [f"{mes[5:7]}/{mes[2:4]}" for mes in meses]
    eixo.plot(rotulos, valores, marker="o", color=COR_LINHA, linewidth=2, markersize=5)
    eixo.fill_between(range(len(valores)), valores, color=COR_LINHA, alpha=0.18)
    eixo.set_ylim(0, max(valores) * 1.3)


def _grafico_dias_pendentes(eixo, registros: list[dict]) -> None:
    faixas = {"0-7": 0, "8-15": 0, "16-30": 0, "31-60": 0, "60+": 0}
    for registro in registros:
        if registro["status"] != "Pendente":
            continue
        dias = registro["dias_pendentes"] or 0
        if dias <= 7:
            faixas["0-7"] += 1
        elif dias <= 15:
            faixas["8-15"] += 1
        elif dias <= 30:
            faixas["16-30"] += 1
        elif dias <= 60:
            faixas["31-60"] += 1
        else:
            faixas["60+"] += 1

    if not any(faixas.values()):
        _sem_dados(eixo, "Idade das ocorrências pendentes (dias)")
        return
    _estilizar(eixo, "Idade das ocorrências pendentes (dias)")
    barras = eixo.bar(list(faixas), list(faixas.values()), color=COR_PENDENTE, width=0.6)
    eixo.bar_label(barras, color=COR_TEXTO, fontsize=9, padding=2)
    eixo.set_ylim(0, max(faixas.values()) * 1.2)


def gerar_painel(destino: Path | None = None) -> Path:
    """Desenha os quatro gráficos num único PNG e devolve o caminho.

    O arquivo é sobrescrito a cada chamada, dentro da pasta de dados do
    aplicativo, para não espalhar imagens temporárias pelo disco.
    """
    registros = repositorio_ocorrencias.listar()
    destino = destino or (config.diretorio_dados() / ARQUIVO_PAINEL)

    figura, eixos = plt.subplots(2, 2, figsize=(12, 7), dpi=110)
    figura.patch.set_facecolor(COR_FUNDO)

    _grafico_status(eixos[0][0], registros)
    _grafico_categorias(eixos[0][1], registros)
    _grafico_evolucao(eixos[1][0], registros)
    _grafico_dias_pendentes(eixos[1][1], registros)

    numeros = resumo()
    figura.suptitle(
        f"{numeros['total']} ocorrências  ·  {numeros['pendentes']} pendentes  ·  "
        f"média de {numeros['media_dias_pendentes']} dias em aberto  ·  "
        f"emitido em {date.today().strftime('%d/%m/%Y')}",
        color=COR_TEXTO,
        fontsize=11,
    )
    figura.tight_layout(rect=(0, 0, 1, 0.95))
    figura.savefig(destino, facecolor=COR_FUNDO)
    plt.close(figura)
    return destino
