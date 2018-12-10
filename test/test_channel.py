import copy
import unittest
from prend.channel import Channel, ChannelType


class TestChannelType(unittest.TestCase):

    def test_parse(self):

        for e in ChannelType:
            parsed = ChannelType.parse(e.name)
            self.assertTrue(parsed == e)

            parsed = ChannelType.parse(' {} '.format(e.name.lower()))
            self.assertTrue(parsed == e)

            parsed = ChannelType.parse(' {} '.format(e.name.upper()))
            self.assertTrue(parsed == e)


class TestChannel(unittest.TestCase):

    def test_eq(self):
        orig = Channel()
        orig.type = ChannelType.GROUP
        orig.name = 'hgffc'

        comp = copy.deepcopy(orig)
        self.assertTrue(orig == comp)

        comp = copy.deepcopy(orig)
        comp.type = ChannelType.ITEM
        self.assertTrue(orig != comp)

        comp = copy.deepcopy(orig)
        comp.name = orig.name + '2'
        self.assertTrue(orig != comp)

    def test_is_valid(self):
        channel = Channel.create(ChannelType.ITEM, 'dummyNumber')
        out = channel.is_valid()
        self.assertTrue(out)

        channel = Channel()
        channel.type = None
        channel.name = 'dummyNumber'
        out = channel.is_valid()
        self.assertFalse(out)

        channel = Channel()
        channel.type = ChannelType.ITEM
        channel.name = None
        out = channel.is_valid()
        self.assertFalse(out)


