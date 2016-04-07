@echo #########################################################################
@echo Deleting required files
@echo #########################################################################
del TB_Launcher.exe c:\vagrant\TB_Launcher.exe 2> NUL
for /d %%G in ("build\TB_Launcher\setuptools*.egg") do rmdir /s /q "%%~G"

@rem uncomment below to skip tests
@rem goto end_of_tests

@echo #########################################################################
@echo Running unit tests...
@echo #########################################################################
nosetests tests -a "!integration"--nocapture

@rem If tests fail, do NOT build!
@if %errorlevel% neq 0 exit /b %errorlevel%

@echo #########################################################################
@echo Running integration tests...
@echo #########################################################################
nosetests tests -a "integration" --nocapture

@rem If tests fail, do NOT build!
@if %errorlevel% neq 0 exit /b %errorlevel%

@echo #########################################################################
@echo Tests passed, building the launcher...
@echo #########################################################################
:end_of_tests

python c:\Kivy-1.8.0-py2.7-win32\Python27\Scripts\pyinstaller-script.py launcher.spec
copy dist\TB_Launcher.exe c:\vagrant
copy dist\TB_Launcher.exe .
