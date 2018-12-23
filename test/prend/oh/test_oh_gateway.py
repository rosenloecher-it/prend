import copy
import unittest
from prend.action import Action
from prend.channel import Channel, ChannelType
from prend.config import Config
from prend.dispatcher import DispatcherActionSink
from prend.oh.oh_event import OhEvent, OhNotificationType
from prend.oh.oh_gateway import OhGateway
from prend.oh.oh_rest import OhRest
from prend.state import State, StateType
from prend.values import OnOffValue, ThingStatusValue
from test.prend.oh.mock_oh_gateway import MockOhGateway


class TestRest(OhRest):
    def __init__(self):
        super().__init__(Config())
        self.dummy_events = []

    def fetch_all(self):
        events = copy.deepcopy(self.dummy_events)
        return events


class TestDispatcher(DispatcherActionSink):
    def __init__(self):
        self.queued_actions = {}

    def push_action(self, root_action: Action) -> None:
        self.queued_actions[root_action.channel] = root_action


class TestOhGateway(unittest.TestCase):

    # pylint: disable:too-many-statements
    def test_fetch_items(self):
        dispatcher = TestDispatcher()
        rest = TestRest()
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


