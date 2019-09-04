import unittest
from prend.tools.convert import Convert


class TestConvert(unittest.TestCase):

    def test_convert_to_bool(self):

        self.assertEqual(Convert.convert_to_bool(' trUe '), True)
        self.assertEqual(Convert.convert_to_bool(' Yes '), True)
        self.assertEqual(Convert.convert_to_bool(' 1 '), True)
        self.assertEqual(Convert.convert_to_bool(' oN '), True)

        self.assertEqual(Convert.convert_to_bool(' fAlse '), False)
        self.assertEqual(Convert.convert_to_bool(' no '), False)
        self.assertEqual(Convert.convert_to_bool(' 0 '), False)
        self.assertEqual(Convert.convert_to_bool(' oFf '), False)

        self.assertEqual(Convert.convert_to_bool(' ddddd ', False), False)
        self.assertEqual(Convert.convert_to_bool(' ddddd ', True), True)

        self.assertEqual(Convert.convert_to_bool(None, False), False)
        self.assertEqual(Convert.convert_to_bool(None, True), True)

    def test_convert_to_int(self):
        self.assertEqual(Convert.convert_to_int(' 123 '), 123)
        self.assertEqual(Convert.convert_to_int(' -9 '), -9)

        self.assertEqual(Convert.convert_to_int('  ', 123), 123)
        self.assertEqual(Convert.convert_to_int(' abc ', 123), 123)
        self.assertEqual(Convert.convert_to_int(None, 123), 123)

    def test_convert_to_float(self):
        self.assertEqual(Convert.convert_to_float(' 123.23 '), 123.23)
        self.assertEqual(Convert.convert_to_float(' -9.3 '), -9.3)

        self.assertEqual(Convert.convert_to_float('  ', 1.1), 1.1)
        self.assertEqual(Convert.convert_to_float(' abc ', 1.1), 1.1)
        self.assertEqual(Convert.convert_to_float(None, 1.1), 1.1)
