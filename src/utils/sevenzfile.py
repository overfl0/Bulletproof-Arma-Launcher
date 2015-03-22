# Tactical Battlefield Installer/Updater/Launcher
# Copyright (C) 2015 TacBF Installer Team.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

import os

import py7zlib

class SevenZFile(object):
    _fd = None
    _file_path = None
    _archive = None

    @classmethod
    def is_7zfile(cls, filepath):
        '''
        Class method: determine if file path points to a valid 7z archive.
        '''
        is7z = False
        fp = None
        try:
            fp = open(filepath, 'rb')
            archive = py7zlib.Archive7z(fp)
            n = len(archive.getnames())
            is7z = True
        finally:
            if fp:
                fp.close()
        return is7z

    def __init__(self, filepath):
        self._file_path = filepath

    def __enter__(self):
        self._fd = open(self._file_path, 'rb')
        self._archive = py7zlib.Archive7z(self._fd)
        return self

    def __exit__(self, type, value, traceback):
        if self._fd:
            self._fd.close()

    def extractall(self, path):
        for name in self._archive.getnames():
            outfilename = os.path.join(path, name)
            outdir = os.path.dirname(outfilename)
            if not os.path.exists(outdir):
                os.makedirs(outdir)
            outfile = open(outfilename, 'wb')
            outfile.write(self._archive.getmember(name).read())
            outfile.close()
