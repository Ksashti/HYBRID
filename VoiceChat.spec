# -*- mode: python ; coding: utf-8 -*-
import os
import sys

# Find opus.dll from pyogg
opus_binaries = []
try:
    import pyogg
    pyogg_dir = os.path.dirname(pyogg.__file__)
    opus_dll = os.path.join(pyogg_dir, 'opus.dll')
    if os.path.exists(opus_dll):
        opus_binaries.append((opus_dll, '.'))
except Exception:
    pass

a = Analysis(
    ['client/main.py'],
    pathex=['.'],
    binaries=opus_binaries,
    datas=[],
    hiddenimports=[
        'PyQt5.QtWidgets',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.sip',
        'opuslib',
        'opuslib.api',
        'opuslib.api.decoder',
        'opuslib.api.encoder',
        'opuslib.api.info',
        'opuslib.api.ctl',
        'opuslib.classes',
        'opuslib.exceptions',
        'pyogg',
        'client',
        'client.protocol',
        'client.config',
        'client.network',
        'client.network.text_client',
        'client.network.voice_client',
        'client.audio',
        'client.audio.engine',
        'client.audio.opus_codec',
        'client.audio.voice_modes',
        'client.ui',
        'client.ui.theme',
        'client.ui.login_window',
        'client.ui.main_window',
        'client.ui.sidebar',
        'client.ui.chat_panel',
        'client.ui.bottom_panel',
        'client.ui.settings_dialog',
        'client.ui.widgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'PyQt5.QtWebEngine',
        'PyQt5.QtWebEngineWidgets',
        'PyQt5.QtWebEngineCore',
        'PyQt5.Qt3D',
        'PyQt5.QtMultimedia',
        'PyQt5.QtBluetooth',
        'PyQt5.QtNfc',
        'PyQt5.QtQuick',
        'PyQt5.QtQml',
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'tkinter',
    ],
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
    name='HYBRID',
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
