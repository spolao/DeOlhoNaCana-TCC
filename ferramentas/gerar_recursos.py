"""Gera os recursos gráficos do aplicativo.

O projeto anterior carregava cinco imagens de um compartilhamento de rede
corporativo — arquivos que nem chegaram a ser versionados, de modo que o
programa quebrava em qualquer outra máquina. Aqui as imagens são desenhadas
por código com Pillow: ninguém precisa baixar nada, não há arquivo binário no
repositório e não há dúvida de licença.

    python ferramentas/gerar_recursos.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from deolhonacana import config  # noqa: E402

VERDE_ESCURO = (32, 74, 48, 255)
VERDE = (58, 130, 82, 255)
VERDE_CLARO = (126, 191, 128, 255)
PALHA = (214, 178, 88, 255)
CINZA = (96, 100, 104, 255)
CINZA_CLARO = (150, 155, 160, 255)
FUNDO_VAZIO = (44, 46, 48, 255)


def _colmo(desenho: ImageDraw.ImageDraw, base_x: int, base_y: int, altura: int,
           largura: int, inclinacao: float, cor: tuple) -> None:
    """Desenha um colmo de cana: hastes com gomos e um par de folhas."""
    topo_x = base_x + int(altura * inclinacao)
    gomos = 6
    for indice in range(gomos):
        inicio = base_y - altura * indice // gomos
        fim = base_y - altura * (indice + 1) // gomos
        deslocamento_inicio = int((base_y - inicio) * inclinacao)
        deslocamento_fim = int((base_y - fim) * inclinacao)
        desenho.rounded_rectangle(
            [
                base_x + deslocamento_inicio - largura // 2,
                fim + 3,
                base_x + deslocamento_fim + largura // 2,
                inicio,
            ],
            radius=largura // 3,
            fill=cor,
            outline=VERDE_ESCURO,
            width=2,
        )

    for lado in (-1, 1):
        ponta_x = topo_x + lado * int(altura * 0.42)
        ponta_y = base_y - altura - int(altura * 0.16)
        desenho.polygon(
            [
                (topo_x, base_y - altura),
                (ponta_x, ponta_y),
                (topo_x + lado * int(altura * 0.10), base_y - altura + int(altura * 0.16)),
            ],
            fill=VERDE_CLARO,
        )


def gerar_marca(destino: Path, lado: int = 512) -> Path:
    """Marca do sistema: uma lupa sobre um talhão de cana."""
    imagem = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    desenho = ImageDraw.Draw(imagem)

    margem = int(lado * 0.06)
    desenho.rounded_rectangle(
        [margem, margem, lado - margem, lado - margem],
        radius=int(lado * 0.22),
        fill=VERDE_ESCURO,
    )

    base = int(lado * 0.80)
    for posicao, altura, inclinacao in (
        (0.30, 0.44, -0.05),
        (0.46, 0.54, 0.02),
        (0.62, 0.46, 0.07),
    ):
        _colmo(
            desenho,
            int(lado * posicao),
            base,
            int(lado * altura),
            int(lado * 0.055),
            inclinacao,
            VERDE,
        )

    # A lupa: aro grosso e cabo inclinado, aludindo ao nome do sistema.
    centro = (int(lado * 0.58), int(lado * 0.44))
    raio = int(lado * 0.20)
    desenho.ellipse(
        [centro[0] - raio, centro[1] - raio, centro[0] + raio, centro[1] + raio],
        outline=PALHA,
        width=int(lado * 0.045),
    )
    angulo = math.radians(45)
    inicio_cabo = (
        centro[0] + int(raio * math.cos(angulo)),
        centro[1] + int(raio * math.sin(angulo)),
    )
    fim_cabo = (
        centro[0] + int(raio * 1.85 * math.cos(angulo)),
        centro[1] + int(raio * 1.85 * math.sin(angulo)),
    )
    desenho.line([inicio_cabo, fim_cabo], fill=PALHA, width=int(lado * 0.05))

    imagem.save(destino)
    return destino


def gerar_icone(destino: Path, origem: Path) -> Path:
    """Ícone .ico multi-resolução para a janela e para o executável."""
    marca = Image.open(origem).convert("RGBA")
    marca.save(destino, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    return destino


def gerar_sem_foto(destino: Path, largura: int = 480, altura: int = 360) -> Path:
    """Espaço reservado exibido enquanto nenhuma foto foi anexada."""
    imagem = Image.new("RGBA", (largura, altura), FUNDO_VAZIO)
    desenho = ImageDraw.Draw(imagem)

    desenho.rounded_rectangle(
        [6, 6, largura - 6, altura - 6], radius=14, outline=CINZA, width=3
    )

    # Silhueta de montanha e sol, o desenho universal de "imagem ausente".
    base = int(altura * 0.72)
    desenho.polygon(
        [(int(largura * 0.18), base), (int(largura * 0.40), int(altura * 0.38)),
         (int(largura * 0.60), base)],
        fill=CINZA,
    )
    desenho.polygon(
        [(int(largura * 0.46), base), (int(largura * 0.66), int(altura * 0.48)),
         (int(largura * 0.86), base)],
        fill=CINZA_CLARO,
    )
    raio_sol = int(altura * 0.075)
    centro_sol = (int(largura * 0.74), int(altura * 0.28))
    desenho.ellipse(
        [centro_sol[0] - raio_sol, centro_sol[1] - raio_sol,
         centro_sol[0] + raio_sol, centro_sol[1] + raio_sol],
        fill=PALHA,
    )
    desenho.line([(int(largura * 0.14), base), (int(largura * 0.86), base)],
                 fill=CINZA_CLARO, width=3)

    texto = "sem foto"
    caixa = desenho.textbbox((0, 0), texto)
    desenho.text(
        ((largura - caixa[2]) / 2, altura * 0.80),
        texto,
        fill=CINZA_CLARO,
    )

    imagem.save(destino)
    return destino


def gerar_cabecalho(destino: Path, largura: int = 1200, altura: int = 160) -> Path:
    """Faixa horizontal com a marca, usada no topo de telas largas."""
    imagem = Image.new("RGBA", (largura, altura), VERDE_ESCURO)
    desenho = ImageDraw.Draw(imagem)

    for indice in range(9):
        _colmo(
            desenho,
            int(largura * (0.06 + indice * 0.105)),
            altura - 12,
            int(altura * 0.72),
            10,
            -0.04 + indice * 0.012,
            VERDE if indice % 2 == 0 else VERDE_CLARO,
        )

    brilho = imagem.filter(ImageFilter.GaussianBlur(1))
    brilho.save(destino)
    return destino


def gerar_todos() -> list[Path]:
    """Gera todas as imagens dentro de ``deolhonacana/recursos/imagens``."""
    pasta = config.diretorio_imagens()
    pasta.mkdir(parents=True, exist_ok=True)

    marca = gerar_marca(pasta / "marca.png")
    gerados = [
        marca,
        gerar_sem_foto(pasta / "sem-foto.png"),
        gerar_cabecalho(pasta / "cabecalho.png"),
        gerar_icone(pasta / "icone.ico", marca),
    ]
    return gerados


if __name__ == "__main__":
    for arquivo in gerar_todos():
        print(f"gerado: {arquivo}")
