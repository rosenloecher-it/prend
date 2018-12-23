import copy
import unittest
from prend.action import Action
from prend.channel import Channel, ChannelType
from prend.config import Config
from prend.dispatcher import DispatcherActionSink
from prend.oh.oh_event import OhEvent, OhNotificationType
from prend.oh.oh_gateway import OhGateway, SendData
from prend.oh.oh_rest import OhRest
from prend.state import State, StateType
from prend.values import OnOffValue, ThingStatusValue
from test.prend.oh.mock_oh_gateway import MockOhGateway


class MockRest(OhRest):
    def __init__(self):
        super().__init__(Config())
        self.dummy_events = []
        self.dummy_send = []

    def fetch_all(self):
        events = copy.deepcopy(self.dummy_events)
        return events

    def send(self, send_command: bool, channel: Channel, state_in):
        send_data = SendData()
        send_data.send_command = send_command
        send_data.channel = copy.deepcopy(channel)
        if state_in is None:
            send_data.state = None
        else:
            send_data.state = copy.deepcopy(state_in)
        self.dummy_send.append(send_data)


class MockDispatcher(DispatcherActionSink):
    def __init__(self):
        self.queued_actions = {}

    def push_action(self, root_action: Action) -> None:
        self.queued_actions[root_action.channel] = root_action


class TestOhGateway(unittest.TestCase):

    # pylint: disable:too-many-statements
    def test_fetch_items(self):
        dispatcher = MockDispatcher()
        rest = MockRest()
        gateway = OhGateway()
        gateway.set_dispatcher(dispatcher)
        gateway.set_rest(rest)

        # prepare rest
        ev_update = OhEvent.create(OhNotificationType.ITEM_CHANGE
                                   , Channel.create(ChannelType.ITEM, 'dummySwitch')
                                   , State.create(StateType.SWITCH, OnOffValue.ON))
        rest.dummy_events.append(ev_update)
        ev_dummy = OhEvent.create(OhNotificationType.GROUP_CHANGE
                                  , Channel.create(ChannelType.GROUP, 'gMarc')
                                  , State.create(StateType.GROUP, None))
        rest.dummy_events.append(ev_dummy)
        ev_dummy = OhEvent.create(OhNotificationType.GROUP_CHANGE
                                  , Channel.create(ChannelType.GROUP, 'gShutter')
                                  , State.create(StateType.GROUP, '0'))
        rest.dummy_events.append(ev_dummy)
        ev_dummy = OhEvent.create(OhNotificationType.THING_CHANGE
                                  , Channel.create(ChannelType.THING, 'homematic:bridge:rhm')
                                  , State.create(StateType.THING_STATUS, ThingStatusValue.ONLINE))
        rest.dummy_events.append(ev_dummy)

        ev_dummy = OhEvent.create(OhNotificationType.ITEM_CHANGE
                                  , Channel.create(ChannelType.ITEM, 'to_be_remove')
                                  , State.create(StateType.SWITCH, OnOffValue.ON))
        gateway.push_event(ev_dummy)

        states_comp = gateway.get_states()
        self.assertEqual(1, len(states_comp))
        self.assertEqual(1, len(dispatcher.queued_actions))
        dispatcher.queued_actions.clear()

        gateway.cache_states()
        states_comp = gateway.get_states()

        self.assertEqual(len(rest.dummy_events), len(states_comp))
        # find a
        for event_r in rest.dummy_events:
            state_g = states_comp.get(event_r.channel)
            self.assertTrue(state_g is not None)
            equal1 = (event_r.state == state_g)
            state_g2 = gateway.get_state(event_r.channel)
            equal2 = (event_r.state == state_g2)
            if not equal1 or not equal2:
                print('event_r.state == state_g:\n    state_src: {}\n    state_out: {}')
                self.assertEqual(state_g, event_r.state)
            del states_comp[event_r.channel]
        self.assertEqual(0, len(states_comp))

        self.assertEqual(len(rest.dummy_events), len(dispatcher.queued_actions))
        states_comp = dispatcher.queued_actions
        for event_r in rest.dummy_events:
            queued_action = dispatcher.queued_actions.get(event_r.channel)
            self.assertTrue(queued_action is not None)
            equal = (event_r.state == queued_action.state_new)
            if not equal:
                print('event_r.state == queued_action.state_new:\n    state_src: {}\n    state_out: {}')
                self.assertEqual(queued_action.state_new, event_r.state)
            del dispatcher.queued_actions[event_r.channel]
        self.assertEqual(0, len(states_comp))

        dispatcher.queued_actions.clear()
        ev_update.state.value = OnOffValue.OFF
        ev_update.state.update_last_change()
        gateway.push_event(ev_update)
        state_g3 = gateway.get_state(ev_update.channel)
        self.assertEqual(ev_update.state, state_g3)
        self.assertEqual(1, len(dispatcher.queued_actions))
        dispatcher.queued_actions.clear()
        gateway.push_event(ev_update)
        self.assertEqual(0, len(dispatcher.queued_actions))  # no change

        ev_update.notification_type = OhNotificationType.ITEM_COMMAND
        dispatcher.queued_actions.clear()
        gateway.push_event(ev_update)
        self.assertEqual(1, len(dispatcher.queued_actions))

    def test_get_states(self):

        gateway = MockOhGateway()
        check_channels = []

        channel1 = Channel.create_item('ch1')
        state1 = State.create(StateType.STRING, channel1.name)
        gateway.set_state(channel1, state1)
        check_channels.append(channel1)

        channel2 = Channel.create_item('ch2')
        state2 = State.create(StateType.STRING, channel2.name)
        gateway.set_state(channel2, state2)
        check_channels.append(channel2)

        states = gateway.get_states()
        self.assertEqual(state1, states.get(channel1))
        self.assertEqual(state2, states.get(channel2))

        channels = gateway.get_channels()
        for channel in channels:
            found = check_channels.index(channel)
            check_channels.remove(channel)

        self.assertEqual(0, len(check_channels))

    def test_send(self):

        comp_list = []
        rest = MockRest()
        gateway = OhGateway()
        gateway.set_rest(rest)

        send_data = SendData()
        send_data.send_command = True
        send_data.channel = Channel.create(ChannelType.ITEM, 'test1-send_command')
        send_data.state = State.create(StateType.STRING, send_data.channel.name)
        comp_list.append(send_data)
        gateway.send_command(send_data.channel, send_data.state)

        send_data = SendData()
        send_data.send_command = False
        send_data.channel = Channel.create(ChannelType.ITEM, 'test2-send_update')
        send_data.state = State.create(StateType.STRING, send_data.channel.name)
        comp_list.append(send_data)
        gateway.send_update(send_data.channel, send_data.state)

        send_data = SendData()
        send_data.send_command = True
        send_data.channel = Channel.create(ChannelType.ITEM, 'test3-send_item_command')
        send_data.state = State.create(StateType.STRING, send_data.channel.name)
        comp_list.append(send_data)
        gateway.send_item_command(send_data.channel.name, send_data.state)

        send_data = SendData()
        send_data.send_command = False
        send_data.channel = Channel.create(ChannelType.ITEM, 'test4-send_item_update')
        send_data.state = State.create(StateType.STRING, send_data.channel.name)
        comp_list.append(send_data)
        gateway.send_item_update(send_data.channel.name, send_data.state)

        send_data = SendData()
        send_data.send_command = False
        send_data.channel = Channel.create(ChannelType.ITEM, 'test5-send_item_update(None)')
        send_data.state = None
        comp_list.append(send_data)
        gateway.send_item_update(send_data.channel.name, send_data.state)

        gateway.send_queued()

        self.assertEqual(len(comp_list), len(rest.dummy_send))

        for i in range(0, len(comp_list)):
            sent = rest.dummy_send[i]
            comp = comp_list[i]

            self.assertEqual(comp.send_command, sent.send_command)
            self.assertEqual(comp.channel, sent.channel)
            self.assertEqual(comp.state, sent.state)

