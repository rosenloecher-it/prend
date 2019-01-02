import unittest
from prend.channel import Channel
from prend.config import ConfigLoader
from prend.oh.oh_gateway import OhGateway
from prend.oh.oh_send_data import OhSendFlags
from prend.rule import Rule
from prend.state import State, StateType
from typing import Optional


class MockOhGateway(OhGateway):

    def __init__(self):
        super().__init__()
        self.last_channel = None
        self.last_state = None

    def send(self, send_command: bool, channel: Channel, state):
        self.last_channel = channel
        self.last_state = state

    def get_states(self):
        pass

    def get_state(self, channel: Channel) -> Optional[State]:
        self.last_channel = channel
        return self.last_state


class MockRule(Rule):

    def __init__(self):
        super().__init__()
        self._config = {}

    def register_actions(self) -> None:
        pass

    def notify_action(self, action) -> None:
        pass

    def add_to_config(self, section_name, value_name, value):
        ConfigLoader.add_to_rule_config(self._config, section_name, value_name, str(value))


class TestRule(unittest.TestCase):

    def test_get_config(self):

        rule = MockRule()
        section_name = 'section'

        value_name = 'bool'
        rule.add_to_config(section_name, value_name, ' trUe ')
        out = rule.get_config_bool(section_name, value_name)
        self.assertEqual(out, True)

        rule.add_to_config(section_name, value_name, '   ')
        out = rule.get_config_bool(section_name, value_name, True)
        self.assertEqual(out, True)

        out = rule.get_config_bool('section_should_not_exists', value_name, True)
        self.assertEqual(out, True)

        value_name = 'int'
        rule.add_to_config(section_name, value_name, '  123 ')
        out = rule.get_config_int(section_name, value_name)
        self.assertEqual(out, 123)

        rule.add_to_config(section_name, value_name, '  -23 ')
        out = rule.get_config_int(section_name, value_name)
        self.assertEqual(out, -23)

        rule.add_to_config(section_name, value_name, None)
        out = rule.get_config_int(section_name, value_name, -23)
        self.assertEqual(out, -23)

        out = rule.get_config_int('section_should_not_exists', value_name, 123)
        self.assertEqual(out, 123)

        value_name = 'float'
        rule.add_to_config(section_name, value_name, '  123.12 ')
        out = rule.get_config_float(section_name, value_name)
        self.assertEqual(out, 123.12)

        rule.add_to_config(section_name, value_name, '  999 ')
        out = rule.get_config_float(section_name, value_name)
        self.assertEqual(out, 999)

        rule.add_to_config(section_name, value_name, '  -23.9 ')
        out = rule.get_config_float(section_name, value_name)
        self.assertEqual(out, -23.9)

        rule.add_to_config(section_name, value_name, None)
        out = rule.get_config_float(section_name, value_name, -23.6)
        self.assertEqual(out, -23.6)

        out = rule.get_config_float('section_should_not_exists', value_name, 123.5)
        self.assertEqual(out, 123.5)

        out = rule.get_config_float('section_should_not_exists', value_name, 123)
        self.assertEqual(out, 123)

    # def test_send_and_get_state(self):
    #     rule = MockRule()
    #     gateway = MockOhGateway()
    #     rule.set_oh_gateway(gateway)
    #
    #     channel = Channel.create(ChannelType.ITEM, 'test')
    #     state = State()
    #     state.type = StateType.DECIMAL
    #     state.value = 123
    #     state.update_last_change()
    #
    #     rule.send_command(channel, state)
    #     self.assertEqual(gateway.last_channel, channel)
    #     self.assertEqual(gateway.last_state, state)
    #
    #     rule.send_update(channel, state)
    #     self.assertEqual(gateway.last_channel, channel)
    #     self.assertEqual(gateway.last_state, state)
    #
    #     out = rule.get_state(channel)
    #     self.assertEqual(out, state)
    #
    #     out = rule.get_item_state(channel.name)
    #     self.assertEqual(out, state)
    #
    #     out = rule.get_state_value(channel)
    #     self.assertEqual(out, state.value)
    #
    #     out = rule.get_item_state_value(channel.name)
    #     self.assertEqual(out, state.value)
    #
    #     rule.send(OhSendFlags.COMMAND | OhSendFlags.CHANNEL_AS_ITEM, channel.name, state)
    #     self.assertEqual(gateway.last_channel, channel)
    #     self.assertEqual(gateway.last_state, state)
    #
    #     rule.send(OhSendFlags.UPDATE | OhSendFlags.CHANNEL_AS_ITEM, channel.name, state)
    #     self.assertEqual(gateway.last_channel, channel)
    #     self.assertEqual(gateway.last_state, state)


if __name__ == '__main__':
    unittest.main()
