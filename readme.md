# Install

To make the install ready for development. Go to http://kivy.org/#download
and download Kivy-1.8.0-py2.7-win32.zip. Unpack it into the project root
in its own folder. In this folder you can run kivy.bat. This fires
up a cmd prompt with every environment variables set.

You also have to install some additional packages with pip from inside the cmd:

`pip install requests futures`

# Running

cd into the src directory and run

`python launcher.py`

from inside cmd.

# Running The Tests

You have to install the nose package.
To run the Tests cd into the src dir and run,

for unit test

`nosetests ../tests -a "!integration" --nocapture`

for integration tests

`nosetests ../tests -a "integration" --nocapture`

*Important:* To run those tests under Linux or Cygwin, replace the double
quotes (") with single quotes (').

# Build

From the project root
execute:

`python <path/to/kivy/installation>\Python27\Scripts\pyinstaller-script.py tblauncher.spec`

to build a single executable

If necessary execute the following command to
rebuild the spec file. A newly spec file will not work, see kivy packaging wiki:

`pyinstaller --name tblauncher --onefile src\launcher.py`
