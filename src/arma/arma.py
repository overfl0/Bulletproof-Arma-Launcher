import os
try:
    import cygwinreg as _winreg  # Cygwin compatibility
    WindowsErrorPortable = _winreg.WindowsError
except ImportError:
    import _winreg
    WindowsErrorPortable = WindowsError


class ArmaNotInstalled(Exception):
    pass


class Arma:

    # Registry paths
    _arma_registry_path = "software\\bohemia interactive\\arma 3"
    _arma_expansions_registry_path = "software\\bohemia interactive\\arma 3\\expansions\\arma 3"

    @staticmethod
    def get_user_path():
        """Returns the place where mods can be installed in the user folder."""
        return os.path.expanduser('~')  # TODO: Check me when run as administrator

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
    print Arma.get_installation_path()
    print Arma.get_executable_path()
