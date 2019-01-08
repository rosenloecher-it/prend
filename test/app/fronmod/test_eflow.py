import datetime
import unittest
from app.fronmod import *
from typing import Optional

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

        class MockEflowChannel(EflowChannel):

            def __init__(self, source_name, agg_plus, agg_minus):
                super().__init__(source_name, agg_plus, agg_minus)
                self.mock_time = None

            def _get_time(self):
                return self.mock_time

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
