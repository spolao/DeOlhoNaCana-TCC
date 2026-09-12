"""Geração do relatório em PDF das ocorrências filtradas.

Era o botão "Gerar PDF" da tela inicial, que não fazia nada. O relatório sai
em Documentos/De Olho na Cana, com o mesmo recorte que estiver aplicado na
tela de consulta, e inclui as fotos anexadas.
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from deolhonacana import config
from deolhonacana.dados import repositorio_ocorrencias
from deolhonacana.servicos import anexos as servico_anexos
from deolhonacana.servicos import formato

COR_CABECALHO = colors.HexColor("#2f5d3f")
COR_LINHA_PAR = colors.HexColor("#f2f5f2")
COR_PENDENTE = colors.HexColor("#c1440e")
COR_FINALIZADO = colors.HexColor("#2f7a4d")

COLUNAS = [
    ("id", "Id", 12 * mm),
    ("data_abertura", "Abertura", 22 * mm),
    ("gleba", "Gleba", 16 * mm),
    ("quadra", "Quadra", 16 * mm),
    ("fazenda", "Fazenda", 40 * mm),
    ("servico", "Serviço", 62 * mm),
    ("observacao", "Observação", 50 * mm),
    ("dias_pendentes", "Dias", 12 * mm),
    ("status", "Status", 22 * mm),
    ("responsavel", "Responsável", 30 * mm),
]


def _estilos() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "titulo": ParagraphStyle(
            "TituloRelatorio",
            parent=base["Title"],
            fontSize=16,
            spaceAfter=2,
            textColor=COR_CABECALHO,
        ),
        "subtitulo": ParagraphStyle(
            "SubtituloRelatorio",
            parent=base["Normal"],
            fontSize=9,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#555555"),
            spaceAfter=8,
        ),
        "celula": ParagraphStyle(
            "Celula", parent=base["Normal"], fontSize=7.5, leading=9
        ),
        "secao": ParagraphStyle(
            "Secao",
            parent=base["Heading2"],
            fontSize=12,
            textColor=COR_CABECALHO,
            spaceBefore=6,
        ),
        "legenda": ParagraphStyle(
            "Legenda",
            parent=base["Normal"],
            fontSize=8,
            textColor=colors.HexColor("#555555"),
            alignment=TA_CENTER,
        ),
    }


def _valor_da_celula(registro: dict, coluna: str) -> str:
    valor = registro.get(coluna)
    if coluna in {"data_abertura", "data_conclusao"}:
        return formato.data_para_texto(valor if valor is None else str(valor))
    if coluna == "observacao":
        return formato.encurtar(valor, 90)
    if coluna == "servico":
        return formato.encurtar(valor, 48)
    return "" if valor is None else str(valor)


def _tabela(registros: list[dict], estilos: dict) -> Table:
    cabecalho = [Paragraph(f"<b>{titulo}</b>", estilos["celula"]) for _, titulo, _ in COLUNAS]
    linhas = [cabecalho]
    for registro in registros:
        linhas.append(
            [
                Paragraph(_valor_da_celula(registro, coluna), estilos["celula"])
                for coluna, _, _ in COLUNAS
            ]
        )

    tabela = Table(
        linhas,
        colWidths=[largura for _, _, largura in COLUNAS],
        repeatRows=1,
    )
    estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), COR_CABECALHO),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cccccc")),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    indice_status = [c for c, _, _ in COLUNAS].index("status")
    for numero, registro in enumerate(registros, start=1):
        if numero % 2 == 0:
            estilo.append(("BACKGROUND", (0, numero), (-1, numero), COR_LINHA_PAR))
        cor = COR_PENDENTE if registro.get("status") == "Pendente" else COR_FINALIZADO
        estilo.append(
            ("TEXTCOLOR", (indice_status, numero), (indice_status, numero), cor)
        )
    tabela.setStyle(TableStyle(estilo))
    return tabela


def _paginas_de_fotos(registros: list[dict], estilos: dict) -> list:
    """Anexa as fotos das ocorrências que têm imagem, três por linha."""
    com_foto = [r for r in registros if r.get("qtd_anexos")]
    if not com_foto:
        return []

    elementos: list = [PageBreak(), Paragraph("Registro fotográfico", estilos["secao"])]
    for registro in com_foto:
        arquivos = repositorio_ocorrencias.listar_anexos(registro["id"])
        celulas, legendas = [], []
        for nome in arquivos:
            caminho = servico_anexos.caminho_de(nome)
            if not caminho.is_file():
                continue
            try:
                celulas.append(Image(str(caminho), width=55 * mm, height=41 * mm))
            except Exception:
                # Arquivo corrompido ou formato que o reportlab não abre: o
                # relatório continua sem essa foto.
                continue
            legendas.append(
                Paragraph(
                    f"Ocorrência {registro['id']} — "
                    f"{formato.data_para_texto(str(registro['data_abertura']))}",
                    estilos["legenda"],
                )
            )
        if not celulas:
            continue
        for inicio in range(0, len(celulas), 3):
            grupo = celulas[inicio : inicio + 3]
            rotulos = legendas[inicio : inicio + 3]
            grade = Table([grupo, rotulos], colWidths=[60 * mm] * len(grupo))
            grade.setStyle(
                TableStyle(
                    [
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
                    ]
                )
            )
            elementos.extend([grade, Spacer(1, 5 * mm)])
    return elementos


def gerar(
    registros: list[dict],
    descricao_filtro: str = "todas as ocorrências",
    incluir_fotos: bool = True,
) -> Path:
    """Monta o PDF e devolve o caminho do arquivo gravado.

    Levanta :class:`ValueError` se a lista estiver vazia — não faz sentido
    emitir um relatório sem linha nenhuma.
    """
    if not registros:
        raise ValueError("Não há ocorrências para incluir no relatório.")

    estilos = _estilos()
    carimbo = datetime.now().strftime("%Y%m%d-%H%M%S")
    destino = config.diretorio_relatorios() / f"ocorrencias-{carimbo}.pdf"

    documento = SimpleDocTemplate(
        str(destino),
        pagesize=landscape(A4),
        leftMargin=10 * mm,
        rightMargin=10 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        title=f"{config.APP_NOME} — Relatório de ocorrências",
        author=config.APP_NOME,
    )

    pendentes = sum(1 for r in registros if r.get("status") == "Pendente")
    elementos = [
        Paragraph(f"{config.APP_NOME} — Relatório de ocorrências", estilos["titulo"]),
        Paragraph(
            f"{config.ORGANIZACAO} · Filtro: {descricao_filtro} · "
            f"{len(registros)} registro(s), {pendentes} pendente(s) · "
            f"Emitido em {datetime.now().strftime('%d/%m/%Y às %H:%M')}",
            estilos["subtitulo"],
        ),
        _tabela(registros, estilos),
    ]
    if incluir_fotos:
        elementos.extend(_paginas_de_fotos(registros, estilos))

    documento.build(elementos)
    return destino


def abrir_no_sistema(caminho: Path) -> bool:
    """Abre o arquivo no leitor padrão do sistema operacional.

    Devolve ``False`` quando não foi possível abrir; o chamador então apenas
    informa o caminho ao usuário.
    """
    try:
        if os.name == "nt":
            os.startfile(caminho)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.run(["open", str(caminho)], check=False)
        else:
            subprocess.run(["xdg-open", str(caminho)], check=False)
    except OSError:
        return False
    return True
