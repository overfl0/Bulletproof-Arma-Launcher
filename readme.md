# Build

From the project root
execute: `pyinstaller tblauncher.spec`
to build a single executable

If necessary execute the following command to
rebuild the spec file. A newly spec file will not work, see kivy packaging wiki:
`pyinstaller --name tblauncher --onefile src\launcher.py`
