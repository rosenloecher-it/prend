import datetime
import math
import unittest
from app.fronmod import *


class MockEflowChannel(EflowChannel):

    def __init__(self, source_name, agg_plus, agg_minus):
        super().__init__(source_name, agg_plus, agg_minus)
        self.mock_time = None

    def get_current_time(self):
        return self.mock_time


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

    def test_complete(self):
        item = 'item'
        plus = 'plus'
        minus = 'minus'

        eflow = MockEflowChannel(item, EflowAggregate(plus), EflowAggregate(minus))
        print(eflow)

        current_time = datetime.datetime(2019, 9, 9, 0, 0, 0)
        eflow.mock_time = current_time

        self.assertEqual(None, eflow.last_time)
        self.assertEqual(None, eflow.last_value)

        last_value = 1
        eflow.push_value(last_value)

        self.assertEqual(current_time, eflow.last_time)
        self.assertEqual(last_value, eflow.last_value)
        self.assertEqual(0, eflow.plus.value_agg)
        self.assertEqual(0, eflow.minus.value_agg)

        # no time change
        eflow.push_value(last_value)
        self.assertEqual(current_time, eflow.last_time)
        self.assertEqual(last_value, eflow.last_value)
        self.assertEqual(0, eflow.plus.value_agg)
        self.assertEqual(0, eflow.minus.value_agg)

        # next step + 1 hour

        current_time += datetime.timedelta(hours=1)
        eflow.mock_time = current_time

        eflow.push_value(last_value)
        self.assertEqual(current_time, eflow.last_time)
        self.assertEqual(last_value, eflow.last_value)
        self.assertEqual(1, eflow.plus.value_agg)
        self.assertEqual(0, eflow.minus.value_agg)

        # next step

        current_time += datetime.timedelta(hours=1)
        eflow.mock_time = current_time

        last_value = -1
        eflow.push_value(last_value)

        self.assertEqual(current_time, eflow.last_time)
        self.assertEqual(last_value, eflow.last_value)

        self.assertEqual(1.25, eflow.plus.value_agg)
        self.assertEqual(-0.25, eflow.minus.value_agg)

        # next step

        current_time += datetime.timedelta(hours=1)
        eflow.mock_time = current_time

        last_value = -1
        eflow.push_value(last_value)

        self.assertEqual(current_time, eflow.last_time)
        self.assertEqual(last_value, eflow.last_value)

        self.assertEqual(1.25, eflow.plus.value_agg)
        self.assertEqual(-1.25, eflow.minus.value_agg)

        # next step

        current_time += datetime.timedelta(hours=0.5)
        eflow.mock_time = current_time

        last_value = -1
        eflow.push_value(last_value)

        self.assertEqual(current_time, eflow.last_time)
        self.assertEqual(last_value, eflow.last_value)

        self.assertEqual(1.25, eflow.plus.value_agg)
        self.assertEqual(-1.75, eflow.minus.value_agg)

        # next step

        current_time += datetime.timedelta(hours=1)
        eflow.mock_time = current_time

        last_value = 0
        eflow.push_value(last_value)
        self.assertEqual(1.25, eflow.plus.value_agg)
        self.assertEqual(-2.25, eflow.minus.value_agg)

        # next step

        current_time += datetime.timedelta(hours=1)
        eflow.mock_time = current_time

        last_value = 0
        eflow.push_value(last_value)
        self.assertEqual(1.25, eflow.plus.value_agg)
        self.assertEqual(-2.25, eflow.minus.value_agg)

        # next step

        current_time += datetime.timedelta(hours=1)
        eflow.mock_time = current_time

        last_value = 1
        eflow.push_value(last_value)
        self.assertEqual(1.75, eflow.plus.value_agg)
        self.assertEqual(-2.25, eflow.minus.value_agg)

        print(eflow)

        # finish

        aggs = eflow.get_aggregates_and_reset()
        self.assertEqual(2, len(aggs))

        hit = 0
        for agg in aggs:
            if agg.item_name == plus and agg.value_agg == 1.75:
                hit += 1
            if agg.item_name == minus and agg.value_agg == -2.25:
                hit += 1
        self.assertEqual(2, hit)

        self.assertEqual(0, eflow.plus.value_agg)
        self.assertEqual(0, eflow.minus.value_agg)

    def test_realistic_times(self):

        item = 'item'
        plus = 'plus'
        minus = 'minus'

        eflow = MockEflowChannel(item, EflowAggregate(plus), EflowAggregate(minus))
        print(eflow)

        eflow.mock_time = datetime.datetime.now()

        value_plus = 800.0
        eflow.push_value(value_plus)

        self.assertEqual(eflow.mock_time, eflow.last_time)
        self.assertEqual(value_plus, eflow.last_value)
        self.assertEqual(0, eflow.plus.value_agg)
        self.assertEqual(0, eflow.minus.value_agg)

        offset_seconds = 10
        for i in range(0, 6):
            eflow.mock_time = eflow.mock_time + datetime.timedelta(seconds=offset_seconds)
            eflow.push_value(value_plus)

        self.assertEqual(0, eflow.minus.value_agg)
        self.assertTrue(math.isclose(value_plus / 60.0, eflow.plus.value_agg, rel_tol=1e-6))

        pass
