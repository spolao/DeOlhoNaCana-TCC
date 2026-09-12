"""Conversões entre o formato que o usuário vê e o que o banco guarda.

O banco grava datas em ISO-8601 porque é o único formato que o SQLite compara
e subtrai corretamente. O usuário brasileiro digita e lê dd/mm/aaaa. Toda a
tradução entre os dois mundos acontece aqui, e em nenhum outro lugar.
"""

from __future__ import annotations

from datetime import date, datetime

FORMATO_BR = "%d/%m/%Y"
FORMATO_ISO = "%Y-%m-%d"


def data_para_texto(valor: date | str | None) -> str:
    """Formata uma data para exibição em dd/mm/aaaa.

    Aceita ``date``, string ISO ou ``None``; devolve string vazia quando não
    houver data.
    """
    if not valor:
        return ""
    if isinstance(valor, date):
        return valor.strftime(FORMATO_BR)
    try:
        return datetime.strptime(valor, FORMATO_ISO).strftime(FORMATO_BR)
    except ValueError:
        return str(valor)


def texto_para_data(texto: str | None) -> date | None:
    """Interpreta o que o usuário digitou como data.

    Aceita dd/mm/aaaa e também ISO, já que o seletor de datas do KivyMD
    devolve ``str(date)``. Devolve ``None`` se não der para interpretar.
    """
    if not texto:
        return None
    texto = texto.strip()
    for formato in (FORMATO_BR, FORMATO_ISO):
        try:
            return datetime.strptime(texto, formato).date()
        except ValueError:
            continue
    return None


def hora_valida(texto: str | None) -> bool:
    """Confere se o texto é uma hora no formato HH:MM."""
    if not texto:
        return False
    try:
        datetime.strptime(texto.strip(), "%H:%M")
    except ValueError:
        return False
    return True


def para_numero(texto: str | None, padrao: float = 0.0) -> float:
    """Lê um número digitado, aceitando as duas notações em uso.

    O operador pode digitar ``12,5`` no padrão brasileiro, e o teclado
    numérico do formulário produz ``12.5``. Ambos valem:

    - com vírgula e ponto (``1.234,56``), o ponto é separador de milhar;
    - só com vírgula (``12,5``), a vírgula é o separador decimal;
    - só com ponto (``12.5``), o ponto é o separador decimal.

    Campo vazio ou conteúdo não numérico devolve ``padrao`` em vez de estourar,
    porque quase todo campo numérico do formulário é opcional.
    """
    if texto is None:
        return padrao
    texto = str(texto).strip()
    if not texto:
        return padrao

    if "," in texto:
        # Vírgula presente: ela é o decimal, e o ponto (se houver) é milhar.
        texto = texto.replace(".", "").replace(",", ".")

    try:
        return float(texto)
    except ValueError:
        return padrao


def para_inteiro(texto: str | None, padrao: int = 0) -> int:
    """Versão inteira de :func:`para_numero`."""
    return int(para_numero(texto, padrao))


def numero_para_texto(valor: float | None, casas: int = 2) -> str:
    """Formata um número no padrão brasileiro, com vírgula decimal."""
    if valor is None:
        return ""
    return f"{valor:,.{casas}f}".replace(",", "\x00").replace(".", ",").replace(
        "\x00", "."
    )


def encurtar(texto: str | None, limite: int = 40) -> str:
    """Corta um texto longo para caber numa célula de tabela."""
    if not texto:
        return ""
    texto = " ".join(str(texto).split())
    if len(texto) <= limite:
        return texto
    return texto[: limite - 1].rstrip() + "…"
