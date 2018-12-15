import logging
import threading
from prend.channel import Channel, ChannelType
from .fronstor_exception import FronstorException
from .fronstor_extracter import FronstorStatus


_logger = logging.getLogger(__name__)


class FronstorProcessor(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self._oh_gateway = None
        self._extracter = None
        self._requester = None

    def set_oh_gateway(self, oh_gateway):
        self._oh_gateway = oh_gateway
        pass

    def set_requester(self, requester):
        self._requester = requester

    def set_extracter(self, extracter):
        self._extracter = extracter

    def shutdown(self):
        pass

    def check_requirements(self):
        if not self._oh_gateway:
            raise FronstorException('no _oh_gateway!')
        if not self._extracter:
            raise FronstorException('no _extracter!')
        if not self._requester:
            raise FronstorException('no _requester!')

    def start(self):
        self.check_requirements()
        super().start()

    def run(self):
        try:
            _logger.debug('run - start query %s', self._requester.get_url())

            json = self._requester.request()
            last_extract = self._extracter.extract(json)
            if last_extract.status == FronstorStatus.SUCCESS:
                self.send_values(last_extract.values)

            _logger.debug('run - success')

        except FronstorException as ex:
            _logger.error('run failed - %s', ex)
        except Exception as ex:
            _logger.exception(ex)
        # todo catch request erros

    def send_values(self, values):

        class ItemData:
            def __init__(self):
                self.channel = None
                self.state = None
                pass
        items = []

        for key, new_value in values.items():
            item = ItemData()
            item.channel = Channel.create_item(key)
            item.state = self._oh_gateway.get_state(item.channel)
            if not item.state:
                raise FronstorException('openhab state ({}) not found!'.format(item.channel))
            if item.state.value == new_value:
                _logger.debug('found equal values: item (%s) - current=%s == new=%s => skip'
                              , key, item.state.value, new_value)
                continue
            if not item.state.set_value_check_type(new_value):
                raise FronstorException('cannot set state ({}) not found!'.format(item.channel))
            items.append(item)

        for item in items:
            # logging is done in OhRest
            self._oh_gateway.send_command(item.channel, item.state)
