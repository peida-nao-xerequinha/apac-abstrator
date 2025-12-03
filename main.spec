# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

BASE_DIR = os.getcwd()

datas = [
    ('data', 'data'),
    ('assets', 'assets'),
    ('input', 'input'),
    ('output', 'output'),
]

datas += collect_data_files('PySide6')

hiddenimports = collect_submodules('PySide6')

a = Analysis(
    [
        'main.py',
        'apac_manager.py',
        'corpo.py',
        'header.py',
        'procedimentos.py',
        'utils.py',
        'variavel.py'
    ],
    pathex=[BASE_DIR],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        
    ],
    noarchive=False,
    cipher=None,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Abstrador',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=os.path.join(BASE_DIR, 'assets', 'mini.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='Abstrador'
)