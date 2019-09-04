import unittest
from prend.oh.oh_event import OhEvent, OhNotificationType


class TestOhEvent(unittest.TestCase):

    def test_repr(self):
        # no crash!
        event = OhEvent.create_empty()
        print(event)

    def test_is_valid(self):
        event = OhEvent()

        event.notification_type = OhNotificationType.IGNORE
        self.assertTrue(not event.is_valid())

        event.notification_type = OhNotificationType.RELOAD
        self.assertTrue(event.is_valid())


class TestOhNotificationType(unittest.TestCase):

    def check_parse(self, type_expected, list_types):
        for text in list_types:
            out = OhNotificationType.parse(text)
            self.assertEqual(out, type_expected)

    def test_parse(self):
        self.check_parse(OhNotificationType.ITEM_CHANGE, ['ItemStateEvent'])
        self.check_parse(OhNotificationType.ITEM_CHANGE, ['ItemStateChangedEvent'])

        self.check_parse(OhNotificationType.GROUP_CHANGE, ['GroupItemStateChangedEvent'])

        self.check_parse(OhNotificationType.ITEM_COMMAND, ['ItemCommandEvent'])

        self.check_parse(OhNotificationType.THING_CHANGE, ['ThingStatusInfoEvent', 'ThingStatusInfoChangedEvent'])

        reload_types = ['ItemAddedEvent', 'ItemRemovedEvent', 'ItemUpdatedEvent', 'ThingAddedEvent',
                        'ThingRemovedEvent', 'ThingUpdatedEvent']
        self.check_parse(OhNotificationType.RELOAD, reload_types)

    def test_str(self):
        self.assertEqual(str(OhNotificationType.ITEM_CHANGE), 'ITEM_CHANGE')


if __name__ == '__main__':
    unittest.main()
