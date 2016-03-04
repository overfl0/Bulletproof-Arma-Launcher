@echo #########################################################################
@echo Deleting required files
@echo #########################################################################
del tblauncher.exe c:\vagrant\tblauncher 2> NUL
for /d %%G in ("build\tblauncher\setuptools*.egg") do rmdir /s /q "%%~G"

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

python c:\Kivy-1.8.0-py2.7-win32\Python27\Scripts\pyinstaller-script.py tblauncher.spec
copy dist\tblauncher.exe c:\vagrant
copy dist\tblauncher.exe .
