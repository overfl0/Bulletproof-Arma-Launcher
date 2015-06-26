setlocal
rem del /q tools\tblauncher\* tools\tblauncher.torrent

rem python c:\Kivy-1.8.0-py2.7-win32\Python27\Scripts\pyinstaller-script.py tblauncher.spec
rem copy dist\tblauncher.exe tools\tblauncher\tblauncher.exe

cd tools

python create_torrent.py -d tblauncher
python torrent_client.py tblauncher.torrent