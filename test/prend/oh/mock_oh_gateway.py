import copy
from prend.channel import Channel
from prend.oh.oh_gateway import OhGateway
from prend.oh.oh_send_data import OhSendData, OhSendFlags
from prend.state import State


class MockOhGateway(OhGateway):

    def __init__(self):
        super().__init__()

        self.sent_actions_list = []
        self.sent_actions_dict = {}
        self.mock_is_connected = True

    def send(self, flags: OhSendFlags, channel, state):
        send_data = OhSendData(flags, channel, state)
        send_data.check()

        self.sent_actions_list.append(send_data)
        self.sent_actions_dict[send_data.get_channel()] = send_data

        super().send(flags, channel, state)

    def is_connected(self):
        return self.mock_is_connected

    def set_state(self, channel_in: Channel, state_in: State):
        if not isinstance(state_in, State):
            raise TypeError()
        channel = copy.deepcopy(channel_in)
        state = copy.deepcopy(state_in)
        with self._lock_state:
            self._states[channel] = state

    def set_item_state(self, channel_name, state: State):
        channel = Channel.create_item(channel_name)
        self.set_state(channel, state)

    def clear(self):
        self._send_queue.empty()
        self.sent_actions_list.clear()
        self.sent_actions_dict.clear()
        with self._lock_state:
            self._states.clear()

    def cache_states(self):
        # prepare chache in test setup
        pass

    def get_sent_data(self, channel):
        sent_data = self.sent_actions_dict.get(channel)
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

        sent_data = self.sent_actions_dict.get(channel)
        if sent_data is None:
            return False

        if isinstance(sent_data.state, State):
            sent_value = sent_data.state.value
        else:
            sent_value = sent_data.state

        if isinstance(data_compare, State):
            comp_value = data_compare.value
        else:
            comp_value = data_compare

        return sent_value == comp_value


