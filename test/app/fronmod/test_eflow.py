import unittest
from app.fronmod import *


class TestEflow(unittest.TestCase):

    def test_get_normed_intercept(self):
        intercept1 = EflowChannel.get_normed_intercept(-1, 1)
        self.assertEqual(0.5, intercept1)

        intercept1 = EflowChannel.get_normed_intercept(1, -1)
        self.assertEqual(0.5, intercept1)

        intercept1 = EflowChannel.get_normed_intercept(1, -3)
        self.assertEqual(0.25, intercept1)

        intercept1 = EflowChannel.get_normed_intercept(3, -1)
        self.assertEqual(0.75, intercept1)
