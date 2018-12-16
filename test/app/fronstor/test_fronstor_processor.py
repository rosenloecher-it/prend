import unittest
from app.fronstor.fronstor_constants import FronstorConstants
from app.fronstor.fronstor_extracter import FronstorExtracter
from app.fronstor.fronstor_processor import FronstorProcessor
from prend.channel import Channel
from prend.state import State, StateType
from test.app.fronstor.mock_requester import MockRequester
from test.prend.oh.mock_oh_gateway import MockOhGateway


class TestFronstorProcessor(unittest.TestCase):

    def setUp(self):

        self.dispatcher = None

        self.mock_gateway = MockOhGateway()
        self.mock_gateway.set_dispatcher(self.dispatcher)

        self.requester = MockRequester()
        self.extracter = FronstorExtracter()

        self.processor = FronstorProcessor()
        self.processor.set_oh_gateway(self.mock_gateway)
        self.processor.set_requester(self.requester)
        self.processor.set_extracter(self.extracter)

    def set_item_state(self, channel_name, state_type, value):
        self.mock_gateway.set_state(Channel.create_item(channel_name)
                                    , State.create(state_type, value))

    def prepare_oh_gateway(self, empty):
        self.mock_gateway.clear()

        default_decimal = None
        default_string = None

        if not empty:
            default_decimal = -9.999
            default_string = 'to_overwrite'

        self.set_item_state(FronstorConstants.ITEM_INV_TEMP, StateType.DECIMAL, default_decimal)
        self.set_item_state(FronstorConstants.ITEM_BAT_TEMP_MAX, StateType.DECIMAL, default_decimal)
        self.set_item_state(FronstorConstants.ITEM_BAT_CYCLE_SPAN, StateType.STRING, default_string)

        for i in range(0, FronstorConstants.ITEM_BAT_COUNT):
            name = FronstorConstants.ITEM_BAT_TEMP_FORMAT.format(i + 1)
            self.set_item_state(name, StateType.DECIMAL, default_decimal)

            name = FronstorConstants.ITEM_BAT_CYCLE_FORMAT.format(i + 1)
            self.set_item_state(name, StateType.DECIMAL, default_decimal)

    def check_sent_item(self, item_name, state_type_expected, value_expected):

        channel = Channel.create_item(item_name)
        sent_item = self.mock_gateway.sent_actions_dict.get(channel)
        self.assertTrue(sent_item)

        self.assertEqual(sent_item.state.type, state_type_expected)
        self.assertEqual(sent_item.state.value, value_expected)

    def test_off_no_change(self):
        self.processor.check_requirements()
        self.requester.set_json_filename('request_off.json')

        self.prepare_oh_gateway(empty=True)
        self.processor.run()
        self.assertEqual(len(self.mock_gateway.sent_actions_list), 0)

    def test_off_send_changes(self):
        self.processor.check_requirements()
        self.requester.set_json_filename('request_off.json')

        self.prepare_oh_gateway(empty=False)
        self.processor.run()

        # print('len(self.mock_gateway.sent_actions_list)=', len(self.mock_gateway.sent_actions_list))
        # print('len(self.mock_gateway.sent_actions_dict)=', len(self.mock_gateway.sent_actions_dict))
        # print(self.mock_gateway.sent_actions_list)

        self.assertEqual(len(self.mock_gateway.sent_actions_list), 6)
        self.assertEqual(len(self.mock_gateway.sent_actions_dict), 6)
        self.check_sent_item(FronstorConstants.ITEM_INV_TEMP, StateType.DECIMAL, None)
        self.check_sent_item(FronstorConstants.ITEM_BAT_TEMP_MAX, StateType.DECIMAL, None)
        for i in range(0, FronstorConstants.ITEM_BAT_COUNT):
            name = FronstorConstants.ITEM_BAT_TEMP_FORMAT.format(i + 1)
            self.check_sent_item(name, StateType.DECIMAL, None)

    def test_success_send_changes(self):
        self.processor.check_requirements()
        self.requester.set_json_filename('request_success.json')

        self.prepare_oh_gateway(empty=True)
        self.processor.run()

        # print('len(self.mock_gateway.sent_actions_list)=', len(self.mock_gateway.sent_actions_list))
        # print('len(self.mock_gateway.sent_actions_dict)=', len(self.mock_gateway.sent_actions_dict))
        # print(self.mock_gateway.sent_actions_list)

        self.assertEqual(len(self.mock_gateway.sent_actions_list), 11)
        self.assertEqual(len(self.mock_gateway.sent_actions_dict), 11)
        self.check_sent_item(FronstorConstants.ITEM_INV_TEMP, StateType.DECIMAL, 26.150000000000034)
        self.check_sent_item(FronstorConstants.ITEM_BAT_TEMP_MAX, StateType.DECIMAL, 27.450000000000045)
        self.check_sent_item(FronstorConstants.ITEM_BAT_CYCLE_SPAN, StateType.STRING, '310-312')

        comp_temps = [27.450000000000045, 27.450000000000045, 27.05000000000001, 26.25]
        comp_cycles = [311, 311, 312, 310]

        for i in range(0, FronstorConstants.ITEM_BAT_COUNT):
            name = FronstorConstants.ITEM_BAT_TEMP_FORMAT.format(i + 1)
            self.check_sent_item(name, StateType.DECIMAL, comp_temps[i])

            name = FronstorConstants.ITEM_BAT_CYCLE_FORMAT.format(i + 1)
            self.check_sent_item(name, StateType.DECIMAL, comp_cycles[i])


if __name__ == '__main__':
    unittest.main()
