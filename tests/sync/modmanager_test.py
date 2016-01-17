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

import unittest
import time
import os
import shutil

from nose.plugins.attrib import attr

from sync.modmanager import ModManager
from sync.mod import Mod
from sync.httpsyncer import HttpSyncer

class ModManagerTest(unittest.TestCase):

    def setUp(self):
        pass

    def test_modmanager_should_be_createable(self):
        m = ModManager()
        self.assertIsNotNone(m)

    def test_should_return_the_right_syncer_class(self):
        m = ModManager()

        self.assertIsNone(m._get_syncer('skdjhskf'))

        cls = m._get_syncer('http')
        self.assertEqual(cls, HttpSyncer)

    @attr('integration')
    def _test_sync_zipped_mod(self):
        m = ModManager()
        self.assertIsNotNone(m)

        # construct mod
        mod = Mod(
            name='@CBA_A3',
            clientlocation='../tests/',
            synctype='http',
            downloadurl='http://dev.withsix.com/attachments/download/22231/CBA_A3_RC4.7z');

        m._sync_single_mod(mod)

        count = 0

        while True:
            time.sleep(1)
            stat = m.query_status()

            if stat == None:
                continue

            if stat['status'] == 'downloading':
                continue

            if stat['status'] == 'finished':
                break

            if count > 3:
                self.assertEqual('finished', stat['status'])
                break

        self.assertTrue(os.path.isdir('../tests/@CBA_A3'))

        shutil.rmtree('../tests/@CBA_A3')
