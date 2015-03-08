# import Windows registry package while ensuring cygwin compatibility
try:
    import cygwinreg as _winreg
    WindowsErrorPortable = _winreg.WindowsError
except ImportError:
    import _winreg
    WindowsErrorPortable = WindowsError

import os
import sys

# Allow relative imports when the script is run from the command line
if __name__ == "__main__":
    sys.path.append(os.path.dirname(sys.path[0]))

from utils.singleton import Singleton


# Exceptions:
class ArmaNotInstalled(Exception):
    pass


class Arma(object):
    __metaclass__ = Singleton
    __custom_path = None

    # Registry paths
    _arma_registry_path = r"software\bohemia interactive\arma 3"
    _arma_expansions_registry_path = r"software\bohemia interactive\arma 3\expansions\arma 3"

    @staticmethod
    def get_user_path():
        """Returns the place where mods can be installed in the user folder."""
        return os.path.expanduser('~')

    @staticmethod
    def get_custom_path():
        """Returns a custom mod installation path set by the user.
        If no path has been set beforehand, returns None"""
        return Arma().__custom_path

    @staticmethod
    def set_custom_path(new_path):
        """Set a custom mod installation path.
        Note: The function does NOT convert the path to an absolute path."""
        Arma().__custom_path = new_path

    @staticmethod
    def get_installation_path():
        """Returns the folder where Arma is installed.
        Raises ArmaNotInstalled if the required registry keys cannot be found."""

        path = None
        try:
            key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, Arma._arma_registry_path, 0, _winreg.KEY_READ | _winreg.KEY_WOW64_32KEY)
            (path, valuetype) = _winreg.QueryValueEx(key, 'main')
            key.Close()
        except WindowsErrorPortable:
            raise ArmaNotInstalled()

        return path

    @staticmethod
    def get_executable_path():
        """Returns path to the arma executable.
        Raises ArmaNotInstalled if Arma is not installed."""
        return os.path.join(Arma.get_installation_path(), "arma3.exe")

    @staticmethod
    def run_game(modlist, profile):
        """Run the game in a separate process.
        All mods in modlist are applied as command line parameters. The profile is also used.
        Raises ArmaNotInstalled if Arma is not installed."""

        pass  # Stub

if __name__ == "__main__":
    a = Arma()
    b = Arma()
    c = Arma()
    Arma.set_custom_path("asd")
    print a.get_custom_path()
    print b.get_custom_path()
    print c.get_custom_path()
    print Arma.get_custom_path()

    b.set_custom_path("bsd")
    print a.get_custom_path()
    print b.get_custom_path()
    print c.get_custom_path()
    print Arma.get_custom_path()


    #print Arma.get_executable_path()
    pass
