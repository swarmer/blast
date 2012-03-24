import unittest
import os
import sys
import io
import contextlib

import blast


TMP_FILE = '__test_tempfile'
def cleanup():
    try:
        os.remove(TMP_FILE)
    except OSError:
        pass


class TestBlast(unittest.TestCase):
    def setUp(self):
        self.blast = blast.Blast(TMP_FILE)

    def tearDown(self):
        self.blast.close()
        cleanup()

    def test_dict(self):
        blast = self.blast

        n = 42
        blast['a'] = n
        self.assertEqual(blast['a'], n)

        s = 'A string with russian словами'
        blast['b'] = s
        self.assertEqual(blast['b'], s)

        v = [1, 2, None, 'Bacon', {42, 666}, ('Tuples!', ('Of Tuples!', 'of size 2'))]
        blast['c'] = v
        self.assertEqual(blast['c'], v)

    def test_iter(self):
        blast = self.blast

        blast['a'] = 1
        blast['b'] = 0
        self.assertEqual(len(blast), 2)

        blast.clear()
        self.assertEqual(len(blast), 0)

        blast['c'] = 42
        self.assertTrue('c' in blast)

        del blast['c']
        self.assertTrue('c' not in blast)

        blast['k1'] = 0
        blast['k2'] = 0
        blast['k3'] = 0
        self.assertEqual(set(blast), {'k1', 'k2', 'k3'})

        blast.clear()
        self.assertEqual(set(blast), set())

    def test_list(self):
        blast = self.blast

        blast['a'] = 0
        blast['b'] = 0
        blast['n.a'] = 0
        blast['n.b'] = 0
        self.assertEqual(blast.get_list(), ['a', 'b', 'n.a', 'n.b'])
        self.assertEqual(blast.get_list('a'), [])
        self.assertEqual(blast.get_list('n'), ['n.a', 'n.b'])
        self.assertEqual(blast.get_list('n.b'), [])

        blast.clear()
        self.assertEqual(blast.get_list(), [])
        self.assertEqual(blast.get_list('a'), [])
        self.assertEqual(blast.get_list('a.b'), [])

    def test_clear(self):
        blast = self.blast

        blast['a'] = '0'
        blast['b'] = '0'
        blast['k.a'] = '0'
        blast['k.b'] = '0'
        blast.clear()
        self.assertEqual(len(blast), 0)

        blast['a'] = '0'
        blast['b'] = '0'
        blast['k.a'] = '0'
        blast['k.b'] = '0'
        blast.clear(key='k')
        self.assertEqual(set(blast), {'a', 'b'})

    def test_validation(self):
        blast = self.blast

        self.assertTrue(blast.is_valid_key('a'))
        self.assertTrue(blast.is_valid_key('wordy'))
        self.assertTrue(blast.is_valid_key('борщ'))
        self.assertTrue(blast.is_valid_key('word1.word2'))
        self.assertTrue(blast.is_valid_key('борщ.матрёшка'))

        self.assertFalse(blast.is_valid_key('word1 word2'))
        self.assertFalse(blast.is_valid_key('wo.rd1 word2'))
        self.assertFalse(blast.is_valid_key('word.'))
        self.assertFalse(blast.is_valid_key('word1.word2.word3'))
        self.assertFalse(blast.is_valid_key('word1.word2.'))
        self.assertFalse(blast.is_valid_key('.word'))
        self.assertFalse(blast.is_valid_key('word1.wor d2'))
        self.assertFalse(blast.is_valid_key('...word1'))
        self.assertFalse(blast.is_valid_key('word1..word2'))


class TestOutput(unittest.TestCase):
    @staticmethod
    def mk_fake(**dct):
        class FakeArgs:
            pass
        f = FakeArgs()
        f.__dict__ = dct
        return f
    
    def set_fake_buffer(self):
        self.fake_stdout = io.StringIO()
        sys.stdout = self.fake_stdout

    def setUp(self):
        self.blast = blast.Blast(TMP_FILE)
        self.old_stdout = sys.stdout
        self.set_fake_buffer()

    def tearDown(self):
        sys.stdout = self.old_stdout
        self.fake_stdout.close()
        self.blast.close()
        cleanup()

    def test_get(self):
        blast = self.blast

        blast.cmd_set(self.mk_fake(key='a', value='42'))
        blast.cmd_get(self.mk_fake(key='a'))
        self.assertEqual(self.fake_stdout.getvalue(), '42\n')
        self.set_fake_buffer()

        blast.cmd_set(self.mk_fake(key='b.c', value='42'))
        blast.cmd_get(self.mk_fake(key='b.c'))
        self.assertEqual(self.fake_stdout.getvalue(), '42\n')
        self.set_fake_buffer()

        blast.cmd_get(self.mk_fake(key='nonexistent'))
        self.assertIn('Error', self.fake_stdout.getvalue())

    def test_delete(self):
        blast = self.blast

        blast.cmd_set(self.mk_fake(key='a', value='42'))
        blast.cmd_get(self.mk_fake(key='a'))
        self.assertEqual(self.fake_stdout.getvalue(), '42\n')
        self.set_fake_buffer()

        blast.cmd_delete(self.mk_fake(key='a'))
        blast.cmd_get(self.mk_fake(key='a'))
        self.assertIn('Error', self.fake_stdout.getvalue())
        self.set_fake_buffer()

        blast.cmd_set(self.mk_fake(key='b.c', value='42'))
        blast.cmd_set(self.mk_fake(key='a', value='42'))
        blast.cmd_get(self.mk_fake(key='b.c'))
        self.assertEqual(self.fake_stdout.getvalue(), '42\n')
        self.set_fake_buffer()

        blast.cmd_get(self.mk_fake(key='a'))
        self.assertEqual(self.fake_stdout.getvalue(), '42\n')
        self.set_fake_buffer()

        blast.cmd_delete(self.mk_fake(key='b'))
        self.assertIn('Error', self.fake_stdout.getvalue())
        self.set_fake_buffer()

        blast.cmd_delete(self.mk_fake(key='a'))
        blast.cmd_get(self.mk_fake(key='b.c'))
        self.assertEqual(self.fake_stdout.getvalue(), '42\n')
        self.set_fake_buffer()

        blast.cmd_delete(self.mk_fake(key='b.c'))
        blast.cmd_get(self.mk_fake(key='b.c'))
        self.assertIn('Error', self.fake_stdout.getvalue())
        self.set_fake_buffer()

    def test_list(self):
        blast = self.blast

        blast.cmd_set(self.mk_fake(key='a', value='42'))
        blast.cmd_set(self.mk_fake(key='b', value='42'))
        blast.cmd_set(self.mk_fake(key='k.a', value='42'))
        blast.cmd_set(self.mk_fake(key='k.b', value='42'))
        blast.cmd_set(self.mk_fake(key='k2.a', value='42'))
        blast.cmd_list(self.mk_fake(key=None))
        self.assertEquals(self.fake_stdout.getvalue(), 'a\nb\nk.a\nk.b\nk2.a\n')
        self.set_fake_buffer()

        blast.cmd_list(self.mk_fake(key='k'))
        self.assertEquals(self.fake_stdout.getvalue(), 'k.a\nk.b\n')
        self.set_fake_buffer()

        blast.cmd_list(self.mk_fake(key='k.a'))
        self.assertIn('no entries', self.fake_stdout.getvalue())
        self.set_fake_buffer()

        blast.cmd_list(self.mk_fake(key='a'))
        self.assertIn('no entries', self.fake_stdout.getvalue())
        self.set_fake_buffer()

        blast.cmd_delete(self.mk_fake(key='a'))
        blast.cmd_delete(self.mk_fake(key='b'))
        blast.cmd_delete(self.mk_fake(key='k.a'))
        blast.cmd_delete(self.mk_fake(key='k.b'))
        blast.cmd_delete(self.mk_fake(key='k2.a'))
        blast.cmd_list(self.mk_fake(key=None))
        self.assertIn('no entries', self.fake_stdout.getvalue())
        self.set_fake_buffer()

        blast.cmd_list(self.mk_fake(key='a'))
        self.assertIn('no entries', self.fake_stdout.getvalue())
        self.set_fake_buffer()

    def test_clear(self):
        blast = self.blast

        blast.cmd_set(self.mk_fake(key='a', value='42'))
        blast.cmd_set(self.mk_fake(key='b', value='42'))
        blast.cmd_set(self.mk_fake(key='k.v', value='42'))
        blast.cmd_clear(self.mk_fake(key=None))
        blast.cmd_list(self.mk_fake(key=None))
        self.assertIn('no entries', self.fake_stdout.getvalue())
        self.set_fake_buffer()

        blast.cmd_set(self.mk_fake(key='a', value='42'))
        blast.cmd_set(self.mk_fake(key='b', value='42'))
        blast.cmd_set(self.mk_fake(key='k.a', value='42'))
        blast.cmd_set(self.mk_fake(key='k.b', value='42'))
        blast.cmd_set(self.mk_fake(key='k.c', value='42'))
        blast.cmd_clear(self.mk_fake(key='k'))
        blast.cmd_list(self.mk_fake(key=None))
        self.assertEqual(self.fake_stdout.getvalue(), 'a\nb\n')
        self.set_fake_buffer()

    def test_open(self):
        val = None
        def fake_open(url):
            nonlocal val
            val = url
        blast.Platform.open = fake_open

        b = self.blast
        b.cmd_set(self.mk_fake(key='a', value='42'))
        b.cmd_open(self.mk_fake(key='a'))
        self.assertEqual(val, '42')

    def test_validation(self):
        blast = self.blast

        with self.assertRaises(SystemExit):
            blast.cmd_set(self.mk_fake(key='a.b.c', value='42'))


class TestMain(unittest.TestCase):
    class OMNOMNOM:
        def write(self, _):
            pass

    def set_fake_buffer(self):
        self.fake_stdout = io.StringIO()
        sys.stdout = self.fake_stdout

    def setUp(self):
        self.old_stdout = sys.stdout
        self.old_stderr = sys.stderr
        sys.stderr = self.OMNOMNOM()
        self.set_fake_buffer()
        self.old_db_path = blast.Blast.DEFAULT_DB_PATH
        blast.Blast.DEFAULT_DB_PATH = TMP_FILE

    def tearDown(self):
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr
        self.fake_stdout.close()
        blast.Blast.DEFAULT_DB_PATH = self.old_db_path
        cleanup()

    def test_get(self):
        blast.main(['set', 'a', '42'])
        blast.main(['get', 'a'])
        self.assertEqual(self.fake_stdout.getvalue(), '42\n')

    def test_delete(self):
        blast.main(['set', 'a', '42'])
        blast.main(['delete', 'a'])
        blast.main(['get', 'a'])
        self.assertIn('Error', self.fake_stdout.getvalue())

    def test_list(self):
        blast.main(['set', 'a', '42'])
        blast.main(['set', 'k.b', '42'])
        blast.main(['list'])
        self.assertEqual(self.fake_stdout.getvalue(), 'a\nk.b\n')

    def test_clear(self):
        blast.main(['set', 'a', '42'])
        blast.main(['clear'])
        blast.main(['list'])
        self.assertIn('no entries', self.fake_stdout.getvalue())

    def test_open(self):
        val = None
        def fake_open(url):
            nonlocal val
            val = url
        blast.Platform.open = fake_open

        blast.main(['set', 'a', '42'])
        blast.main(['open', 'a'])
        self.assertEqual(val, '42')
