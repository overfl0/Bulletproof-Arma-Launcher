# import Windows registry package while ensuring cygwin compatibility
import platform
import sys

if platform.system() is not 'Linux':
    # Regular Windows version
    try:
        import cygwinreg as _winreg
        WindowsError = _winreg.WindowsError
        KEY_WOW64_32KEY = 0x200  # Cygwin, you sucker!

    except ImportError:
        import _winreg
        WindowsError = WindowsError
        KEY_WOW64_32KEY = _winreg.KEY_WOW64_32KEY


    class Registry(object):
        Error = WindowsError

        @staticmethod
        def ReadValue(super_key_handle, key_path, value_name, force_32bit=True):
            """Read the value value_name from the key key_path from Local Machine in the Registry.

            super_key_handle is an already open registry key or a predefined one (like HKEY_LOCAL_MACHINE).
            If force_32bit is set, it will force 32bit view of the registry."""

            flags = _winreg.KEY_READ
            if force_32bit:
                flags = flags | KEY_WOW64_32KEY

            key = _winreg.OpenKey(super_key_handle, key_path, 0, flags)
            (value, valuetype) = _winreg.QueryValueEx(key, value_name)
            key.Close()

            return value

        @staticmethod
        def ReadValueMachine(key_path, value_name, force_32bit=True):
            """Read the value value_name from the key key_path from Local Machine in the Registry.

            If force_32bit is set, it will force 32bit view of the registry."""

            return Registry.ReadValue(_winreg.HKEY_LOCAL_MACHINE, key_path, value_name, force_32bit)

else:  # Linux dummy implementation. Works ONLY inside unit tests!

    # Don't allow the use of this module on linux outside of unit tests
    if "unittest" not in sys.modules.keys():
        raise Exception("Registry not implemented on Linux. Dummy class for unit tests only!")

    # Dummy class with fake methods
    class Registry(object):
        Error = Exception

        @staticmethod
        def ReadValue(super_key_handle, key_path, value_name, force_32bit=True):
            return '/tmp'

        @staticmethod
        def ReadValueMachine(key_path, value_name, force_32bit=True):
            return '/tmp'
