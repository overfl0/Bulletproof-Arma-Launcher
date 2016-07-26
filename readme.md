# Install

Manually installing the environment is now quite tricky as it involves, among other things, getting the right version of Kivy (1.9.1) and patching it with our own custom patches ([located in the Patches directory](https://bitbucket.org/tacbf_launcher/build_environment/src/master/Patches/) of the `build_environment` repository).

We're trying to make it as easy as possible to start working on the launcher and we have created [a Vagrant configuration file that will create a virtual machine](https://bitbucket.org/tacbf_launcher/build_environment) containing everything that is needed to code right away.

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
Execute the file ```build.bat```.
The script will first run tests and then create the executable if the tests pass.

##### Manually
From the project root
execute:

`python <path/to/kivy/installation>\Python27\Scripts\pyinstaller-script.py launcher.spec`

If necessary execute the following command to
rebuild the spec file. A newly spec file will not work, see kivy packaging wiki:

`pyinstaller --name <launcher name> --onefile src\launcher.py`

However, this should normally not be required as the spec file should already be present.

# Communication

Feel free to reach the developers of the Tactical Battlefield mod and the Launcher on their respective discord channels:

* [#general](https://discordapp.com/channels/106788078437281792/106788078437281792)
* [#launcher](https://discordapp.com/channels/106788078437281792/106792735066894336)