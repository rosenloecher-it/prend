import datetime

import pytz
import requests
import unittest
from prend.channel import Channel, ChannelType
from prend.oh.oh_event import OhEvent, OhNotificationType
from prend.oh.oh_gateway import OhGatewayEventSink
from prend.oh.oh_rest import OhRest
from prend.oh.oh_send_data import OhSendData, OhSendFlags
from prend.state import State, StateType
from prend.values import OnOffValue, ThingStatusValue
from test.setup_test import SetupTest


class TestEventSink(OhGatewayEventSink):
    def __init__(self):
        self.list = []

    def push_event(self, event: OhEvent) -> None:
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
        rest = OhRest(SetupTest.get_config())
        time_start_loading = datetime.datetime.now()

        # test item
        # noinspection PyPep8
        json_data = {'link': 'http://127.0.0.1:8080/rest/items/dummySwitch', 'state': 'ON', 'editable': False, 'type': 'Switch', 'name': 'dummySwitch', 'category': 'settings', 'tags': [], 'groupNames': []}  # noqa
        ev_out = rest._fetch_item(time_start_loading, json_data)
        channel = Channel.create(ChannelType.ITEM, 'dummySwitch')
        state = State.create(StateType.SWITCH, OnOffValue.ON)
        ev_cmp = OhEvent.create(OhNotificationType.ITEM_CHANGE, channel, state)
        self.check_fetch_event(ev_out, ev_cmp)

        # test groups
        # noinspection PyPep8
        json_data = {'members': [], 'link': 'http://homeserver:8080/rest/items/gMarc', 'state': 'NULL', 'editable': False, 'type': 'Group', 'name': 'gMarc', 'label': 'Zimmer Marc', 'category': 'boy_1', 'tags': [], 'groupNames': []}  # noqa
        ev_out = rest._fetch_item(time_start_loading, json_data)
        channel = Channel.create(ChannelType.GROUP, 'gMarc')
        state = State.create(StateType.GROUP, None)
        ev_cmp = OhEvent.create(OhNotificationType.GROUP_CHANGE, channel, state)
        self.check_fetch_event(ev_out, ev_cmp)

        # noinspection PyPep8
        json_data = {'members': [], 'groupType': 'Rollershutter', 'function': {'name': 'EQUALITY'}, 'link': 'http://homeserver:8080/rest/items/gShutter', 'state': '0', 'editable': False, 'type': 'Group', 'name': 'gShutter', 'label': 'Alle Rollläden', 'category': 'rollershutter-50', 'tags': [], 'groupNames': []}  # noqa
        ev_out = rest._fetch_item(time_start_loading, json_data)
        channel = Channel.create(ChannelType.GROUP, 'gShutter')
        state = State.create(StateType.GROUP, '0')
        ev_cmp = OhEvent.create(OhNotificationType.GROUP_CHANGE, channel, state)
        self.check_fetch_event(ev_out, ev_cmp)

    def test_fetch_thing(self):
        rest = OhRest(SetupTest.get_config())
        time_start_loading = datetime.datetime.now()

        # noinspection PyPep8
        json_data = {'statusInfo': {'status': 'ONLINE', 'statusDetail': 'NONE'}, 'editable': False, 'label': 'Homematic Bridge', 'configuration': {'cuxdPort': 8701, 'socketMaxAlive': 900, 'installModeDuration': 60, 'reconnectInterval': 3600, 'timeout': 15, 'hmIpPort': 2010, 'discoveryTimeToLive': -1, 'wiredPort': 2000, 'gatewayType': 'ccu', 'callbackHost': '127.0.0.1', 'groupPort': 9292, 'gatewayAddress': '127.0.0.1', 'unpairOnDeletion': False, 'rfPort': 2001}, 'properties': {'serialNumber': 'NEQ1327832', 'firmwareVersion': '2.29.23.20171118', 'modelId': 'CCU2'}, 'UID': 'homematic:bridge:rhm', 'thingTypeUID': 'homematic:bridge', 'channels': []}  # noqa
        ev_out = rest._fetch_thing(time_start_loading, json_data)
        channel = Channel.create(ChannelType.THING, 'homematic:bridge:rhm')
        state = State.create(StateType.THING_STATUS, ThingStatusValue.ONLINE)
        ev_cmp = OhEvent.create(OhNotificationType.THING_CHANGE, channel, state)
        self.check_fetch_event(ev_out, ev_cmp)

    def test_format_for_request(self):
        test_time = datetime.datetime(2020, 8, 9, 15, 5, 1, 234111, tzinfo=pytz.utc)
        out = OhRest.format_for_request(test_time)
        print(out)
        self.assertEqual(b'2020-08-09T15:05:01.234+0000', out)

        out = OhRest.format_for_request(123)
        print(out)
        self.assertEqual(b'123', out)

        out = OhRest.format_for_request(1.23)
        print(out)
        self.assertEqual(b'1.23', out)

        out = OhRest.format_for_request('abc')
        print(out)
        self.assertEqual(b'abc', out)

        out = OhRest.format_for_request('3,4°C / 56%')
        print(out)
        self.assertEqual(b'3,4\xc2\xb0C / 56%', out)

    def test_send_change_command_to_update(self):
        class MockOhRest(OhRest):
            def __init__(self):
                super().__init__(SetupTest.get_config())
                self.send_type = None
                pass

            def _req_post(self, uri_path: str, payload=None) -> None:
                self.send_type = 'post'

            def _req_put(self, uri_path: str, payload=None) -> None:
                self.send_type = 'put'

            def clear(self):
                self.send_type = None

        channel = Channel.create_item('abc')
        rest = MockOhRest()

        rest.clear()
        data = OhSendData(OhSendFlags.COMMAND, channel, 123)
        rest.send(data)
        self.assertEqual('post', rest.send_type)

        rest.clear()
        data = OhSendData(OhSendFlags.COMMAND, channel, None)
        rest.send(data)
        self.assertEqual('put', rest.send_type)


if __name__ == '__main__':
    unittest.main()
