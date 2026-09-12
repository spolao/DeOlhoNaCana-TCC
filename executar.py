"""Ponto de entrada do De Olho na Cana.

    python executar.py

Não é preciso criar banco nem rodar script antes: a primeira execução monta
tudo na pasta de dados do usuário.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Permite rodar o arquivo de qualquer diretório, sem instalar o pacote.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from deolhonacana.app import executar  # noqa: E402

if __name__ == "__main__":
    executar()
