# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.win32.versioninfo import (
    VSVersionInfo,
    FixedFileInfo,
    StringFileInfo,
    StringTable,
    StringStruct,
    VarFileInfo,
    VarStruct,
)

app_name = 'simple-yt-dlp-wrapper'
version_info = VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=(1, 0, 0, 0),
        prodvers=(1, 0, 0, 0),
        mask=0x3F,
        flags=0x0,
        OS=0x40004,
        fileType=0x1,
        subtype=0x0,
        date=(0, 0),
    ),
    kids=[
        StringFileInfo(
            [
                StringTable(
                    '041104B0',
                    [
                        StringStruct('CompanyName', 'simple-yt-dlp-wrapper'),
                        StringStruct('FileDescription', 'simple-yt-dlp-wrapper'),
                        StringStruct('FileVersion', '1.0.0.0'),
                        StringStruct('InternalName', app_name),
                        StringStruct('OriginalFilename', f'{app_name}.exe'),
                        StringStruct('ProductName', 'simple-yt-dlp-wrapper'),
                        StringStruct('ProductVersion', '1.0.0.0'),
                    ],
                )
            ]
        ),
        VarFileInfo([VarStruct('Translation', [1041, 1200])]),
    ],
)

a = Analysis(
    ['app.pyw'],
    pathex=[],
    binaries=[],
    datas=[('resources/icon.ico', 'resources')],
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
    [],
    exclude_binaries=True,
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=['resources/icon.ico'],
    version=version_info,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=app_name,
)
