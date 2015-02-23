# -*- mode: python -*-
from kivy.tools.packaging.pyinstaller_hooks import install_hooks
install_hooks(globals())

a = Analysis(['src\\launcher.py'],
             pathex=['H:\\projects\\tacbf-launcher'],
             hiddenimports=['concurrent', 'concurrent.futures'],
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          Tree('./src'),
          Tree('./resources'),
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='tblauncher.exe',
          debug=False,
          strip=None,
          upx=True,
          console=True )
