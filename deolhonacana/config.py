"""Configuração e resolução de caminhos.

O aplicativo é monomáquina e não depende de rede: tudo — banco, anexos e
relatórios — vive em pastas locais resolvidas em tempo de execução. Nenhum
caminho é fixo no código, de modo que o programa roda em qualquer computador,
sob qualquer usuário do sistema e também a partir de um pendrive.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NOME = "De Olho na Cana"
ORGANIZACAO = "Usina Modelo"
VERSAO = "2.0.0"

#: Nome da pasta usada tanto no modo portátil quanto no diretório do usuário.
PASTA_APLICACAO = "DeOlhoNaCana"

#: Variável de ambiente que sobrepõe a escolha automática do diretório de dados.
VAR_AMBIENTE_DADOS = "DONC_DIR"


def _raiz_projeto() -> Path:
    """Pasta que contém o pacote — a raiz do repositório em execução normal."""
    return Path(__file__).resolve().parent.parent


def _base_executavel() -> Path:
    """Pasta onde o programa está instalado, considerando build do PyInstaller."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return _raiz_projeto()


def raiz_recursos() -> Path:
    """Pasta do pacote com os recursos estáticos (.kv e imagens).

    Sob PyInstaller os arquivos são extraídos em ``sys._MEIPASS``; fora dele,
    ficam ao lado deste módulo.
    """
    embutido = getattr(sys, "_MEIPASS", None)
    if embutido:
        return Path(embutido) / "deolhonacana"
    return Path(__file__).resolve().parent


def diretorio_dados() -> Path:
    """Diretório gravável onde ficam banco e anexos.

    Ordem de resolução:

    1. variável de ambiente ``DONC_DIR``, se definida;
    2. pasta ``dados/`` ao lado do executável, se já existir (modo portátil);
    3. diretório de dados do usuário do sistema operacional.
    """
    definido = os.environ.get(VAR_AMBIENTE_DADOS, "").strip()
    if definido:
        destino = Path(definido).expanduser()
    else:
        portatil = _base_executavel() / "dados"
        if portatil.is_dir():
            destino = portatil
        elif os.name == "nt":
            raiz = os.environ.get("APPDATA") or Path.home()
            destino = Path(raiz) / PASTA_APLICACAO
        elif sys.platform == "darwin":
            destino = Path.home() / "Library" / "Application Support" / PASTA_APLICACAO
        else:
            raiz = os.environ.get("XDG_DATA_HOME") or (Path.home() / ".local" / "share")
            destino = Path(raiz) / PASTA_APLICACAO

    destino.mkdir(parents=True, exist_ok=True)
    return destino


def caminho_banco() -> Path:
    """Arquivo SQLite único do sistema."""
    return diretorio_dados() / "deolhonacana.db"


def diretorio_anexos() -> Path:
    """Pasta para onde as fotos escolhidas pelo usuário são copiadas."""
    destino = diretorio_dados() / "anexos"
    destino.mkdir(parents=True, exist_ok=True)
    return destino


def diretorio_relatorios() -> Path:
    """Pasta onde os PDFs são gravados — Documentos do usuário, quando existir."""
    documentos = Path.home() / "Documents"
    base = documentos if documentos.is_dir() else diretorio_dados()
    destino = base / APP_NOME
    destino.mkdir(parents=True, exist_ok=True)
    return destino


def diretorio_imagens() -> Path:
    """Pasta dos recursos gráficos gerados por ``ferramentas/gerar_recursos.py``."""
    return raiz_recursos() / "recursos" / "imagens"


def caminho_imagem(nome: str) -> str:
    """Caminho de uma imagem como texto, no formato que o Kivy espera.

    Devolve string vazia quando o arquivo não existe, para que a interface
    apenas não mostre a imagem em vez de quebrar.
    """
    arquivo = diretorio_imagens() / nome
    return str(arquivo) if arquivo.is_file() else ""


def caminho_tela(nome_kv: str) -> str:
    """Caminho absoluto de um arquivo ``.kv`` do pacote."""
    return str(raiz_recursos() / "telas" / nome_kv)


def caminho_esquema_sql() -> Path:
    """Arquivo DDL usado para criar o banco na primeira execução."""
    return raiz_recursos() / "dados" / "esquema.sql"
