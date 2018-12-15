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
        pass

    def set_requester(self, requester):
        self._requester = requester

    def set_extracter(self, extracter):
        self._extracter = extracter

    def open(self):
        super().open()

        if not self._requester:
            self._requester = FronstorRequester()
        if not self._extracter:
            self._extracter = FronstorExtracter()

        url = self.get_config('fronstor', 'url')
        self._requester.set_url(url)

    def register_actions(self) -> None:
        cron_job = schedule.every(5).minutes
        self.subscribe_cron_actions(self.__class__.__name__, cron_job)

        channel = Channel.create_startup()
        self.subscribe_channel_actions(channel)

    def notify_action(self, action) -> None:
        try:
            # check for general connection to openhab
            if not self.is_connected():
                _logger.debug('notify_action - NOT CONNECTED - abort')
                return

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
        self._processor.set_extracter(self._extracter)
        self._processor.set_oh_gateway(self._oh_gateway)
        self._processor.set_requester(self._requester)

        self._processor.start()





