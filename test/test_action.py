import copy
import unittest
from prend.action import Action
from prend.channel import Channel, ChannelType
from prend.oh.oh_event import OhNotificationType
from prend.state import State, StateType


class TestOhAction(unittest.TestCase):

    def test_repr(self):
        # no crash
        action = Action()
        print(action)

    def test_eq(self):
        orig = Action()
        orig.channel = Channel.create(ChannelType.ITEM, 'channel')
        orig.state_old = State.create(StateType.DECIMAL, 2.2)
        orig.state_new = State.create(StateType.DECIMAL, 4.4)
        orig.notification_type = OhNotificationType.ITEM_COMMAND

        comp = copy.deepcopy(orig)
        self.assertTrue(orig == comp)

        self.assertTrue(orig is not None)
        self.assertTrue(orig != 1)

        comp = copy.deepcopy(orig)
        orig.channel = Channel.create(ChannelType.ITEM, 'channel2')
        self.assertTrue(orig != comp)

        comp = copy.deepcopy(orig)
        orig.state_old = State.create(StateType.DECIMAL, 2.23)
        self.assertTrue(orig != comp)

        comp = copy.deepcopy(orig)
        orig.state_new = State.create(StateType.DECIMAL, 2.23)
        self.assertTrue(orig != comp)

        comp = copy.deepcopy(orig)
        orig.notification_type = OhNotificationType.ITEM_CHANGE
        self.assertTrue(orig != comp)

    def test_should_be_published(self):
        orig = Action()
        orig.channel = Channel.create(ChannelType.ITEM, 'channel')
        orig.state_old = State.create(StateType.DECIMAL, 2.2)
        orig.state_new = State.create(StateType.DECIMAL, 2.2)
        orig.notification_type = OhNotificationType.ITEM_CHANGE

        comp = copy.deepcopy(orig)
        out = comp.should_be_published()
        self.assertFalse(out)

        comp = copy.deepcopy(orig)
        comp.notification_type = OhNotificationType.ITEM_COMMAND
        out = comp.should_be_published()
        self.assertTrue(out)

        comp = copy.deepcopy(orig)
        comp.state_new = State.create(StateType.DECIMAL, 2.3)
        out = comp.should_be_published()
        self.assertTrue(out)

        comp = copy.deepcopy(orig)
        comp.channel = Channel.create(ChannelType.CRON, 'channel')
        out = comp.should_be_published()
        self.assertTrue(out)

    def test_is_valid(self):
        orig = Action()
        orig.channel = Channel.create(ChannelType.ITEM, 'channel')
        orig.state_old = State.create(StateType.DECIMAL, 2.2)
        orig.state_new = State.create(StateType.DECIMAL, 2.2)
        orig.notification_type = OhNotificationType.ITEM_CHANGE

        cron = Action()
        cron.channel = Channel.create(ChannelType.CRON, 'channel')
        cron.state_old = None
        cron.state_new = None
        cron.notification_type = None

        comp = copy.deepcopy(orig)
        out = comp.is_valid()
        self.assertTrue(out)

        comp = copy.deepcopy(orig)
        comp.state_old = None
        out = comp.is_valid()
        self.assertTrue(out)

        comp = copy.deepcopy(cron)
        out = comp.is_valid()
        self.assertTrue(out)

        comp = copy.deepcopy(orig)
        comp.channel.name = None
        out = comp.is_valid()
        self.assertFalse(out)

        comp = copy.deepcopy(orig)
        comp.state_new = None
        out = comp.is_valid()
        self.assertFalse(out)

        comp = copy.deepcopy(orig)
        comp.notification_type = None
        out = comp.is_valid()
        self.assertFalse(out)




