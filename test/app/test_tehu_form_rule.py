import datetime
import locale
import unittest
from app.tehu_form_rule import TehuFormRule, ItemSet
from prend.action import Action
from prend.channel import Channel
from prend.dispatcher import Dispatcher
from prend.oh.oh_event import OhNotificationType
from prend.state import State, StateType
from test.prend.oh.mock_oh_gateway import MockOhGateway


class TestTehuFormRule(unittest.TestCase):

    DEFAULT_VALUE = 0

    def setUp(self):
        locale.setlocale(locale.LC_ALL, "de_DE.UTF8")

        self.dispatcher = Dispatcher()

        self.mock_gateway = MockOhGateway()
        self.mock_gateway.set_dispatcher(self.dispatcher)

        self.rule = TehuFormRule()
        self.rule.set_dispatcher(self.dispatcher)
        self.rule.set_oh_gateway(self.mock_gateway)

        state_num = State.create(StateType.DECIMAL, self.DEFAULT_VALUE)
        for item_set in self.rule._item_set_list:
            self.mock_gateway.set_state(Channel.create_item(item_set.humi), state_num)
            self.mock_gateway.set_state(Channel.create_item(item_set.temp), state_num)
            self.mock_gateway.set_state(Channel.create_item(item_set.temp)
                                        , State.create(StateType.STRING, self.DEFAULT_VALUE))

    def check_sent_item(self, item_name, state_type_expected, value_expected):

        channel = Channel.create_item(item_name)
        sent_item = self.mock_gateway.sent_actions_dict.get(channel)
        self.assertTrue(sent_item)

        self.assertEqual(sent_item.state.type, state_type_expected)
        self.assertEqual(sent_item.state.value, value_expected)

    def test_action_single(self):
        item_set = ItemSet('showTempHumiBathDown', 'valTempBathDown', 'valHumiBathDown')
        state_num = State.create(StateType.DECIMAL, self.DEFAULT_VALUE)

        self.mock_gateway.set_state(Channel.create_item(item_set.humi), state_num)
        self.mock_gateway.set_state(Channel.create_item(item_set.temp), state_num)

        new_value = 1.23
        action = Action()
        action.channel = Channel.create_item(item_set.temp)
        action.state_new = State.create(StateType.DECIMAL, new_value)
        action.notification_type = OhNotificationType.ITEM_COMMAND
        self.mock_gateway.set_state(Channel.create_item(item_set.temp), State.create(StateType.DECIMAL, new_value))

        self.rule.notify_action(action)

        # print('len(self.mock_gateway.sent_actions_list)=', len(self.mock_gateway.sent_actions_list))
        # print('len(self.mock_gateway.sent_actions_dict)=', len(self.mock_gateway.sent_actions_dict))
        # print(self.mock_gateway.sent_actions_list)
        self.assertEqual(1, len(self.mock_gateway.sent_actions_list))
        self.assertEqual(1, len(self.mock_gateway.sent_actions_dict))

        text_value = '1,2°C / 0%'
        self.check_sent_item('showTempHumiBathDown', StateType.STRING, text_value)

    def test_action_startup(self):
        action = Action.create_startup_action()
        self.rule.notify_action(action)

        # print('len(self.mock_gateway.sent_actions_list)=', len(self.mock_gateway.sent_actions_list))
        # print('len(self.mock_gateway.sent_actions_dict)=', len(self.mock_gateway.sent_actions_dict))
        # print(self.mock_gateway.sent_actions_list)

        self.assertEqual(len(self.mock_gateway.sent_actions_list), 7)
        self.assertEqual(len(self.mock_gateway.sent_actions_dict), 7)

        text_value = '0,0°C / 0%'

        for item_set in self.rule._item_set_list:
            self.check_sent_item(item_set.show, StateType.STRING, text_value)

    def test_format_number(self):

        state = State.create(StateType.DECIMAL, 0)

        state.value = 11.123
        out = TehuFormRule._format_number(state, False)
        print(out)
        self.assertEqual(out, '11,1°C')

        state.value = 9
        out = TehuFormRule._format_number(state, False)
        print(out)
        self.assertEqual(out, '9,0°C')

        state.value = 11.123
        out = TehuFormRule._format_number(state, True)
        print(out)
        self.assertEqual(out, '11%')

        state.value = 8.75  # round up
        out = TehuFormRule._format_number(state, True)
        print(out)
        self.assertEqual(out, '9%')

        # old value warning

        time_minus = TehuFormRule.TIME_SHOW_REFRESH_WARNING_SEC * 2
        state.last_change = datetime.datetime.now() - datetime.timedelta(seconds=time_minus)

        state.value = 11.123
        out = TehuFormRule._format_number(state, False)
        print(out)
        self.assertEqual(out, '!11,1°C')

        state.value = 8.75  # round up
        out = TehuFormRule._format_number(state, True)
        print(out)
        self.assertEqual(out, '!9%')

        # invalid state

        state.value = None
        out = TehuFormRule._format_number(state, True)
        print(out)
        self.assertEqual(out, '-')

        out = TehuFormRule._format_number(None, True)
        print(out)
        self.assertEqual(out, '-')
