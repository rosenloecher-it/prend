import unittest
from prend.values import HsbValue


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



if __name__ == '__main__':
    unittest.main()
