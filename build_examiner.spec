# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files


project_root = Path.cwd()
core_root = project_root / 'Core'

datas = []
for relative in [
    'Core',
    'users/templates',
    'users/static',
    'users/authentication',
    'exercises/fixtures',
    'nutrition/fixtures',
    'media',
]:
    source = core_root / relative
    if source.exists():
        datas.append((str(source), relative))

datas += collect_data_files('django.contrib.admin')
datas += collect_data_files('django.contrib.auth')
datas += collect_data_files('django.contrib.contenttypes')
datas += collect_data_files('django.contrib.sessions')
datas += collect_data_files('django.contrib.messages')
datas += collect_data_files('django.contrib.staticfiles')
datas += collect_data_files('allauth')
datas += collect_data_files('rest_framework')

hiddenimports = [
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt',
    'users',
    'users.authentication',
    'exercises',
    'nutrition',
    'services',
]


a = Analysis(
    ['Core/examiner_launcher.py'],
    pathex=[str(core_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='FitTrackExaminer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
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
    name='FitTrackExaminer',
)
