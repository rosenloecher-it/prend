import schedule
import time
import unittest
from prend.action import Action
from prend.dispatcher import Dispatcher
from prend.channel import Channel, ChannelType
from prend.oh.oh_event import OhNotificationType
from prend.state import State, StateType
from prend.rule import Rule


class DispatchCheckerRule(Rule):

    def __init__(self, dispatcher):
        super().__init__()
        self._dispatcher = dispatcher
        self.notifications = []

    def register_actions(self) -> None:
        # not needed
        pass

    def clear_notifications(self):
        self.notifications.clear()

    def notify_action(self, action) -> None:
        self.notifications.append(action)


class TestDispatcher(unittest.TestCase):

    def test_dispatch_action(self):
        dispatcher = Dispatcher()
        checker = DispatchCheckerRule(dispatcher)

        channel = Channel.create(ChannelType.ITEM, 'dummyNumber')
        checker.subscribe_channel_actions(channel)

        action_in = Action()
        action_in.channel = channel
        action_in.state_new = State.create(StateType.DECIMAL, 3)
        action_in.notification_type = OhNotificationType.ITEM_COMMAND

        self.assertTrue(len(checker.notifications) == 0)
        something_processed = dispatcher.dispatch()
        self.assertFalse(something_processed)
        self.assertTrue(len(checker.notifications) == 0)

        dispatcher.push_action(action_in)
        something_processed = dispatcher.dispatch()
        self.assertTrue(something_processed)
        self.assertTrue(len(checker.notifications) == 1)

        action_out = checker.notifications[0]

        action_out.listener = None  # compare!
        compare = (action_in == action_out)
        self.assertTrue(compare)

    def test_dispatch_cron(self):
        dispatcher = Dispatcher()
        checker = DispatchCheckerRule(dispatcher)

        self.assertTrue(len(checker.notifications) == 0)
        something_processed = dispatcher.dispatch()
        self.assertFalse(something_processed)
        self.assertTrue(len(checker.notifications) == 0)

        cron_key = 'cron1'
        cron_job = schedule.every().second
        checker.subscribe_cron_actions(cron_key, cron_job)

        max_loop = 8
        while True:
            time.sleep(0.2)
            print('loop ({})'.format(max_loop))
            something_processed = dispatcher.dispatch_skip_cron(1)  # waid 1ms
            if something_processed:
                break
            if max_loop < 0:
                break
            max_loop -= 1
            time.sleep(0.2)

        self.assertTrue(something_processed)
        self.assertTrue(len(checker.notifications) >= 1)

        action_out = checker.notifications[0]
        print('test - action_out: ', action_out)
        action_out.listener = None  # compare!

        action_cmp = Action()
        action_cmp.channel = Channel.create(ChannelType.CRON, cron_key)
        compare = (action_cmp == action_out)
        self.assertTrue(compare)


if __name__ == '__main__':
    unittest.main()
