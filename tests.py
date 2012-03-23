import unittest
import os

import blast
TMP_FILE = '__test_tempfile'
blast.Store.DB_PATH = TMP_FILE

class TestStore(unittest.TestCase):
    def setUp(self):
        self.store = blast.Store().__enter__()

    def test_dict(self):
        store = self.store

        n = 42
        store['a'] = n
        self.assertEqual(store['a'], n)

        s = 'A string with russian словами'
        store['b'] = s
        self.assertEqual(store['b'], s)

        v = [1, 2, None, 'Bacon', {42, 666}, ('Tuples!', ('Of Tuples!', 'of size 2'))]
        store['c'] = v
        self.assertEqual(store['c'], v)

    def test_iter(self):
        store = self.store

        store['a'] = 1
        store['b'] = 0
        self.assertEqual(len(store), 2)

        del store['a']
        del store['b']
        self.assertEqual(len(store), 0)

        store['c'] = 42
        self.assertTrue('c' in store)

        del store['c']
        self.assertTrue('c' not in store)

        store['k1'] = 0
        store['k2'] = 0
        store['k3'] = 0
        self.assertEqual(set(store), {'k1', 'k2', 'k3'})

        del store['k1']
        del store['k2']
        del store['k3']
        self.assertEqual(set(store), set())

    def tearDown(self):
        self.store.__exit__(None, None, None)
        os.remove(TMP_FILE)
