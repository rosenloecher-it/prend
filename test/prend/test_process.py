import unittest
from prend.process import Process


class TestDispatcher(unittest.TestCase):

    def test_dummy(self):
        process = Process()

        out = process._print_and_return(1)
        self.assertEqual(out, 1)

        out = process._print_and_return(None)
        self.assertEqual(out, None)

    def test_init_locale(self):
        # mainly test no crash
        result = Process._init_locale('non_sense_dfdsfs')
        self.assertEqual(result, False)

        result = Process._init_locale('')
        self.assertEqual(result, True)

        result = Process._init_locale('  ')
        self.assertEqual(result, True)

        result = Process._init_locale(None)
        self.assertEqual(result, True)

        result = Process._init_locale('de_DE.UTF8  ')
        self.assertEqual(result, True)



