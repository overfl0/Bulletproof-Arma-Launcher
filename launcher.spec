# -*- mode: python -*-

# Needed for generating the build number
import site
site.addsitedir(os.path.join(os.getcwd(), 'src', 'utils'))
site.addsitedir(os.path.join(os.getcwd(), 'src'))

import launcher_config
import os
import primitive_git

from kivy.tools.packaging.pyinstaller_hooks import get_hooks
from kivy.deps import sdl2, glew

# Create the build number
primitive_git.save_git_sha1_to_file('.', primitive_git.build_sha1_file)
config_dir = 'resources/{}'.format(launcher_config.config_select.config_dir)

a = Analysis([
                'src/launcher.py',
                '{}/launcher_configuration.py'.format(config_dir),
             ],
             pathex=[''],
             hiddenimports=['concurrent', 'concurrent.futures', 'importlib'],
             **get_hooks())

# Add the build number
a.datas += [(primitive_git.build_sha1_file, primitive_git.build_sha1_file, 'DATA')]

pyz = PYZ(a.pure)
exe = EXE(pyz,
          Tree('./src'),
          Tree(config_dir),  # resources/<name> directory contents
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='{}.exe'.format(launcher_config.executable_name),
          *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
          debug=False,
          strip=None,
          upx=True,
          icon=os.path.join(config_dir, launcher_config.icon),
          console=False )
