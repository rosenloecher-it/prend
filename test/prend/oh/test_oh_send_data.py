import unittest
from prend.channel import Channel
from prend.oh.oh_send_data import OhSendData, OhSendFlags
from prend.state import State, StateType


class TestOhSendData(unittest.TestCase):

    def test_common(self):

        channel = Channel.create_item('abc')
        state = State.create(StateType.DECIMAL, 1.23)

        data = OhSendData(OhSendFlags.COMMAND | OhSendFlags.SEND_ONLY_IF_DIFFER, channel, state)
        data.check()  # no raise
        self.assertTrue(data.flags & OhSendFlags.COMMAND)
        self.assertTrue(data.flags & OhSendFlags.SEND_ONLY_IF_DIFFER)
        self.assertTrue(data.is_flag(OhSendFlags.SEND_ONLY_IF_DIFFER))
        self.assertTrue(data.is_send())
        self.assertTrue(not data.is_update())
        self.assertEqual(data.get_channel(), channel)
        self.assertEqual(data.get_state_value(), state.value)

        data = OhSendData(OhSendFlags.UPDATE | OhSendFlags.CHANNEL_AS_ITEM, channel.name, state.value)
        data.check()  # no raise
        self.assertTrue(data.flags & OhSendFlags.UPDATE)
        self.assertTrue(data.flags & OhSendFlags.CHANNEL_AS_ITEM)
        self.assertTrue(data.is_flag(OhSendFlags.CHANNEL_AS_ITEM))
        self.assertTrue(not data.is_send())
        self.assertTrue(data.is_update())
        self.assertEqual(data.get_channel(), channel)
        self.assertEqual(data.get_state_value(), state.value)

    def test_check_fails(self):

        channel = Channel.create_item('abc')
        state = State.create(StateType.DECIMAL, 1.23)

        try:
            data = OhSendData(OhSendFlags.COMMAND | OhSendFlags.UPDATE, channel, state)
            data.check()  # no raise
            self.assertTrue(False)
        except (TypeError, ValueError):
            self.assertTrue(True)

        try:
            data = OhSendData(OhSendFlags.COMMAND | OhSendFlags.CHANNEL_AS_ITEM, 123, state)
            data.check()  # no raise
            self.assertTrue(False)
        except (TypeError, ValueError):
            self.assertTrue(True)

        try:
            data = OhSendData(OhSendFlags.COMMAND | OhSendFlags.CHANNEL_AS_ITEM, None, state)
            data.check()  # no raise
            self.assertTrue(False)
        except (TypeError, ValueError):
            self.assertTrue(True)
