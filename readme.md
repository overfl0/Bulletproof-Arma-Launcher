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

## Getting a prebuilt Libtorrent dependency

Because libtorrent doesn't provide python modules anymore (the last one
available on Github is libtorrent-1.0.9 for Python 2.7) you have to build the
libtorrent-python library yourself or get a prebuilt version build by someone.
You can also ask the main libtorrent developer if he could start providing the
python binaries again, on the libtorrent mailing list :)

You can get a [prebuilt libtorrent.pyd file for Python 3.7 32bit](https://github.com/overfl0/Bulletproof-Arma-Launcher/releases/download/1.15.2/libtorrent.pyd).
Put it into your virtualenv, to the `Lib/site-packages` directory.

## Building the Libtorrent dependency

Because libtorrent doesn't provide python modules anymore (the last one
available on Github is libtorrent-1.0.9 for Python 2.7) you have to build the
libtorrent-python library yourself.
You can also ask the main libtorrent developer if he could start providing the
python binaries again, on the libtorrent mailing list :)

The steps are based on [this outdated documentation page](https://www.libtorrent.org/python_binding.html)
and are as follows: (assuming you want to build libtorrent with Boost v1.71.0)

1. Install the [32bit version of Python 3.7](https://www.python.org/ftp/python/3.7.6/python-3.7.6.exe)
   to `C:\Python37` (this will then match AppVeyor setup).
2. Download and install [Visual C++ 2015 Build Tools](https://go.microsoft.com/fwlink/?LinkId=691126).
   Mind you: You do NOT want _Microsoft Build Tools 2015_, this is a different
   package!
3. Download [Boost libraries](https://dl.bintray.com/boostorg/release/1.71.0/source/boost_1_71_0.zip).
   Extract them to c:/Libraries/boost_1_71_0
4. Run a _Visual C++ 2015 x86 Native Build Tools Command Prompt_ (Start menu).
   You should be able to call `cl.exe` without getting a "Command not found"
   error.
5. Create these environmental vars:
    ```
    set BOOST_BUILD_PATH=c:/Libraries/boost_1_71_0/tools/build/
    set BOOST_ROOT=c:/Libraries/boost_1_71_0/
    ```
6. Go to the BOOST_ROOT directory
    ```
    cd %BOOST_ROOT%
    ```
7. Execute `bootstrap.bat`
8. Add the directory with the newly generated b2.exe binary to the path
    ```
    set PATH=c:/Libraries/boost_1_71_0/tools/build/src/engine/;%PATH%
    ```
9. Move the file user-config.jam from `%BOOST_BUILD_PATH%/example/` to
   `%BOOST_BUILD_PATH%/user-config.jam` and add this at the end:
    ```
    using msvc : 14.0 : : /std:c++11 ;
    using python : 3.7 : C:/Python37 : C:/Python37/include : C:/Python37/libs ;
    ```
10. Download the latest [libtorrent release from Github](https://github.com/arvidn/libtorrent/releases)
11. Unpack it, go to the `bindings/python` (in that Build Tools command prompt)
    and execute:
    ```
    C:\Python37\python.exe setup.py build --bjam
    ```
12. Copy the resulting `libtorrent.pyd` file from `build/lib/` to your
    virtualenv, to `Lib\site-packages`

## Building the launcher

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
