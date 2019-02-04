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

    CRON_SENT_MEDIUM = 'CRON_SENT_MEDIUM'
    CRON_SENT_SLOW = 'CRON_SENT_SLOW'

    CRON_RECONNECT = 'CRON_RECONNECT'

    def __init__(self):
        super().__init__()
        self._is_open = False
        self._processor = None
        self._reader = None
        self._url = None
        self._port = None
        self._quick_mode = 0
        self._error_counter = 0

    def open(self):
        self._url = self.get_config('fronmod', 'url')
        if not self._url:
            _logger.warning('no url => disable!')
            return

        try:
            port_text = self.get_config('fronmod', 'port')
            self._port = int(port_text)
        except (ValueError, TypeError):
            _logger.error('no port => disable!')
            return

        self._processor = FronmodProcessor()
        self._reconnect_reader()

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
        cron_job = schedule.every(2).seconds
        self.subscribe_cron_actions(self.CRON_FETCH_QUICK, cron_job)

        # cron_job = schedule.every(15).seconds
        # self.subscribe_cron_actions(self.CRON_FETCH_MEDIUM, cron_job)

        cron_job = schedule.every(60).to(65).seconds
        self.subscribe_cron_actions(self.CRON_FETCH_SLOW, cron_job)

        cron_job = schedule.every(55).to(65).seconds
        self.subscribe_cron_actions(self.CRON_SENT_MEDIUM, cron_job)

        cron_job = schedule.every(290).to(310).seconds
        self.subscribe_cron_actions(self.CRON_SENT_SLOW, cron_job)

        cron_job = schedule.every(390).to(410).seconds
        self.subscribe_cron_actions(self.CRON_RECONNECT, cron_job)

        channel = Channel.create_startup()
        self.subscribe_channel_actions(channel)

    def _reconnect_reader(self):
        if self._reader:
            self._reader.close()
            self._reader = None
            _logger.debug('_reconnect_reader')

        self._reader = FronmodReader(self._url, self._port)
        self._reader.open()
        self._processor.set_reader(self._reader)

        self._show_errors = True
        self._error_counter = 0
        self._processor.set_show_errors(self._show_errors)

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
                elif self.CRON_SENT_MEDIUM == action.channel.name:
                    self.handle_cron_send(MobuFlag.Q_MEDIUM)
                elif self.CRON_SENT_SLOW == action.channel.name:
                    self.handle_cron_send(MobuFlag.Q_SLOW)
                elif self.CRON_RECONNECT == action.channel.name:
                    self._reconnect_reader()

            # _logger.debug('notify_action - %s', action)
            # self._start_processor()

        except FronmodException as ex:
            if self._show_errors:
                _logger.error('notify_action failed - %s', ex)

            self._error_counter += 1
            if self._error_counter > 12:
                _logger.error('notify_action - suppress following errors until reconnect!')
                self._show_errors = False
                self._processor.set_show_errors(self._show_errors)

    def handle_cron_fetch_quick(self):

        if self._quick_mode == 1:  # :4s
            self._processor.process_inverter_model()  # must be first
        elif self._quick_mode == 2:  # :6s
            self._processor.process_mppt_model()
        elif self._quick_mode == 3:  # :8s
            self._processor.process_meter_model()
        elif self._quick_mode == 4:  # :10s
            self.handle_cron_send(MobuFlag.Q_QUICK)

        self._quick_mode += 1
        if self._quick_mode >= 5:
            self._quick_mode = 0

    def handle_cron_fetch_medium(self):
        pass

    def handle_cron_fetch_slow(self):
        self._processor.process_storage_model()

    def handle_cron_send(self, flags):
        send_data_list = self._processor.get_send_data(flags)
        for send_data in send_data_list:
            self._oh_gateway.send_data(send_data)

