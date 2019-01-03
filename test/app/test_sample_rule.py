import unittest
from app.sample_rule import SampleRule
from prend.action import Action
from prend.channel import Channel
from prend.dispatcher import Dispatcher
from prend.state import State, StateType
from test.prend.oh.mock_oh_gateway import MockOhGateway


class TestSampleRule(unittest.TestCase):

    def setUp(self):
        self.dispatcher = Dispatcher()

        self.mock_gateway = MockOhGateway()
        self.mock_gateway.set_dispatcher(self.dispatcher)

        self.rule = SampleRule()
        self.rule.set_dispatcher(self.dispatcher)
        self.rule.set_oh_gateway(self.mock_gateway)

    def test_notify_action(self):
        expected_num = 2
        self.mock_gateway.set_state(Channel.create_item(SampleRule.ITEM_DUMMY_1)
                                    , State.create(StateType.DECIMAL, expected_num))

        action = Action.create_cron_action(SampleRule.CRON_NAME)
        self.rule.notify_action(action)

        self.assertEqual(2, len(self.mock_gateway.sent_actions_list))
        self.assertEqual(2, len(self.mock_gateway.sent_actions_dict))

        value_str = self.mock_gateway.get_sent_data(Channel.create_item(SampleRule.ITEM_STRING))
        value_num = self.mock_gateway.get_sent_data(Channel.create_item(SampleRule.ITEM_DUMMY_2))

        self.assertTrue(value_str is not None)
        self.assertEqual(expected_num, value_num)

    def test_notify_action_not_connected(self):
        self.mock_gateway.mock_is_connected = False

        expected_num = 2
        self.mock_gateway.set_state(Channel.create_item(SampleRule.ITEM_DUMMY_1)
                                    , State.create(StateType.DECIMAL, expected_num))

        action = Action.create_cron_action(SampleRule.CRON_NAME)
        self.rule.notify_action(action)

        self.assertEqual(0, len(self.mock_gateway.sent_actions_list))
        self.assertEqual(0, len(self.mock_gateway.sent_actions_dict))

    def test_dummy(self):
        print('dummy')
        rule = SampleRule()
        print(rule)
        self.assertTrue(True)
