# -*- mode: python -*-

# Needed for generating the build number
import site
site.addsitedir(os.path.join(os.getcwd(), 'src', 'utils'))
site.addsitedir(os.path.join(os.getcwd(), 'src'))

import primitive_git
from config import config

# If the import below produces some errors, you need to patch your Kivy installation:
# https://github.com/kivy/kivy/pull/3652/files?short_path=90047c6
from kivy.tools.packaging.pyinstaller_hooks import get_hooks

from kivy.deps import sdl2, glew

# Create the build number
primitive_git.save_git_sha1_to_file('.', primitive_git.build_sha1_file)

a = Analysis(['src/launcher.py'],
             pathex=[''],
             hiddenimports=['concurrent', 'concurrent.futures'],
             **get_hooks())

# Add the build number
a.datas += [(primitive_git.build_sha1_file, primitive_git.build_sha1_file, 'DATA')]

pyz = PYZ(a.pure)
exe = EXE(pyz,
          Tree('./src'),
          Tree('./resources', excludes=['unused']),
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='{}.exe'.format(config.executable_name),
          *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
          debug=False,
          strip=None,
          upx=True,
          icon='./resources/icons/tb.ico',
          console=False )
