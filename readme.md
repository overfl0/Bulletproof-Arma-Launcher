# Install

Manually installing the environment is now quite tricky as it involves, among other things, getting the right version of Kivy (1.9.1) and patching it with our own custom patches ([located in the Patches directory](https://github.com/overfl0/Bulletproof-Build-Environment/tree/master/Patches) of the `Bulletproof-Build-Environment` repository).

We're trying to make it as easy as possible to start working on the launcher and we have created [a Vagrant configuration file that will create a virtual machine](https://github.com/overfl0/Bulletproof-Build-Environment) containing everything that is needed to code right away.

Until issues with Kivy are fixed and the right patches are included in the Kivy source code, this is the preferred method of working on the launcher.
# Running

##### LiClipse
Open LiClipse, select the default workspace and run ```launcher.py```

##### Manually
Double click `src\launcher.py` or open a command prompt and execute `python src\launcher.py`

##### Fake Steam, Arma, TeamSpeak installation
To fake Steam, Arma, TeamSpeak installation and set several other internal variables, copy ```devmode_sample.conf``` to ```devmode.conf``` and put it in the same directory as you're running the launcher from. Then, uncomment and/or modify its contents accordingly.

# Running The Tests

To run the Tests cd into the src dir and run,

for unit test

`nosetests ../tests -a "!integration" --nocapture`

for integration tests

`nosetests ../tests -a "integration" --nocapture`

*Important:* To run those tests under Linux or Cygwin, replace the double
quotes (") with single quotes (').

# Build

To create a <launcher_name>.exe executable do the following:

##### Automatically
Make sure the config\config.py file is populated. Copy config_sample.py and modify its values otherwise.
Execute the file ```build.bat```.
The script will first run tests and then create the executable if the tests pass.

##### Manually
From the project root
execute:

`python <path/to/python>\Python27\Scripts\pyinstaller-script.py launcher.spec`

If necessary execute the following command to
rebuild the spec file. A newly spec file will not work, see kivy packaging wiki:

`pyinstaller --name <launcher name> --onefile src\launcher.py`

However, this should normally not be required as the spec file should already be present.
