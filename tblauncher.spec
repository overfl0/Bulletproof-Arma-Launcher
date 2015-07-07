# -*- mode: python -*-

# Needed for generating the build number
import site
site.addsitedir(os.path.join(os.getcwd(), 'src', 'utils'))
import primitive_git

from kivy.tools.packaging.pyinstaller_hooks import install_hooks

# Create the build number
primitive_git.save_git_sha1_to_file('.', primitive_git.build_sha1_file)
install_hooks(globals())

a = Analysis(['src/launcher.py'],
             pathex=[''],
             hiddenimports=['concurrent', 'concurrent.futures'],
             runtime_hooks=None)

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
          name='tblauncher_alpha2.exe',
          debug=False,
          strip=None,
          upx=True,
          console=True )
