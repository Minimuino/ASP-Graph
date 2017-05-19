# -*- mode: python -*-
# -*- coding: utf-8 -*-

# Template code found at http://howcanfix.com/52141/pyinstaller-kivy-clockapp-example-issue

import os
from os.path import join

from kivy import kivy_data_dir
from kivy.tools.packaging import pyinstaller_hooks as hooks

absolute_path = '/path/to/project/'
block_cipher = None
kivy_deps_all = hooks.get_deps_all()
kivy_factory_modules = hooks.get_factory_modules()

datas = [(join(absolute_path, 'src/main.kv'), '.')]
binaries = [(join(absolute_path, 'lib/gringo.so'), '.')]

# list of modules to exclude from analysis
excludes = ['gi', 'Tkinter', '_tkinter', 'twisted', 'pygments', 'pygame', 'matplotlib', 'cv2', 'numpy']

# list of hiddenimports
hiddenimports = kivy_deps_all['hiddenimports'] + kivy_factory_modules

# assets
kivy_assets_toc = Tree(kivy_data_dir, prefix=join('kivy_install', 'data'))
source_assets_toc = []
assets_toc = [kivy_assets_toc, source_assets_toc]

tocs = assets_toc


a = Analysis([join(absolute_path, 'src/main.py')],
             pathex=[join(absolute_path, 'bin')],
             binaries=binaries,
             datas=datas,
             hiddenimports=hiddenimports,
             hookspath=[],
             runtime_hooks=[],
             excludes=excludes,
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

##
# Build into one folder:
##
exe = EXE(pyz,
          a.scripts,
          name='ASP-Graph',
          exclude_binaries=True,
          debug=False,
          strip=False,
          upx=True,
          console=True)

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               *tocs,
               strip=False,
               upx=True,
               name='ASP-Graph')

##
# Build into one file:
##
# exe = EXE(pyz,
#           a.scripts,
#           a.binaries,
#           a.zipfiles,
#           a.datas,
#           name='ASP-Graph',
#           exclude_binaries=False,
#           debug=False,
#           strip=False,
#           upx=True,
#           console=True)
