import datetime
import logging
import schedule
from prend.channel import Channel, ChannelType
from prend.rule import Rule


_logger = logging.getLogger(__name__)


# inherit for Rule to get all
class SampleRule(Rule):

    # (overwriten) register your notifications and do some initialisation
    def register_actions(self) -> None:
        _logger.info('register_actions')

        # _logger.info('show config: {}'.format(self._config))
        # better access confif via self.get_config*

        # create cron job - syntax see https://github.com/dbader/schedule
        cron_job = schedule.every().minute
        # choose a cron name to recognize several cron jobs
        self.subscribe_cron_actions('cron_name_1', cron_job)

        # create channel object and subscribe for changes
        channel = Channel.create(ChannelType.ITEM, 'dummy_number')
        self.subscribe_openhab_actions(channel)

        # create channel obect and subscribe for changes
        channel = Channel.create(ChannelType.ITEM, 'dummy_switch')
        self.subscribe_openhab_actions(channel)

        # state changes for things
        # channel = Channel.create(ChannelType.THING, 'uid')
        # self.subscribe_openhab_actions(channel)

    # all notification will be sent here
    def notify_action(self, action) -> None:

        # check for general connection to openhab
        if not self.is_connected():
            _logger.info('notify_action - NOT CONNECTED - %s', action)
        else:
            _logger.info('notify_action - %s', action)

            # get item state
            dummy_number = self.get_item_state_value('dummy_number')

            if dummy_number is None:
                dummy_number = 1
                self.send_item_command('dummy_number', dummy_number)

            # send command to another item (there is also a "send_item_update")
            self.send_item_command('dummy_number_2', dummy_number)

            # send another command
            text = '{} ({})'.format(dummy_number, datetime.datetime.now().isoformat())
            self.send_item_command('dummy_string', text)

        # in general: see "State" for values and "Channel" for channels of items + things

