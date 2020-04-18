# Create your own launcher

See the extensive [documentation on the wiki](https://github.com/overfl0/Bulletproof-Arma-Launcher/wiki/Launcher-management) for a step by step guide.
The wiki is updated much more often than this readme file.

# Disclaimer

The launcher requires you to have both Steam and Arma correctly installed and
will not work if it can't find them. That means that it will **not** work with
cracked Arma versions.
Do not ask me to help you with this.

# Installation

First, make sure you have Python 2.7 installed (yes, work to porting to Python
3 is under way, feel free to reach out, to help with that).

Then install a virtualenv (preferably [virtualenvwrapper](https://pypi.org/project/virtualenvwrapper-win/))
to contain all the dependencies in one place. The instructions below assume
you've installed virtualenvwrapper.

Create the a Python 2.7 virtualenv once and install the requirements:
```
mkvirtualenv bulletproof -p c:\Python27\python.exe
workon bulletproof
cd YourLauncherDirectory
pip install -r requirements.txt
```

# Running

Remember to always select the `bulletproof` virtualenv, before doing anything
else, after opening a command prompt. You do that by calling:
```
workon bulletproof
```

Then:
```
python src\launcher.py
```

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

Make sure the config\config.py file is populated. Copy config_sample.py and
modify its values otherwise.
Execute the file ```build.bat``` (after selecting the virtualenv, as usual).
The script will first run tests and then create the executable if the tests
pass.

##### Manually

From the project root
execute:

`python <path/to/python>\Python27\Scripts\pyinstaller-script.py launcher.spec`

If necessary execute the following command to
rebuild the spec file. A newly spec file will not work, see kivy packaging wiki:

`pyinstaller --name <launcher name> --onefile src\launcher.py`

However, this should normally not be required as the spec file should already be present.
