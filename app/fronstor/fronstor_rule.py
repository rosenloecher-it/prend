import datetime
import logging
import schedule
from prend.channel import Channel
from prend.rule import Rule
from .fronstor_requester import FronstorRequester
from .fronstor_extracter import FronstorExtracter
from .fronstor_processor import FronstorProcessor
from .fronstor_exception import FronstorException


_logger = logging.getLogger(__name__)


class FronstorRule(Rule):

    def __init__(self):
        super().__init__()
        self._requester = None
        self._extracter = None
        self._processor = None
        self._processor_config = None
        pass

    def set_requester(self, requester):
        self._requester = requester

    def set_extracter(self, extracter):
        self._extracter = extracter

    def open(self):

        if not self._requester:
            self._requester = FronstorRequester()
        if not self._extracter:
            self._extracter = FronstorExtracter()

    def register_actions(self) -> None:
        cron_job = schedule.every().minute
        self.subscribe_cron_actions(self.__class__.__name__, cron_job)

        self.subscribe_channel_actions(Channel.create_startup())

    def notify_action(self, action) -> None:
        try:
            # check for general connection to openhab
            if not self.is_connected():
                _logger.debug('notify_action - NOT CONNECTED - abort')
                return

            # todo config

            # todo time measurment
            _logger.debug('notify_action - %s', action)

            self._start_processor()

        except FronstorException as ex:
            _logger.error('notify_action failed - %s', ex)

    def _start_processor(self):

        if self._processor:
            if not self._processor.is_alive():
                self._processor.shutdown()
                self._processor = None

        if self._processor:
            raise FronstorException('processor is still running!')

        self._processor = FronstorProcessor()
        self._processor.set_requester(self._requester)
        self._processor.set_extracter(self._extracter)
        self._processor.set_oh_gateway(self._oh_gateway)

        self._processor.start()




