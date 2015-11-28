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

from __future__ import unicode_literals

import mockfs
import os
import unittest

from nose.plugins.attrib import attr
from sync import integrity

BASE_DIR = 'c:\\base'
TOP_DIR = 'top_dir'


class IntegrityTest(unittest.TestCase):

    def _add_file(self, rel_path, top_dir=TOP_DIR, base_dir=BASE_DIR,
                  physical=True, inTorrent=True):

        # Allow passing more than one file to add
        if isinstance(rel_path, basestring):
            rel_path = [rel_path]

        for f in rel_path:
            physical_path = os.path.join(base_dir, top_dir, f)

            # Create "real" file on "disk"
            if physical:
                self.fs.add_entries({physical_path: ""})

            # Add to torrent internal data
            if inTorrent:
                if physical:
                    self.physical_files_expected.add(physical_path)

                self.file_paths.add(os.path.join(top_dir, f))

    def _add_real_file_only(self, rel_path, top_dir=TOP_DIR, base_dir=BASE_DIR):
        return self._add_file(rel_path, top_dir, base_dir, True, False)

    def _add_torrent_file_only(self, rel_path, top_dir=TOP_DIR, base_dir=BASE_DIR):
        return self._add_file(rel_path, top_dir, base_dir, False, True)

    def _set_basic_files(self):
        self._add_file('dir1\\file11')
        self._add_file('dir1\\file12')
        self._add_file('dir2\\file21')
        self._add_file('dir2\\file22')

    def setUp(self):
        self.physical_files_expected = set([])
        self.file_paths = set([])

        self.fs = mockfs.replace_builtins()
        self._set_basic_files()

    def tearDown(self):
        self.checkIfDirContains(BASE_DIR, self.physical_files_expected)
        mockfs.restore_builtins()

    def checkIfDirContains(self, dirpath, files):
        for f in files:
            self.assertTrue(os.path.exists(f), "File does not exist, but should: {}".format(f))

        for (dirpath, _, filenames) in os.walk(dirpath):
            for f in filenames:
                full_f = os.path.join(dirpath, f)
                # print "checkIfDirContains: {}".format(full_f)
                self.assertIn(full_f, files, "Superfluous file: {}".format(full_f))

    @attr('integration')
    def test_check_mod_directories_synced(self):
        top_dirs, dirs_orig, file_paths = integrity.parse_files_list(self.file_paths)
        retval = integrity.check_mod_directories((top_dirs, dirs_orig, file_paths),
                                                 BASE_DIR, check_subdir='', on_superfluous='ignore')

        self.assertEqual(retval, True, "retval should be true")

    @attr('integration')
    def test_check_mod_directories_too_much(self):
        self._add_real_file_only('dir1\\file6')
        top_dirs, dirs_orig, file_paths = integrity.parse_files_list(self.file_paths)
        retval = integrity.check_mod_directories((top_dirs, dirs_orig, file_paths),
                                                 BASE_DIR, check_subdir='', on_superfluous='remove')

        self.assertEqual(retval, True, "retval should be true")

    @attr('integration')
    def test_check_mod_directories_not_enough(self):
        self._add_torrent_file_only('dir1\\file7')
        top_dirs, dirs_orig, file_paths = integrity.parse_files_list(self.file_paths)
        retval = integrity.check_mod_directories((top_dirs, dirs_orig, file_paths),
                                                 BASE_DIR, check_subdir='', on_superfluous='ignore')

        self.assertEqual(retval, False, "retval should be false")
