import unittest
from prend.values import HsbValue, OpeningValue, OnOffValue


class TestHsbValue(unittest.TestCase):

    def test_parse(self):

        out = HsbValue.parse(' 12 , 14, 16.1 ')
        self.assertEqual(out, HsbValue(12, 14, 16))

        out = HsbValue.parse(' 12 , 14.8, 16.1 ')
        self.assertEqual(out, HsbValue(12, 15, 16))

        out = HsbValue.parse(' 12 , 14, 16 ')
        self.assertEqual(out, HsbValue(12, 14, 16))

        try:
            HsbValue.parse(' 12 , 14 ')
            self.assertTrue(False)
        except ValueError:
            self.assertTrue(True)

        try:
            HsbValue.parse(' 12 , 14 , abc')
            self.assertTrue(False)
        except ValueError:
            self.assertTrue(True)


class TestOpeningValue(unittest.TestCase):

    def test_parse(self):

        out = OpeningValue.parse(' closed ')
        self.assertEqual(out, OpeningValue.CLOSED)

        out = OpeningValue.parse(' tilted ')
        self.assertEqual(out, OpeningValue.TILTED)

        out = OpeningValue.parse(' Open ')
        self.assertEqual(out, OpeningValue.OPEN)


class TestOnOffValue(unittest.TestCase):

    def test_falsy(self):
        self.assertEqual(bool(OnOffValue.OFF), False)
        self.assertEqual(bool(OnOffValue.ON), True)
