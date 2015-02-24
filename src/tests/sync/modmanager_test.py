import unittest

from sync.modmanager import ModManager
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
