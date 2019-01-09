import datetime
import logging
import requests
import threading
import typing
from .oh_event import OhEvent, OhIllegalEventException
from .oh_send_data import OhSendData
from prend.channel import ChannelType
from prend.config import Config
from prend.state import State
from requests.auth import HTTPBasicAuth
from typing import Optional


"""
see also: python-openhab: https://github.com/sim0nx/python-openhab
"""


_logger = logging.getLogger(__name__)


class OhRestException(Exception):
    pass


class OhRest:
    def __init__(self, config: Config):
        self._rest_base_url = config.oh_rest_base_url
        if not self._rest_base_url:
            raise OhRestException('no openhab url!')
        self._username = config.oh_username
        self._password = config.oh_password
        self._simulate_sending = config.oh_simulate_sending
        self._timeout = config.timeout or None
        self._session = None
        self._lock_session = threading.Lock()

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *args):
        self.close()

    def open(self):
        with self._lock_session:
            self._session = requests.Session()
            self._session.headers['accept'] = 'application/json'
            if self._username:
                self._session.auth = HTTPBasicAuth(self._username, self._password)

    def close(self):
        with self._lock_session:
            if self._session:
                self._session.close()
                self._session = None

    def fetch_all(self):
        events = []
        self.fetch_items(events)
        self.fetch_things(events)
        return events

    def fetch_items(self, events: list) -> None:
        time_start_loading = datetime.datetime.now()
        res = self._req_get('/items/')
        for json_data in res:
            event = self._fetch_item(time_start_loading, json_data)
            if event:
                events.append(event)

    @staticmethod
    def _fetch_item(time_start_loading, json_data) -> Optional[OhEvent]:
        try:
            # _logger.info(json_data)
            channel_type = None
            type_string = json_data['type']
            if type_string:
                type_string = type_string.strip().upper()
                channel_type = ChannelType.ITEM
                if type_string == 'GROUP':
                    channel_type = ChannelType.GROUP

            if channel_type in [ChannelType.ITEM, ChannelType.GROUP]:
                event = OhEvent.create_from_state_json(json_data, channel_type)
            else:
                raise OhRestException('unknown item type({})!'.format(type_string))

            if not event.is_valid():
                raise OhIllegalEventException(event)

            event.state.last_change = time_start_loading
            return event

        except Exception as ex:
            _logger.exception(ex)
            _logger.error('faulty item/group json:\n%s', json_data)
            return None

    def fetch_things(self, events: list) -> None:
        time_start_loading = datetime.datetime.now()
        res = self._req_get('/things/')
        for json_data in res:
            event = self._fetch_thing(time_start_loading, json_data)
            if event:
                events.append(event)

    @staticmethod
    def _fetch_thing(time_start_loading, json_data) -> Optional[OhEvent]:
        try:
            # _logger.info(json_data)
            event = OhEvent.create_from_thing_json(json_data)
            if not event.is_valid():
                raise OhIllegalEventException(event)

            event.state.last_change = time_start_loading
            return event
        except Exception as ex:
            _logger.exception(ex)
            _logger.error('faulty thing json:\n%s', json_data)
            return None

    @staticmethod
    def _check_req_return(req: requests.Response) -> None:
        if not (200 <= req.status_code < 300):
            req.raise_for_status()

    def send(self, data: OhSendData):

        if data is None:
            raise ValueError()
        data.check()  # raise *

        channel = data.get_channel()
        value_state = data.get_state_value()

        send_command = data.is_send()
        if data.is_send() and value_state is None:
            _logger.warning('cannot send None/UNDEF via COMMAND => use UPDATE instead!')
            # noinspection PyUnusedLocal
            send_command = False

        item_name = channel.name
        value_json = self.format_for_request(value_state)

        if send_command:
            url = '/items/{}'.format(item_name)
            if self._simulate_sending:
                _logger.info('SIMULATE post command: "%s" = %s', url, value_json)
            else:
                _logger.info('send POST COMMAND: "%s" = %s', url, value_json)
                self._req_post(url, payload=value_json)
        else:
            url = '/items/{}/state'.format(item_name)
            if self._simulate_sending:
                _logger.info('SIMULATE put update: "%s" = %s', url, value_json)
            else:
                _logger.info('send PUT UPDATE: "%s" = %s', url, value_json)
                self._req_put(url, payload=value_json)

    def _req_get(self, uri_path: str) -> typing.Any:
        with self._lock_session:
            req = self._session.get(self._rest_base_url + uri_path, timeout=self._timeout)
            self._check_req_return(req)
            return req.json()

    def _req_post(self, uri_path: str, payload=None) -> None:
        with self._lock_session:
            req = self._session.post(self._rest_base_url + uri_path, data=payload, timeout=self._timeout)
            self._check_req_return(req)

    def _req_put(self, uri_path: str, payload=None) -> None:
        with self._lock_session:
            req = self._session.put(self._rest_base_url + uri_path, data=payload, timeout=self._timeout)
            self._check_req_return(req)

    @staticmethod
    def format_for_request(value_in) -> str:
        text_out = State.convert_to_json(value_in)
        text_out = text_out.encode('utf-8')
        return text_out
