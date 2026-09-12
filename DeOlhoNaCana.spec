# -*- mode: python ; coding: utf-8 -*-
"""Empacotamento com PyInstaller.

    pyinstaller DeOlhoNaCana.spec

Gera dist/DeOlhoNaCana/, que roda em máquinas sem Python instalado. Para
distribuir em modo portátil, crie uma pasta `dados/` vazia ao lado do
executável: o programa passa a gravar ali em vez de no perfil do usuário.
"""

from pathlib import Path

from kivy_deps import glew, sdl2
from kivymd import hooks_path as kivymd_hooks_path

RAIZ = Path(SPECPATH)
PACOTE = RAIZ / "deolhonacana"

# Os .kv e as imagens não são módulos Python: precisam ser copiados à mão.
# config.raiz_recursos() já sabe procurá-los em sys._MEIPASS quando congelado.
dados = [
    (str(PACOTE / "telas" / "*.kv"), "deolhonacana/telas"),
    (str(PACOTE / "dados" / "esquema.sql"), "deolhonacana/dados"),
    (str(PACOTE / "recursos" / "imagens" / "*"), "deolhonacana/recursos/imagens"),
]

a = Analysis(
    ["executar.py"],
    pathex=[str(RAIZ)],
    binaries=[],
    datas=dados,
    hiddenimports=["deolhonacana.telas"],
    hookspath=[kivymd_hooks_path],
    runtime_hooks=[],
    # O backend Agg do matplotlib é o único usado; os demais só incham o pacote.
    excludes=[
        "tkinter",
        "pytest",
        "PyQt5",
        "PySide2",
        "matplotlib.backends._backend_tk",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="DeOlhoNaCana",
    debug=False,
    strip=False,
    upx=True,
    console=False,
    icon=str(PACOTE / "recursos" / "imagens" / "icone.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    # SDL2 e GLEW são as bibliotecas nativas de janela e OpenGL do Kivy.
    *[Tree(caminho) for caminho in (sdl2.dep_bins + glew.dep_bins)],
    strip=False,
    upx=True,
    upx_exclude=[],
    name="DeOlhoNaCana",
)
