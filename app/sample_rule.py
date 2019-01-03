import datetime
import logging
import schedule
from prend.channel import Channel, ChannelType
from prend.oh.oh_send_data import OhSendFlags
from prend.rule import Rule


_logger = logging.getLogger(__name__)


# inherit for Rule to get all
class SampleRule(Rule):

    CRON_NAME = 'cron_name_1'

    # openhab item names
    ITEM_DUMMY_1 = 'dummy_number'
    ITEM_DUMMY_2 = 'dummy_number_2'
    ITEM_STRING = 'dummy_string'
    ITEM_SWITCH = 'dummy_switch'

    # (overwriten) register your notifications and do some initialisation
    def register_actions(self) -> None:
        _logger.debug('register_actions')

        # _logger.info('show config: {}'.format(self._config))
        # better access config via self.get_config*

        # create cron job - syntax see https://github.com/dbader/schedule
        cron_job = schedule.every().minute
        # choose a cron name to recognize several cron jobs
        self.subscribe_cron_actions(self.CRON_NAME, cron_job)

        # create channel object and subscribe for changes
        channel = Channel.create(ChannelType.ITEM, self.ITEM_DUMMY_1)
        self.subscribe_channel_actions(channel)

        # create channel obect and subscribe for changes
        channel = Channel.create(ChannelType.ITEM, self.ITEM_SWITCH)
        self.subscribe_channel_actions(channel)

        # state changes for things
        # channel = Channel.create(ChannelType.THING, 'uid')
        # self.subscribe_openhab_actions(channel)

    # all notification will be sent here
    def notify_action(self, action) -> None:

        # check for general connection to openhab
        if not self.is_connected():
            _logger.debug('notify_action - NOT CONNECTED - %s', action)
        else:
            _logger.debug('notify_action - %s', action)

            # get item state
            dummy_number = self.get_item_state_value(self.ITEM_DUMMY_1)

            if dummy_number is None:
                dummy_number = 1
                self.send(OhSendFlags.COMMAND | OhSendFlags.CHANNEL_AS_ITEM, self.ITEM_DUMMY_1, dummy_number)

            dummy_number_2 = dummy_number
            if dummy_number % 5 == 0:
                dummy_number_2 = None

            self.send(OhSendFlags.COMMAND | OhSendFlags.CHANNEL_AS_ITEM, self.ITEM_DUMMY_2, dummy_number_2)

            # send another command
            text = '{} ({})'.format(dummy_number, datetime.datetime.now().isoformat())
            self.send(OhSendFlags.COMMAND | OhSendFlags.CHANNEL_AS_ITEM, self.ITEM_STRING, text)

        # in general: see "State" for values and "Channel" for channels of items + things

