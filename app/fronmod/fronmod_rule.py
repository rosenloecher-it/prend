import logging
import schedule
from prend.channel import Channel
from prend.rule import Rule
from .fronmod_exception import FronmodException


_logger = logging.getLogger(__name__)


class FronmodRule(Rule):

    def __init__(self):
        super().__init__()
        self._is_open = False
        pass

    def open(self):
        url = self.get_config('fronmod', 'url')
        if not url:
            _logger.warning('no url => disable!')
            return

        super().open()
        self._is_open = True

    def register_actions(self) -> None:
        cron_job = schedule.every(5).minutes
        self.subscribe_cron_actions(self.__class__.__name__, cron_job)

        channel = Channel.create_startup()
        self.subscribe_channel_actions(channel)

    def notify_action(self, action) -> None:
        try:
            if not self._is_open:
                _logger.debug('not opened => abort')
                return

            # check for general connection to openhab
            if not self.is_connected():
                _logger.debug('notify_action - NOT CONNECTED - abort')
                return

            # _logger.debug('notify_action - %s', action)
            # self._start_processor()

        except FronmodException as ex:
            _logger.error('notify_action failed - %s', ex)


