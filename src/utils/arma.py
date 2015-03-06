import os
try:
    import cygwinreg as _winreg  # Cygwin compatibility
except ImportError:
    import _winreg


class ArmaNotInstalledException(Exception):
    pass


class Arma:

    # Registry paths
    _arma_registry_path = "software\\bohemia interactive\\arma 3"
    _arma_expansions_registry_path = "software\\bohemia interactive\\arma 3\\expansions\\arma 3"

    @staticmethod
    def get_user_path():
        """Returns the place where mods can be installed in the user folder."""
        pass  # Stub

    @staticmethod
    def get_installation_path():
        """Returns the folder where Arma is installed.
        Raises ArmaNotInstalledException if the required registry keys cannot be found."""

        path = None
        try:
            key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, Arma._arma_registry_path)
            (path, valuetype) = _winreg.QueryValueEx(key, 'main')
            key.Close()
        except _winreg.WindowsError:
            raise ArmaNotInstalledException()

        return path

    @staticmethod
    def get_executable_path():
        """Returns path to the arma executable.
        Raises ArmaNotInstalledException if Arma is not installed."""
        return os.path.join(Arma.get_installation_path(), "arma3.exe")

    @staticmethod
    def run_game(modlist, profile):
        """Run the game in a separate process.
        All mods in modlist are applied as command line parameters. The profile is also used.
        Raises ArmaNotInstalledException if Arma is not installed."""

        pass  # Stub

if __name__ == "__main__":
    print Arma.get_installation_path()
    print Arma.get_executable_path()
