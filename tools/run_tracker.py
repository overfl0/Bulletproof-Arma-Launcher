#!/usr/bin/env python

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

# These are small hacks to just use the tracker out of the box
# without the need to install anything


import os
import site
import sys

file_directory = os.path.dirname(os.path.realpath(__file__))
pytt_directory = os.path.join(file_directory, 'Pytt')
# Allow relative imports when the script is run from the command line
site.addsitedir(os.path.abspath(pytt_directory))


def quiet_unlink_files(directory, filenames):
    for filename in filenames:
        try:
            os.unlink(os.path.join(directory, filename))
        except Exception:
            pass

# make sure tornado package is installed
try:
    import tornado
except Exception:
    print "This tracker requires tornado to be installed"
    print "You can install it by issuing the command:"
    print "pip install tornado"
    sys.exit(1)

# increase MAX_ALLOWED_PEERS because 55 yielded errors with common BitTorrent clients
import pytt.utils
pytt.utils.MAX_ALLOWED_PEERS = 1000

# Run the tracker
import pytt.tracker

print "For additional commandline switches, run {} -h".format(sys.argv[0])
try:
    pytt.tracker.start_tracker()
finally:
    # Remove the files after usage. Dumb but it gets the job done and the submodule does not appear "dirty"
    quiet_unlink_files(os.path.join(pytt_directory, "pytt"), ("bencode.pyc", "tracker.pyc", "utils.pyc", "__init__.pyc"))
