
@echo Building all the available launchers in "resources" directory 

@for /D %%A IN ("resources\*") DO (
    @echo ********************************************************************************
    @echo Building %%~nxA...
    @echo ********************************************************************************

    del src\launcher_config\config_select.pyc
    echo config_dir = u'%%~nxA' > src\launcher_config\config_select.py
    python build.py new
)
