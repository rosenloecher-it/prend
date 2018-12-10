import copy
import datetime
import unittest
from dateutil.tz import tzoffset
from prend.state import State, StateType
from prend.values import OnOffValue, OnlineOfflineValue


class TestStateType(unittest.TestCase):

    def test_parse_type(self):

        out = StateType.parse('???')
        self.assertEqual(out, None)

        out = StateType.parse(None)
        self.assertEqual(out, None)

        out = StateType.parse('decimal')
        self.assertEqual(out, StateType.DECIMAL)

        out = StateType.parse('Decimal')
        self.assertEqual(out, StateType.DECIMAL)


class TestState(unittest.TestCase):

    def test_eq(self):
        orig = State()
        orig.type = StateType.DECIMAL
        orig.value = 'hgffc'

        comp = copy.deepcopy(orig)
        comp.update_last_change()
        self.assertTrue(orig == comp)

        comp = copy.deepcopy(orig)
        comp.type = StateType.ONOFF
        self.assertTrue(orig != comp)

        comp = copy.deepcopy(orig)
        comp.value = orig.value + '2'
        self.assertTrue(orig != comp)

    def test_convert_to_json(self):

        out = State.convert_to_json(datetime.datetime(2018, 12, 3, 13, 7, 45, tzinfo=tzoffset(None, 3600)))
        self.assertEqual(out, '2018-12-03T13:07:45+01:00')

        out = State.convert_to_json(-0.123)
        self.assertEqual(out, '-0.123')

        out = State.convert_to_json(0.123)
        self.assertEqual(out, '0.123')

        out = State.convert_to_json(-123)
        self.assertEqual(out, '-123')

        out = State.convert_to_json(123)
        self.assertEqual(out, '123')

        out = State.convert_to_json(OnlineOfflineValue.ONLINE)
        self.assertEqual(out, 'ONLINE')
        out = State.convert_to_json(OnlineOfflineValue.OFFLINE)
        self.assertEqual(out, 'OFFLINE')

        out = State.convert_to_json(OnOffValue.ON)
        self.assertEqual(out, 'ON')
        out = State.convert_to_json(OnOffValue.OFF)
        self.assertEqual(out, 'OFF')

        out = State.convert_to_json(None)
        self.assertEqual(out, 'UNDEF')

    def test_import_state(self):
        # todo
        pass


if __name__ == '__main__':
    unittest.main()
