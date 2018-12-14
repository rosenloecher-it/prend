import copy
import datetime
import unittest
from dateutil.tz import tzoffset
from prend.state import State, StateType
from prend.values import OnOffValue, ThingStatusValue


class TestStateType(unittest.TestCase):

    def test_parse_type(self):

        out = StateType.parse('???')
        self.assertEqual(out, StateType.UNKNOWN)

        out = StateType.parse(None)
        self.assertEqual(out, StateType.UNKNOWN)

        out = StateType.parse(' Number ')
        self.assertEqual(out, StateType.DECIMAL)

        out = StateType.parse('decimal')
        self.assertEqual(out, StateType.DECIMAL)

        out = StateType.parse('Decimal')
        self.assertEqual(out, StateType.DECIMAL)


    def test_is_number_type(self):

        for en in StateType:
            expected = False
            if en in [StateType.DECIMAL, StateType.DIMMER, StateType.ROLLERSHUTTER, StateType.PERCENT]:
                expected = True
            out = en.is_number_type()
            self.assertEqual(out, expected)


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

        out = State.convert_to_json(ThingStatusValue.ONLINE)
        self.assertEqual(out, 'ONLINE')
        out = State.convert_to_json(ThingStatusValue.OFFLINE)
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

    def check_convert_roundabout(self, state_type, state_value):

        state = State.convert(state_type, state_value)
        json_out = State.convert_to_json(state.value)

        if not json_out or json_out != state_value:
            print('check_convert_roundabout - {}\n    in  = {}\n    out = {}'.format(state_type, state_value, json_out))
            self.assertTrue(False)

    def test_convert_roundabout(self):

        # wrong type/value combination
        self.check_convert_roundabout(' onoff ', 'abc')
        self.check_convert_roundabout(' upDown ', 'abc')
        self.check_convert_roundabout(' decimAl ', 'abc')
        self.check_convert_roundabout(' decimAl ', 'abc')
        self.check_convert_roundabout(' thing ', 'abc')

        self.check_convert_roundabout(' unknown_type_XGH ', '66,56,0')
        self.check_convert_roundabout(' hsb ', '66,56,0')

        self.check_convert_roundabout(' decimAl ', '123.4')

        self.check_convert_roundabout(' onoff ', 'ON')
        self.check_convert_roundabout(' onoff ', 'OFF')

        self.check_convert_roundabout(' upDown ', 'UP')
        self.check_convert_roundabout(' upDown ', 'DOWN')

        self.check_convert_roundabout(' thing_status ', 'ONLINE')
        self.check_convert_roundabout(' thing ', 'OFFLINE')
        self.check_convert_roundabout(' thing ', 'INITIALIZING')
        self.check_convert_roundabout(StateType.THING_STATUS.name, 'ONLINE')

    def check_ensure_value_int(self, state_type, value_in, value_cmp):
        state = State.create(state_type, copy.deepcopy(value_in))
        value_out = state.ensure_value_int()
        self.assertEqual(value_out, value_cmp)

    def test_ensure_value_int(self):
        self.check_ensure_value_int(StateType.ROLLERSHUTTER, 11.23, 11)
        self.check_ensure_value_int(StateType.DIMMER, 11.23, 11)
        self.check_ensure_value_int(StateType.DECIMAL, -11.23, -11)
        self.check_ensure_value_int(StateType.PERCENT, 11, 11)

    def check_ensure_value_float(self, state_type, value_in, value_cmp):
        state = State.create(state_type, copy.deepcopy(value_in))
        value_out = state.ensure_value_float()
        self.assertEqual(value_out, value_cmp)

    def test_ensure_value_float(self):
        self.check_ensure_value_float(StateType.ROLLERSHUTTER, 11.23, 11.23)
        self.check_ensure_value_float(StateType.DIMMER, 11.23, 11.23)
        self.check_ensure_value_float(StateType.DECIMAL, -11.23, -11.23)
        self.check_ensure_value_float(StateType.PERCENT, 11, 11)

    def check_set_value_check_type(self, state_type, value1, value2, expected_result):
        state = State.create(state_type, value1)
        result = state.set_value_check_type(copy.deepcopy(value2))
        self.assertEqual(result, expected_result)
        if result:
            self.assertEqual(state.value, value2)

    def test_set_value_check_type(self):
        self.check_set_value_check_type(StateType.DECIMAL, 1, 2.4, True)
        self.check_set_value_check_type(StateType.DECIMAL, 1, 2, True)
        self.check_set_value_check_type(StateType.DECIMAL, 1.23, 2.34, True)
        self.check_set_value_check_type(StateType.DECIMAL, 1.23, 2, True)


if __name__ == '__main__':
    unittest.main()
