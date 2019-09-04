import unittest
from prend.config import Config
from prend.channel import Channel, ChannelType
from prend.oh.oh_event import OhEvent, OhNotificationType
from prend.oh.oh_gateway import OhGatewayEventSink
from prend.oh.oh_observer import OhObserver
from prend.state import State, StateType


class TestEventSink(OhGatewayEventSink):
    def __init__(self):
        self.list = []

    def push_event(self, event: OhEvent) -> None:
        self.list.append(event)


class MockNotificationEvent:
    def __init__(self, data):
        self.data = data


class TestOhObserver(unittest.TestCase):

    def setUp(self):
        self.event_sink = TestEventSink()
        self.observer = OhObserver(Config(), self.event_sink)

    def check_handle_event(self, str_in, ev_cmp):
        self.event_sink.list.clear()

        self.observer._handle_event(MockNotificationEvent(str_in))

        if not ev_cmp:
            self.assertEqual(len(self.event_sink.list), 0)
        else:
            self.assertEqual(len(self.event_sink.list), 1)
            ev_out = self.event_sink.list[0]
            if ev_cmp != ev_out:
                self.assertEqual(ev_cmp, ev_out)

    def test_handle_event_default(self):

        # {"topic":"smarthome/items/valSockMeasPower/state","payload":"{\"type\":\"Decimal\",\"value\":\"109.01\"}","type":"ItemStateEvent"}
        # noinspection PyPep8
        str_in = '{"topic":"smarthome/items/valSockMeasPower/state","payload":"{\\\"type\\\":\\\"Decimal\\\",\\\"value\\\":\\\"109.01\\\"}","type":"ItemStateEvent"}'  # noqa
        oh_channel = Channel.create(ChannelType.ITEM, 'valSockMeasPower')
        oh_state = State.create(StateType.DECIMAL, 109.01)
        ev_cmp = OhEvent.create(OhNotificationType.ITEM_CHANGE, oh_channel, oh_state)
        self.check_handle_event(str_in, ev_cmp)

    def test_handle_event_invalid(self):
        # exception will occur, but should be catched! no crash!
        self.check_handle_event('invalid event!', None)

        self.check_handle_event(None, None)

    def test_handle_event_ignore(self):
        str_in = '{"topic":"xxx","type":"FirmwareStatusInfoEvent"}'
        self.check_handle_event(str_in, None)


# todo
# self.check_parse(OhNotificationType.RELOAD,
#                 ['ItemAddedEvent', 'ItemRemovedEvent', 'ItemUpdatedEvent'
#                     , 'ThingAddedEvent', 'ThingRemovedEvent', 'ThingUpdatedEvent'])
