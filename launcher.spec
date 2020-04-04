# -*- mode: python -*-

# Needed for generating the build number
import site
site.addsitedir(os.path.join(os.getcwd(), 'src', 'utils'))
site.addsitedir(os.path.join(os.getcwd(), 'src'))

import launcher_config
import os
import primitive_git

from kivy_deps import sdl2, glew

# Create the build number
primitive_git.save_git_sha1_to_file('.', primitive_git.build_sha1_file)
config_dir = 'resources/{}'.format(launcher_config.config_select.config_dir)

hiddenimports=[]
hiddenimports.append('importlib')  # Kivy 1.9.2
hiddenimports.append('_cffi_backend')  # Paramiko (cryptography)

a = Analysis(['src/launcher.py'],
             hiddenimports=hiddenimports)

# Add the build number
a.datas += [(primitive_git.build_sha1_file, primitive_git.build_sha1_file, 'DATA')]

pyz = PYZ(a.pure)
exe = EXE(pyz,
          Tree('./src', prefix='src', excludes=['*.pyc']),
          Tree(config_dir, prefix='resources'),  # resources/<name> directory contents
          Tree('./common_resources', prefix='common_resources'),
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
