# Bulletproof Arma Launcher
# Copyright (C) 2016 Lukasz Taczuk
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

import sys

from critical_messagebox import MessageBox
from distutils.version import LooseVersion
from utils import paths
from utils.testtools_compat import _format_exc_info

if not paths.is_pyinstaller_bundle():
    from pkg_resources import \
        require, \
        DistributionNotFound, \
        VersionConflict

else:
    # Pyinstaller does not handle pkg_resources well. Create dummy exceptions
    # This should be safe as PyInstaller should already take care of dependencies
    class DistributionNotFound(Exception):
        pass

    class VersionConflict(Exception):
        pass

libtorrent_least_required_version = '1.0.9'
kivy_least_required_version = '1.11.1'


def strip_requirements(lines):
    output = []
    for line in lines:
        if line.strip().startswith('#'):
            continue
        if 'libtorrent' in line:
            continue
        if 'mockfs' in line:
            continue
        output.append(line)
    return output


def check_libraries_requirements():
    """Check if the required dependencies are met.
    Calling this function at the program start will allow the program to terminate
    gracefully in case of an unmet dependency instead of crashing while performing
    important tasks."""
    file_path = paths.get_base_path('requirements.txt')

    try:
        # Skip the check if we are running in a |PyInstaller| bundle. Assume everything is all right.
        if not paths.is_pyinstaller_bundle():
            with file(file_path) as req_file:
                requirements = strip_requirements(req_file.readlines())
                print('testing', requirements)
                require(requirements)

        # Libtorrent requirements
        try:
            # Workaround for libtorrent version (not available on pip so it cannot
            # be written inside requirements.txt).
            import libtorrent

            if LooseVersion(libtorrent.version) < LooseVersion(libtorrent_least_required_version):
                raise VersionConflict('libtorrent {}'.format(libtorrent.version),
                                      'libtorrent >= {}'.format(libtorrent_least_required_version))

        except ImportError:
            raise DistributionNotFound('libtorrent')

        # Kivy requirements
        try:
            import multiprocessing
            multiprocessing.freeze_support()

            import kivy

            kivy.require(kivy_least_required_version)

        except ImportError:
            raise DistributionNotFound('kivy')

        except Exception:
            # Kivy raises an Exception with a not-so-nicely formatted message
            # Just print it and exit
            msg = "".join(_format_exc_info(*sys.exc_info())) + \
                  "\nAvast DeepScreen is known to fail here."
            MessageBox(msg, 'Kivy error')
            sys.exit(1)

    except VersionConflict as ex:
        message = 'Wrong library version. Installed: {}. Required: {}'.format(ex.args[0], ex.args[1])
        MessageBox(message, 'Error')
        sys.exit(1)

    except DistributionNotFound as ex:
        message = 'Missing python library. Required: {}'.format(ex.args[0])
        MessageBox(message, 'Error')
        sys.exit(1)
