# Bulletproof Arma Launcher
# Copyright (C) 2017 Lukasz Taczuk
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.


from __future__ import unicode_literals


import ast
import sys

# from PyInstaller.archive.readers import CArchiveReader
from external.pyinstxtractor import extract_file


VERSION_LOCATION = 'src\\launcher_config\\version.py'


class PypeekerException(Exception):
    pass

'''
def get_file_from_pyinstaller_exe(name, file_name):
    """Retrieves a file packed into an exe built by PyInstaller.
    Returns the file contents or None if the file was not found.
    """

    try:
        archive = CArchiveReader(name)
    except IOError as ex:
        if ex.errno == 2:  # No such file or directory
            raise PypeekerException('Could not find the exectuable on disk!')

        raise

    location = archive.toc.find(file_name)
    if location == -1:
        raise PypeekerException('No file inside the executable: '.format(file_name))

    extract_value = archive.extract(location)
    if extract_value is None:
        return extract_value

    _, contents = extract_value  # ispkg, contents
    return contents
'''

def get_version(name, location=VERSION_LOCATION):
    """Get the version.py of the launcher stored in location.
    If used with a custom location right now, the location
    """

    # contents = get_file_from_pyinstaller_exe(name, location)
    contents = extract_file(name, location)
    if contents is None:
        raise PypeekerException('Could not retrieve version file from the executable!')

    tree = ast.parse(contents)

    # Find the version information
    for elem in tree.body:
        # Do safety checks
        if not isinstance(elem, ast.Assign):
            continue

        if len(elem.targets) != 1:
            continue

        if elem.targets[0].id != 'version':
            continue

        return elem.value.s

    raise PypeekerException('Version variable not found in the version file!')

if __name__ == '__main__':
    print get_version(sys.argv[1])
