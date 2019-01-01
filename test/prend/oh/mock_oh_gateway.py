import copy
from collections import namedtuple
from prend.channel import Channel
from prend.oh.oh_gateway import OhGateway
from prend.state import State


class MockOhGateway(OhGateway):

    def __init__(self):
        super().__init__()

        self.sent_actions_list = []
        self.sent_actions_dict = {}
        self.mock_is_connected = True

    def send_queued(self):
        pass  # do nothing

    def send(self, send_command: bool, channel: Channel, state):
        SentAction = namedtuple('SentAction', ['channel', 'state', 'send_command'])

        sent_action = SentAction(copy.deepcopy(channel), copy.deepcopy(state), send_command)
        self.sent_actions_list.append(sent_action)
        self.sent_actions_dict[sent_action.channel] = sent_action

        super().send(send_command, channel, state)

    def is_connected(self):
        return self.mock_is_connected

    def set_state(self, channel_in: Channel, state_in: State):
        channel = copy.deepcopy(channel_in)
        state = copy.deepcopy(state_in)
        with self._lock_state:
            self._states[channel] = state

    def clear(self):
        self._send_queue.empty()
        self.sent_actions_list.clear()
        self.sent_actions_dict.clear()
        with self._lock_state:
            self._states.clear()

    def cache_states(self):
        # prepare chache in test setup
        pass

    def exists_sent_item(self, channel, state_expected) -> bool:
        sent_item = self.sent_actions_dict.get(channel)
        return state_expected == sent_item

