# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['backend.py'],
    pathex=[],
    binaries=[],
datas=[
    ('login.html', '.'),
    ('signup.html', '.'),
    ('welcomepage.html', '.'),
    ('style.css', '.'),
    ('script.js', '.'),
    ('gta6.mp4', '.'),
    ('videoend.png', '.'),
    ('build_version.txt', '.'),
],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='RUN_TO_RWANDA_6',
    icon='favicon.ico',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
