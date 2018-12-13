import unittest
from app.sample_rule import SampleRule

class TestSampleRule(unittest.TestCase):

    def test_dummy(self):
        print('dummy')
        rule = SampleRule()
        self.assertTrue(True)
