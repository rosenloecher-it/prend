import requests
import unittest
from prend.config import Config
from prend.channel import Channel, ChannelType
from prend.oh.oh_event import OhEvent, OhNotificationType
from prend.oh.oh_gateway import OhGatewayEventSink
from prend.oh.oh_rest import OhRest
from prend.state import State, StateType
from prend.values import OnOffValue, ThingStatusValue
import datetime


class TestEventSink(OhGatewayEventSink):
    def __init__(self):
        self.list = []

    def queue_event(self, event: OhEvent) -> None:
        self.list.append(event)


class TestOhRest(unittest.TestCase):

    # from test.setup_test import SetupTest
    # def manual_test_fetch_items(self):
    #     config = SetupTest.get_config()
    #
    #     events = None
    #     with OhRest(config) as ohRest:
    #         events = ohRest.fetch_items()
    #
    #     for event in events:
    #         print('items/groups: ', event)
    #
    # def manual_test_fetch_things(self):
    #     config = SetupTest.get_config()
    #
    #     events = None
    #     with OhRest(config) as ohRest:
    #         events = ohRest.fetch_things()
    #
    #     for event in events:
    #         print('things: ', event)

    # noinspection PyBroadException
    # pylint: disable=protected-access
    def check_check_req_return(self, expected_result: bool, req):
        try:
            OhRest._check_req_return(req)
            result = True
        except Exception:
            result = False
        self.assertEqual(expected_result, result)

    def test_check_req_return(self):

        req = requests.Response()

        self.check_check_req_return(False, None)

        self.check_check_req_return(False, req)

        req.status_code = 200
        self.check_check_req_return(True, req)
        req.status_code = 299
        self.check_check_req_return(True, req)

        req.status_code = 400
        self.check_check_req_return(False, req)

    def check_fetch_event(self, ev_out, ev_cmp):
        result = (ev_cmp == ev_out)
        if not result:
            print('check_oh_event failed with\n    out: {}\n    cmp: {}'.format(ev_out, ev_cmp))
        self.assertTrue(result)

    # pylint: disable=line-too-long, protected-access
    def test_fetch_item(self):
        rest = OhRest(Config())
        time_start_loading = datetime.datetime.now()

        # test item
        # noinspection PyPep8
        json_data = {'link': 'http://127.0.0.1:8080/rest/items/dummySwitch', 'state': 'ON', 'editable': False, 'type': 'Switch', 'name': 'dummySwitch', 'category': 'settings', 'tags': [], 'groupNames': []}
        ev_out = rest._fetch_item(time_start_loading, json_data)
        channel = Channel.create(ChannelType.ITEM, 'dummySwitch')
        state = State.create(StateType.SWITCH, OnOffValue.ON)
        ev_cmp = OhEvent.create(OhNotificationType.ITEM_CHANGE, channel, state)
        self.check_fetch_event(ev_out, ev_cmp)

        # test groups
        # noinspection PyPep8
        json_data = {'members': [], 'link': 'http://homeserver:8080/rest/items/gMarc', 'state': 'NULL', 'editable': False, 'type': 'Group', 'name': 'gMarc', 'label': 'Zimmer Marc', 'category': 'boy_1', 'tags': [], 'groupNames': []}
        ev_out = rest._fetch_item(time_start_loading, json_data)
        channel = Channel.create(ChannelType.GROUP, 'gMarc')
        state = State.create(StateType.GROUP, None)
        ev_cmp = OhEvent.create(OhNotificationType.GROUP_CHANGE, channel, state)
        self.check_fetch_event(ev_out, ev_cmp)

        # noinspection PyPep8
        json_data = {'members': [], 'groupType': 'Rollershutter', 'function': {'name': 'EQUALITY'}, 'link': 'http://homeserver:8080/rest/items/gShutter', 'state': '0', 'editable': False, 'type': 'Group', 'name': 'gShutter', 'label': 'Alle Rollläden', 'category': 'rollershutter-50', 'tags': [], 'groupNames': []}
        ev_out = rest._fetch_item(time_start_loading, json_data)
        channel = Channel.create(ChannelType.GROUP, 'gShutter')
        state = State.create(StateType.GROUP, '0')
        ev_cmp = OhEvent.create(OhNotificationType.GROUP_CHANGE, channel, state)
        self.check_fetch_event(ev_out, ev_cmp)

    def test_fetch_thing(self):
        rest = OhRest(Config())
        time_start_loading = datetime.datetime.now()

        # noinspection PyPep8
        json_data = {'statusInfo': {'status': 'ONLINE', 'statusDetail': 'NONE'}, 'editable': False, 'label': 'Homematic Bridge', 'configuration': {'cuxdPort': 8701, 'socketMaxAlive': 900, 'installModeDuration': 60, 'reconnectInterval': 3600, 'timeout': 15, 'hmIpPort': 2010, 'discoveryTimeToLive': -1, 'wiredPort': 2000, 'gatewayType': 'ccu', 'callbackHost': '127.0.0.1', 'groupPort': 9292, 'gatewayAddress': '127.0.0.1', 'unpairOnDeletion': False, 'rfPort': 2001}, 'properties': {'serialNumber': 'NEQ1327832', 'firmwareVersion': '2.29.23.20171118', 'modelId': 'CCU2'}, 'UID': 'homematic:bridge:rhm', 'thingTypeUID': 'homematic:bridge', 'channels': []}
        ev_out = rest._fetch_thing(time_start_loading, json_data)
        channel = Channel.create(ChannelType.THING, 'homematic:bridge:rhm')
        state = State.create(StateType.THING_STATUS, ThingStatusValue.ONLINE)
        ev_cmp = OhEvent.create(OhNotificationType.THING_CHANGE, channel, state)
        self.check_fetch_event(ev_out, ev_cmp)


if __name__ == '__main__':
    unittest.main()


