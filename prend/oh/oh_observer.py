import aiohttp
import asyncio
import json
import logging
import threading
from aiosseclient import Event
from prend.config import Config
from prend.oh.oh_event import OhEvent, OhNotificationType
from random import randint


"""
aiosseclient for for OpenHAB notifications
    Asynchronous Server Side Events (SSE) Client
    https://github.com/ebraminio/aiosseclient
"""


_logger = logging.getLogger(__name__)


class OhObserverException(Exception):
    pass


class OhObserver(threading.Thread):

    def __init__(self, config: Config, gateway):
        threading.Thread.__init__(self)
        self._rest_base_url = config.oh_rest_base_url
        self._username = config.oh_username
        self._password = config.oh_password
        self._event_loop = None
        self._gateway = gateway

    def _handle_event(self, event_in) -> None:
        if not event_in or not event_in.data:
            _logger.error('invalid event (None)')
            return

        try:
            event_out = OhEvent.create_from_notify_json(event_in.data)

            if event_out.notification_type == OhNotificationType.IGNORE:
                pass
            elif event_out.is_valid():
                self._gateway.push_event(event_out)
                # _logger.debug('event queued: %s', event_out)
            else:
                raise OhObserverException('invalid event!')

        except json.decoder.JSONDecodeError:
            _logger.error('cannot parse faulty json: %s', event_in.data)
        except Exception as ex:
            _logger.exception(ex)
            _logger.error('cannot parse faulty json: %s', event_in.data)

    # copied from aiosseclient.aiosseclient - to set timeout
    @staticmethod
    async def _aiosseclient(url, last_id, **kwargs):
        if 'headers' not in kwargs:
            kwargs['headers'] = {}

        # The SSE spec requires making requests with Cache-Control: nocache
        kwargs['headers']['Cache-Control'] = 'no-cache'

        # The 'Accept' header is not required, but explicit > implicit
        kwargs['headers']['Accept'] = 'text/event-stream'

        if last_id:
            kwargs['headers']['Last-Event-ID'] = last_id

        one_year_in_seconds = 365*24*60*60

        try:
            async with aiohttp.ClientSession(read_timeout=one_year_in_seconds) as session:
                response = await session.get(url, **kwargs)
                lines = []
                async for line in response.content:
                    line = line.decode('utf8')

                    if line == '\n' or line == '\r' or line == '\r\n':
                        if lines[0] == ':ok\n':
                            lines = []
                            continue

                        yield Event.parse(''.join(lines))
                        lines = []
                    else:
                        lines.append(line)
        except (
                aiohttp.client_exceptions.ClientError,
                asyncio.TimeoutError,
                ConnectionError
        ) as ex:
            _logger.error('exception _aiosseclient - %s: %s', ex.__class__.__name__, ex)
        except Exception as ex:
            _logger.error('exception _aiosseclient')
            _logger.exception(ex)
            raise

    async def _loop(self) -> None:
        last_id = '{}{}'.format(self.__class__.__name__, randint(0, 99999))

        try:

            url = '{}/events'.format(self._rest_base_url)
            _logger.debug('connecting to %s (id=%s)', url, last_id)

            async for event in self._aiosseclient(url, last_id):
                self._handle_event(event)

            # normally there was an exception in another thread
            _logger.debug('_loop - exiting "normally", but expected to run forever!')

        except (
                aiohttp.client_exceptions.ClientError,
                asyncio.TimeoutError,
                ConnectionError,
                TimeoutError
        ) as ex:
            _logger.error('_loop exiting - %s: %s', ex.__class__.__name__, ex)
        except Exception as ex:
            _logger.error('exception _loop')
            _logger.exception(ex)

    def shutdown(self) -> None:
        pass

    def is_connected(self):
        return self.is_alive()

    def run(self):

        event_loop = None
        try:
            event_loop = asyncio.new_event_loop()
            event_loop.run_until_complete(self._loop())

            # normally there was an exception in another thread
            _logger.debug('run - exiting "normally", but expected to run forever!')

        except (
                aiohttp.client_exceptions.ClientError,
                asyncio.TimeoutError,
                ConnectionError,
                TimeoutError
        ) as ex:
            _logger.error('run - %s: %s', ex.__class__.__name__, ex)
        except Exception as ex:
            _logger.error('run - %s: %s', ex.__class__.__name__, ex)
            _logger.exception(ex)
        finally:
            if event_loop:
                event_loop.close()
