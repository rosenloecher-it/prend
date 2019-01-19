import logging
import schedule
from . import *
from prend.channel import Channel, ChannelType
from prend.oh.oh_send_data import OhSendFlags, OhSendData
from prend.rule import Rule


_logger = logging.getLogger(__name__)


class FronmodRule(Rule):

    CRON_FETCH_QUICK = 'CRON_FETCH_QUICK'
    CRON_FETCH_MEDIUM = 'CRON_FETCH_MEDIUM'
    CRON_FETCH_SLOW = 'CRON_FETCH_SLOW'

    CRON_SENT_QUICK = 'CRON_SENT_QUICK'
    CRON_SENT_MEDIUM = 'CRON_SENT_MEDIUM'
    CRON_SENT_SLOW = 'CRON_SENT_SLOW'

    def __init__(self):
        super().__init__()
        self._is_open = False
        self._processor = None
        self._reader = None
        pass

    def open(self):
        url = self.get_config('fronmod', 'url')
        if not url:
            _logger.warning('no url => disable!')
            return
        try:
            port_text = self.get_config('fronmod', 'port')
            port = int(port_text)
        except (ValueError, TypeError):
            _logger.error('no port => disable!')
            return

        self._reader = FronmodReader(url, port)
        self._reader.open()

        self._processor = FronmodProcessor()
        self._processor.set_reader(self._reader)

        super().open()
        self._is_open = True

    def close(self):
        if self._is_open:
            self.reset_items()

        self._is_open = False
        self._processor = None
        if self._reader:
            self._reader.close()
            self._reader = None

        super().close()

    def reset_items(self):
        _logger.debug('reset_items')
        flags = OhSendFlags.UPDATE | OhSendFlags.CHANNEL_AS_ITEM | OhSendFlags.SKIP_CHANNEL_CHECK
        for item_name in FronmodConfig.RESET_ITEM_LIST:
            data = OhSendData(flags, item_name, None)
            self._oh_gateway.send_data(data)

    def register_actions(self) -> None:
        cron_job = schedule.every(5).seconds
        self.subscribe_cron_actions(self.CRON_FETCH_QUICK, cron_job)

        # cron_job = schedule.every(15).seconds
        # self.subscribe_cron_actions(self.CRON_FETCH_MEDIUM, cron_job)

        cron_job = schedule.every(60).seconds
        self.subscribe_cron_actions(self.CRON_FETCH_SLOW, cron_job)

        cron_job = schedule.every(10).seconds
        self.subscribe_cron_actions(self.CRON_SENT_QUICK, cron_job)

        cron_job = schedule.every(60).seconds
        self.subscribe_cron_actions(self.CRON_SENT_MEDIUM, cron_job)

        cron_job = schedule.every(300).seconds
        self.subscribe_cron_actions(self.CRON_SENT_SLOW, cron_job)

        channel = Channel.create_startup()
        self.subscribe_channel_actions(channel)

    def notify_action(self, action) -> None:
        try:
            if not self._is_open:
                _logger.debug('not opened => abort')
                return

            # # check for general connection to openhab
            # if not self.is_connected():
            #     _logger.debug('notify_action - NOT CONNECTED - abort')
            #     return

            if ChannelType.CRON == action.channel.type:
                if self.CRON_FETCH_QUICK == action.channel.name:
                    self.handle_cron_fetch_quick()
                elif self.CRON_FETCH_SLOW == action.channel.name:
                    self.handle_cron_fetch_slow()
                elif self.CRON_SENT_QUICK == action.channel.name:
                    self.handle_cron_send(MobuFlag.Q_QUICK)
                elif self.CRON_SENT_MEDIUM == action.channel.name:
                    self.handle_cron_send(MobuFlag.Q_MEDIUM)
                elif self.CRON_SENT_SLOW == action.channel.name:
                    self.handle_cron_send(MobuFlag.Q_SLOW)

            # _logger.debug('notify_action - %s', action)
            # self._start_processor()

        except FronmodException as ex:
            _logger.error('notify_action failed - %s', ex)

    def handle_cron_fetch_quick(self):
        self._processor.process_inverter_model()  # must be first
        self._processor.process_mppt_model()
        self._processor.process_meter_model()

    def handle_cron_fetch_medium(self):
        pass

    def handle_cron_fetch_slow(self):
        self._processor.process_storage_model()

    def handle_cron_send(self, flags):
        send_data_list = self._processor.get_send_data(flags)
        for send_data in send_data_list:
            self._oh_gateway.send_data(send_data)

