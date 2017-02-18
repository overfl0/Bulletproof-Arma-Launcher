# -*- coding: utf-8 -*-
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

import hashlib
import mockfs
import os
import unittest

from nose.plugins.attrib import attr
from sync import integrity
from utils import walker

BASE_DIR = 'c:\\base'
TOP_DIR = 'top_dir'
DIRECTORY = {}

'''This test makes use of a modified mockfs, a library to mock a file system.
The modification allows mockfs to work on windows file paths.
The file system is populated with files, so is the "torrent" structure.
Then the function check_mod_directories() is ran. Its purpose is to remove
superfluous files from the file system and report whether all the files required
from the "torrent" are in fact on the disk.

At the end of each test, _check_if_dir_contains_only() checks if the required
files and directories are still on disk (no berserk removal) and if all files
contained in a given directory are in fact listed in the torrent (no superfluous
files on disk).
'''


class IntegrityTest(unittest.TestCase):

    def setUp(self):
        self.physical_files_expected = set([])
        self.physical_dirs_expected = set([])
        self.file_paths = set([])

        self.fs = mockfs.replace_builtins()
        self._set_basic_files()

    def tearDown(self):
        self._check_if_dir_contains_only(BASE_DIR, self.physical_dirs_expected, self.physical_files_expected)
        mockfs.restore_builtins()

    def _add_file(self, rel_path, top_dir=TOP_DIR, base_dir=BASE_DIR,
                  physical=True, in_torrent=True, force_keep_it=False, content=''):
        '''Add the file/dir to mockfs. Also add it to the appropriate internal "set".'''

        # Allow passing more than one file to add
        if isinstance(rel_path, basestring):
            rel_path = [rel_path]

        for f in rel_path:
            physical_path = os.path.join(base_dir, top_dir, f)

            # Create "real" file on "disk"
            if physical:
                self.fs.add_entries({physical_path: content})

                if in_torrent or force_keep_it:
                    if content != DIRECTORY:
                        self.physical_files_expected.add(physical_path)
                        directory = os.path.dirname(physical_path)
                    else:
                        directory = physical_path

                    while directory != base_dir:
                        self.physical_dirs_expected.add(directory)
                        directory = os.path.dirname(directory)

            # Add to torrent internal data
            if in_torrent:
                self.file_paths.add(os.path.join(top_dir, f))

    def _add_real_file_only(self, rel_path, top_dir=TOP_DIR, base_dir=BASE_DIR, force_keep_it=False, content=''):
        return self._add_file(rel_path, top_dir, base_dir, physical=True, in_torrent=False, force_keep_it=force_keep_it, content=content)

    def _add_torrent_file_only(self, rel_path, top_dir=TOP_DIR, base_dir=BASE_DIR, content=''):
        return self._add_file(rel_path, top_dir, base_dir, physical=False, in_torrent=True, content=content)

    def _set_basic_files(self):
        '''Add some dummy files so that the tests actually have to do something.'''
        self._add_file('dir1\\file11')
        self._add_file('dir1\\file12')
        self._add_file('dir2\\file21')
        self._add_file('dir2\\file22')

        self.basic_checksums = {
            TOP_DIR + '\\dir1\\file11': hashlib.sha1('').digest(),
            TOP_DIR + '\\dir1\\file12': hashlib.sha1('').digest(),
            TOP_DIR + '\\dir2\\file21': hashlib.sha1('').digest(),
            TOP_DIR + '\\dir2\\file22': hashlib.sha1('').digest(),
        }

    def _check_if_dir_contains_only(self, dirpath, dirs, files):
        '''Make sure all required files are physically present on disk (no
        berserk removal). Make sure all files in directory are actually required
        (no superfluous files).
        '''

        # Are all required files really on the file system?
        for f in files:
            self.assertTrue(os.path.isfile(f), "File does not exist, but should: {}".format(f))

        for d in dirs:
            self.assertTrue(os.path.isdir(d), "Directory does not exist, but should: {}".format(d))

        # Are all files on disk required by the torrent?
        for (dirpath, dirnames, filenames) in walker.walk(dirpath):
            for f in filenames:
                full_f = os.path.join(dirpath, f)
                # print "_check_if_dir_contains_only: {}".format(full_f)
                self.assertIn(full_f, files, "Superfluous file: {}".format(full_f))

            for d in dirnames:
                full_d = os.path.join(dirpath, d)
                self.assertIn(full_d, dirs, "Superfluous directory: {}".format(full_d))

    ############################################################################
    # Actual tests start here                                                  #
    ############################################################################

    @attr('integration')
    def test_sync_already_synced(self):
        retval = integrity.check_mod_directories(self.file_paths,
                                                 BASE_DIR, check_subdir='', on_superfluous='remove')

        self.assertEqual(retval, True, "check_mod_directories should return true")

    @attr('integration')
    def test_sync_superfluous_entries_so_remove(self):
        self._add_real_file_only('dir1\\file6')
        self._add_real_file_only('dir1\\dir6', content=DIRECTORY)
        self._add_real_file_only('dir1\\żółw')
        self._add_real_file_only('żółw\\dir6', content=DIRECTORY)
        self.assertTrue(os.path.isdir(os.path.join(BASE_DIR, TOP_DIR, 'dir1\\dir6')), 'File is not a dir!')
        self.assertTrue(os.path.isdir(os.path.join(BASE_DIR, TOP_DIR, 'żółw\\dir6')), 'File is not a dir!')

        retval = integrity.check_mod_directories(self.file_paths,
                                                 BASE_DIR, check_subdir='', on_superfluous='remove')

        self.assertEqual(retval, True, "check_mod_directories should return true")

    @attr('integration')
    def test_sync_superfluous_entries_but_ignore(self):
        self._add_real_file_only('dir1\\file6', force_keep_it=True)
        self._add_real_file_only('dir1\\dir6', force_keep_it=True, content=DIRECTORY)
        self._add_real_file_only('dir1\\żółw', force_keep_it=True)
        self._add_real_file_only('żółw\\dir6', force_keep_it=True, content=DIRECTORY)
        self.assertTrue(os.path.isdir(os.path.join(BASE_DIR, TOP_DIR, 'dir1\\dir6')), 'File is not a dir!')
        self.assertTrue(os.path.isdir(os.path.join(BASE_DIR, TOP_DIR, 'żółw\\dir6')), 'File is not a dir!')

        retval = integrity.check_mod_directories(self.file_paths,
                                                 BASE_DIR, check_subdir='', on_superfluous='ignore')

        self.assertEqual(retval, True, "check_mod_directories should return true")

    @attr('integration')
    def test_sync_superfluous_file_on_warn(self):
        self._add_real_file_only('dir1\\file6', force_keep_it=True)
        # self._add_real_file_only('dir1\\dir6', force_keep_it=True, content=DIRECTORY)
        # self.assertTrue(os.path.isdir(os.path.join(BASE_DIR, TOP_DIR, 'dir1\\dir6')), 'File is not a dir!')

        retval = integrity.check_mod_directories(self.file_paths,
                                                 BASE_DIR, check_subdir='', on_superfluous='warn')

        self.assertEqual(retval, False, "check_mod_directories should return false")

    @attr('integration')
    def test_sync_superfluous_dir_on_warn(self):
        self._add_real_file_only('dir1\\dir6', force_keep_it=True, content=DIRECTORY)
        self.assertTrue(os.path.isdir(os.path.join(BASE_DIR, TOP_DIR, 'dir1\\dir6')), 'File is not a dir!')

        retval = integrity.check_mod_directories(self.file_paths,
                                                 BASE_DIR, check_subdir='', on_superfluous='warn')

        self.assertEqual(retval, False, "check_mod_directories should return false")

    @attr('integration')
    def test_sync_missing_file(self):
        self._add_torrent_file_only('dir1\\file7')
        retval = integrity.check_mod_directories(self.file_paths,
                                                 BASE_DIR, check_subdir='', on_superfluous='ignore')

        self.assertEqual(retval, False, "check_mod_directories should return false")

    @attr('integration')
    def test_sync_missing_unicode_file(self):
        self._add_torrent_file_only('dir1\\żółw')
        retval = integrity.check_mod_directories(self.file_paths,
                                                 BASE_DIR, check_subdir='', on_superfluous='ignore')

        self.assertEqual(retval, False, "check_mod_directories should return false")

    @attr('integration')
    def _test_sync_missing_dir(self):
        '''Test invalid because checking empty dirs from torrents not yet implemented.'''
        self._add_torrent_file_only('dir1\\dir6', content=DIRECTORY)

        retval = integrity.check_mod_directories(self.file_paths,
                                                 BASE_DIR, check_subdir='', on_superfluous='ignore')

        self.assertEqual(retval, False, "check_mod_directories should return true")

    @attr('integration')
    def test_sync_entries_in_other_top_dirs(self):
        self._add_real_file_only('dir1\\file6', top_dir='other', force_keep_it=True)
        self._add_real_file_only('dir2\\file1', top_dir='other', force_keep_it=True)
        self._add_real_file_only('dir2\\dire1', top_dir='other2', force_keep_it=True, content=DIRECTORY)
        self._add_real_file_only('somefile', top_dir='', base_dir='c:\\', force_keep_it=True)
        self._add_real_file_only('otherfile', top_dir='', base_dir=BASE_DIR, force_keep_it=True)

        retval = integrity.check_mod_directories(self.file_paths,
                                                 BASE_DIR, check_subdir='', on_superfluous='remove')

        self.assertEqual(retval, True, "check_mod_directories should return true")

    @attr('integration')
    def test_sync_keep_whitelisted_physical_entries(self):
        self._add_real_file_only('dir1\\tfr.ts3_plugin', force_keep_it=True)
        self._add_real_file_only('dir1\\will_be_removed')
        self._add_real_file_only('tfr.ts3_plugin\\somefile', force_keep_it=True)
        self._add_real_file_only('tfr.ts3_plugin\\otherfile', force_keep_it=True)
        self._add_real_file_only('.synqinfo\\file1', force_keep_it=True)
        self._add_real_file_only('.synqinfo\\file2', force_keep_it=True)

        retval = integrity.check_mod_directories(self.file_paths,
                                                 BASE_DIR, check_subdir='', on_superfluous='remove')

        self.assertEqual(retval, True, "check_mod_directories should return true")

    @attr('integration')
    def test_sync_keep_whitelisted_physical_entries_on_warn(self):
        self._add_real_file_only('dir1\\tfr.ts3_plugin', force_keep_it=True)
        self._add_real_file_only('tfr.ts3_plugin\\somefile', force_keep_it=True)
        self._add_real_file_only('tfr.ts3_plugin\\otherfile', force_keep_it=True)
        self._add_real_file_only('.synqinfo\\file1', force_keep_it=True)
        self._add_real_file_only('.synqinfo\\file2', force_keep_it=True)

        retval = integrity.check_mod_directories(self.file_paths,
                                                 BASE_DIR, check_subdir='', on_superfluous='warn')

        self.assertEqual(retval, True, "check_mod_directories should return true")

    @attr('integration')
    def test_sync_whitelisted_entries_from_torrent_removed(self):
        self._add_torrent_file_only('dir1\\tfr.ts3_plugin')
        self._add_torrent_file_only('tfr.ts3_plugin\\somefile')
        self._add_torrent_file_only('tfr.ts3_plugin\\otherfile')
        self._add_torrent_file_only('.synqinfo\\file1')
        self._add_torrent_file_only('.synqinfo\\file2')

        retval = integrity.check_mod_directories(self.file_paths,
                                                 BASE_DIR, check_subdir='', on_superfluous='remove')

        self.assertEqual(retval, True, "check_mod_directories should return true")

    @attr('integration')
    def test_sync_unicode(self):
        self._add_file('test\\żółw')
        retval = integrity.check_mod_directories(self.file_paths,
                                                 BASE_DIR, check_subdir='', on_superfluous='remove')

        self.assertEqual(retval, True, "check_mod_directories should return true")

    def _set_basic_subdir_files(self):
        self._add_file('ts\\plugins\\tsfile1')
        self._add_file('ts\\plugins\\tsfile2')
        self._add_file('ts\\plugins\\tsdir1\\tsfile3')

        # c:\\teamspeak\\plugins\\tsfileX
        self._add_real_file_only('tsfile1', 'plugins', 'c:\\teamspeak', force_keep_it=True)
        self._add_real_file_only('tsfile2', 'plugins', 'c:\\teamspeak', force_keep_it=True)
        self._add_real_file_only('tsdir1\\tsfile3', 'plugins', 'c:\\teamspeak', force_keep_it=True)

        # Irrelevant files. They MUST be kept and NOT removed!
        self._add_real_file_only('somePlugin\\pluginFile', 'plugins', 'c:\\teamspeak', force_keep_it=True)
        self._add_real_file_only('otherPluginFile', 'plugins', 'c:\\teamspeak', force_keep_it=True)
        self._add_real_file_only('tsInternalFile', '', 'c:\\teamspeak', force_keep_it=True)
        self._add_real_file_only('passer-byFile', '', 'c:\\', force_keep_it=True)
        self._add_real_file_only('passer-byDir\\somefile', '', 'c:\\', force_keep_it=True)

    @attr('integration')
    def test_sync_subdir(self):
        self._set_basic_subdir_files()
        retval = integrity.check_mod_directories(self.file_paths,
                                                 base_directory='c:\\teamspeak\\plugins',
                                                 check_subdir='top_dir\\ts\\plugins',
                                                 on_superfluous='warn')

        self.assertEqual(retval, True, "check_mod_directories should return true")

    @attr('integration')
    def test_sync_subdir_missing(self):
        self._set_basic_subdir_files()
        self._add_file('ts\\plugins\\tsdir1\\tsfile4')
        retval = integrity.check_mod_directories(self.file_paths,
                                                 base_directory='c:\\teamspeak\\plugins',
                                                 check_subdir='top_dir\\ts\\plugins',
                                                 on_superfluous='warn')

        self.assertEqual(retval, False, "check_mod_directories should return false")

    @attr('integration')
    def test_sync_nocase(self):
        self._set_basic_subdir_files()

        self._add_torrent_file_only('dir1\\case1')
        self._add_real_file_only('dir1\\Case1', force_keep_it=True)
        self._add_torrent_file_only('dir1\\Case2')
        self._add_real_file_only('dir1\\case2', force_keep_it=True)

        self._add_torrent_file_only('dir3\\case3')
        self._add_real_file_only('Dir3\\Case3', force_keep_it=True)
        self._add_torrent_file_only('Dir4\\case4')
        self._add_real_file_only('dir4\\Case4', force_keep_it=True)

        self._add_torrent_file_only('dir5\\subdir1\\case5')
        self._add_real_file_only('Dir5\\Subdir1\\Case5', force_keep_it=True)
        self._add_torrent_file_only('Dir6\\Subdir2\\case6')
        self._add_real_file_only('dir6\\subdir2\\Case6', force_keep_it=True)

        retval = integrity.check_mod_directories(self.file_paths,
                                                 BASE_DIR, check_subdir='', on_superfluous='remove')

        self.assertEqual(retval, True, "check_mod_directories should return true")

    @attr('integration')
    def test_sync_nocase_with_checksums_ok(self):
        # self._set_basic_subdir_files()
        checksums = self.basic_checksums.copy()

        self._add_torrent_file_only('dir1\\case1')
        self._add_real_file_only('dir1\\Case1', force_keep_it=True, content='tralala')
        checksums[TOP_DIR + '\\dir1\\case1'] = hashlib.sha1('tralala').digest()

        self._add_torrent_file_only('dir1\\Case2')
        self._add_real_file_only('dir1\\case2', force_keep_it=True, content='tralala2')
        checksums[TOP_DIR + '\\dir1\\Case2'] = hashlib.sha1('tralala2').digest()

        self._add_torrent_file_only('dir5\\subdir1\\case5')
        self._add_real_file_only('Dir5\\Subdir1\\Case5', force_keep_it=True, content='tralala3')
        checksums[TOP_DIR + '\\dir5\\subdir1\\case5'] = hashlib.sha1('tralala3').digest()

        self._add_torrent_file_only('Dir6\\Subdir2\\case6')
        self._add_real_file_only('dir6\\subdir2\\Case6', force_keep_it=True, content='tralala4')
        checksums[TOP_DIR + '\\Dir6\\Subdir2\\case6'] = hashlib.sha1('tralala4').digest()

        retval = integrity.check_mod_directories(self.file_paths,
                                                 BASE_DIR, check_subdir='', on_superfluous='remove',
                                                 checksums=checksums)

        self.assertEqual(retval, True, "check_mod_directories should return true")

    @attr('integration')
    def test_sync_nocase_with_checksums_not_ok1(self):
        # self._set_basic_subdir_files()
        checksums = self.basic_checksums.copy()

        self._add_torrent_file_only('dir1\\case1')
        self._add_real_file_only('dir1\\Case1', force_keep_it=True, content='tralala')
        checksums[TOP_DIR + '\\dir1\\case1'] = hashlib.sha1('NOT tralala').digest()

        retval = integrity.check_mod_directories(self.file_paths,
                                                 BASE_DIR, check_subdir='', on_superfluous='remove',
                                                 checksums=checksums)

        self.assertEqual(retval, False, "check_mod_directories should return false")

    @attr('integration')
    def test_sync_nocase_with_checksums_not_ok2(self):
        # self._set_basic_subdir_files()
        checksums = self.basic_checksums.copy()

        self._add_torrent_file_only('dir1\\Case2')
        self._add_real_file_only('dir1\\case2', force_keep_it=True, content='tralala2')
        checksums[TOP_DIR + '\\dir1\\Case2'] = hashlib.sha1('NOT tralala2').digest()

        retval = integrity.check_mod_directories(self.file_paths,
                                                 BASE_DIR, check_subdir='', on_superfluous='remove',
                                                 checksums=checksums)

        self.assertEqual(retval, False, "check_mod_directories should return false")

# TODO: fix torrent empty directory check both in normal and in subdir check
