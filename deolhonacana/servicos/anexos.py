"""Cópia e recuperação das fotos anexadas às ocorrências.

O projeto antigo guardava no banco o caminho absoluto do arquivo escolhido
pelo usuário. Bastava mover ou renomear a foto original para o registro
apontar para o nada. Aqui o arquivo é copiado para dentro da pasta de dados do
aplicativo e o banco guarda só o nome — o conjunto banco + pasta de anexos
passa a ser autocontido e pode ser copiado inteiro para outra máquina.
"""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from deolhonacana import config

#: Extensões aceitas no seletor de arquivos.
EXTENSOES_ACEITAS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}

#: Tamanho máximo por anexo, para o banco de fotos não crescer sem limite.
TAMANHO_MAXIMO_MB = 15


class ErroAnexo(Exception):
    """Problema ao anexar um arquivo, com mensagem pronta para o usuário."""


def e_imagem(caminho: str | Path) -> bool:
    """Diz se o arquivo tem extensão de imagem reconhecida."""
    return Path(caminho).suffix.lower() in EXTENSOES_ACEITAS


def guardar(origem: str | Path) -> str:
    """Copia a imagem para a pasta de anexos e devolve o nome gravado.

    O nome é único, gerado a partir de UUID, preservando a extensão original.
    Assim duas fotos chamadas ``foto.jpg`` nunca se sobrescrevem.
    """
    origem = Path(origem)

    if not origem.is_file():
        raise ErroAnexo("Arquivo não encontrado.")
    if not e_imagem(origem):
        aceitas = ", ".join(sorted(EXTENSOES_ACEITAS))
        raise ErroAnexo(f"Formato não aceito. Use uma imagem ({aceitas}).")

    tamanho_mb = origem.stat().st_size / (1024 * 1024)
    if tamanho_mb > TAMANHO_MAXIMO_MB:
        raise ErroAnexo(f"A imagem tem {tamanho_mb:.1f} MB; o limite é {TAMANHO_MAXIMO_MB} MB.")

    nome = f"{uuid.uuid4().hex}{origem.suffix.lower()}"
    destino = config.diretorio_anexos() / nome
    try:
        shutil.copy2(origem, destino)
    except OSError as erro:
        raise ErroAnexo(f"Não foi possível copiar a imagem: {erro}") from erro
    return nome


def caminho_de(nome: str) -> Path:
    """Caminho absoluto de um anexo a partir do nome guardado no banco."""
    return config.diretorio_anexos() / nome


def caminho_para_exibir(nome: str | None) -> str:
    """Caminho a colocar num widget de imagem, ou string vazia se sumiu."""
    if not nome:
        return ""
    arquivo = caminho_de(nome)
    return str(arquivo) if arquivo.is_file() else ""


def remover(nome: str) -> bool:
    """Apaga o arquivo de um anexo do disco. Ausente conta como removido."""
    arquivo = caminho_de(nome)
    try:
        arquivo.unlink(missing_ok=True)
    except OSError:
        return False
    return True
