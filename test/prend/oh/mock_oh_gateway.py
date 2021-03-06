import copy
import datetime

from prend.channel import Channel, ChannelType
from prend.oh.oh_gateway import OhGateway
from prend.oh.oh_send_data import OhSendData, OhSendFlags
from prend.state import State, StateType
from typing import Optional

from prend.values import OnOffValue


class MockOhGateway(OhGateway):

    def __init__(self):
        super().__init__()

        self.sent_actions_list = []
        self.sent_actions_channel_dict = {}
        self.mock_is_connected = True

    def send(self, flags: OhSendFlags, channel, state):
        send_data = OhSendData(flags, channel, state)
        send_data.check()

        self.sent_actions_list.append(send_data)
        self.sent_actions_channel_dict[send_data.get_channel()] = send_data

        super().send(flags, channel, state)

    def is_connected(self):
        return self.mock_is_connected

    def set_state(self, channel_in: Channel, state_in: State):
        if state_in is None:
            state_in = State.create(StateType.UNDEF, None)

        if isinstance(state_in, int) or isinstance(state_in, float):
            state_in = State.create(StateType.DECIMAL, state_in)
        if isinstance(state_in, OnOffValue):
            state_in = State.create(StateType.ONOFF, state_in)
        if isinstance(state_in, datetime.datetime):
            state_in = State.create(StateType.DATETIME, state_in)

        if not isinstance(state_in, State):
            raise TypeError(f"State expected, is'{type(state_in)}' instead!")
        channel = copy.deepcopy(channel_in)
        state = copy.deepcopy(state_in)
        with self._lock_state:
            self._states[channel] = state

    def clear_state(self, channel: Channel):
        if channel:
            with self._lock_state:
                del self._states[channel]

    def set_item_state(self, channel_name, state: Optional[State]):
        channel = Channel.create_item(channel_name)
        self.set_state(channel, state)

    def clear_item_state(self, channel_name):
        channel = Channel.create_item(channel_name)
        self.clear_state(channel)

    def clear_sent_actions(self):
        self._send_queue.empty()
        self.sent_actions_list.clear()
        self.sent_actions_channel_dict.clear()

    def clear(self):
        self.clear_sent_actions()
        with self._lock_state:
            self._states.clear()

    def cache_states(self):
        # prepare chache in test setup
        pass

    def get_last_channel_data(self, channel):
        if isinstance(channel, str):
            channel = Channel.create(ChannelType.ITEM, channel)
        sent_data = self.sent_actions_channel_dict.get(channel)
        if sent_data is None:
            return None
        return sent_data.state

    def exists_sent_item(self, channel_in, data_compare) -> bool:
        if isinstance(channel_in, Channel):
            channel = channel_in
        elif isinstance(channel_in, str):
            channel = Channel.create_item(channel_in)
        else:
            raise TypeError()

        for sent_data in self.sent_actions_list:
            if sent_data.get_channel() != channel:
                continue

            if isinstance(sent_data.state, State):
                sent_value = sent_data.state.value
            else:
                sent_value = sent_data.state

            if isinstance(data_compare, State):
                comp_value = data_compare.value
            else:
                comp_value = data_compare

            if type(sent_value) == float and type(comp_value) == float:
                if abs(sent_value - comp_value) <= 0.000001:
                    return True
            else:
                if sent_value == comp_value:
                    return True

        return False

    def is_sent_item(self, index: int, channel_in, data_compare) -> bool:
        if isinstance(channel_in, Channel):
            channel = channel_in
        elif isinstance(channel_in, str):
            channel = Channel.create_item(channel_in)
        else:
            raise TypeError()

        sent_data = self.sent_actions_list[index]

        if sent_data.get_channel() != channel:
            return False

        if isinstance(sent_data.state, State):
            sent_value = sent_data.state.value
        else:
            sent_value = sent_data.state

        if isinstance(data_compare, State):
            comp_value = data_compare.value
        else:
            comp_value = data_compare

        if type(sent_value) == float and type(comp_value) == float:
            if abs(sent_value - comp_value) <= 0.000001:
                return True
        else:
            if sent_value == comp_value:
                return True

        return False
