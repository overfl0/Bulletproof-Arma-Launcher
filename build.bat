@echo #########################################################################
@echo Deleting required files
@echo #########################################################################
del tblauncher.exe c:\vagrant\tblauncher 2> NUL
for /d %%G in ("build\tblauncher\setuptools*.egg") do rmdir /s /q "%%~G"

@rem @echo #########################################################################
@rem @echo Running unit tests...
@rem @echo #########################################################################
@rem nosetests tests -a "!integration"--nocapture

@rem If tests fail, do NOT build!
@rem @if %errorlevel% neq 0 exit /b %errorlevel%

@echo #########################################################################
@echo Running integration tests...
@echo #########################################################################
nosetests tests -a "integration" --nocapture

@rem If tests fail, do NOT build!
@if %errorlevel% neq 0 exit /b %errorlevel%

@echo #########################################################################
@echo Tests passed, building the launcher...
@echo #########################################################################
python c:\Python27\Scripts\pyinstaller-script.py tblauncher.spec
copy dist\tblauncher.exe c:\vagrant
copy dist\tblauncher.exe .
