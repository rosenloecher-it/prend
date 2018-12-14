import unittest
from app.fronstor.fronstor_extracter import FronstorExtracter, FronstorStatus
from test.app.fronstor.mock_requester import MockRequester
from test.app.fronstor.mock_openhab import MockOpenhab
from app.fronstor.fronstor_constants import FronstorConstants
from app.fronstor.fronstor_rule import FronstorRule

class TestExtracter(unittest.TestCase):

    def setUp(self):

        self.rule = FronstorRule()

        self.requester = MockRequester()
        self.extracter = FronstorExtracter()

        self.rule.set_requester(self.requester)
        self.rule.set_extracter(self.extracter)

        self.rule.open()

#    def test_loadRequestFileNotFound(self):
#        hitException = False
#
#        try:
#            self.requester.setJsonFileName('request_file_not_found.non_json')
#            self.processor.process()
#        except FileNotFoundError:
#            hitException = True
#
#        self.assertTrue(hitException)
#
#
#
#    def test_loadRequestNonValid(self):
#        hitException = False
#
#        try:
#            self.requester.setJsonFileName('request_invalid.non_json')
#            self.processor.process()
#        except FileNotFoundError:
#            hitException = True
#
#        self.assertTrue(hitException)

    def test_off(self):
        self.openhab.clear()
        self.requester.set_json_filename('request_off.json')
        self.processor.process()

        result = self.processor.get_last_extract()
        self.assertEqual(result.status, FronstorStatus.OFF)



    def test_success(self):
        self.openhab.clear()
        self.requester.set_json_filename('request_success.json')
        self.processor.process()

        result = self.processor.get_last_extract()
        self.assertEqual(result.status, FronstorStatus.SUCCESS)

        print('result', result)

        comp_temps = [27.450000000000045, 27.450000000000045, 27.05000000000001, 26.25]
        comp_cycles = [311, 311, 312, 310]

        for i in range(0, FronstorConstants.ITEM_BAT_COUNT):
            itemName = FronstorConstants.ITEM_BAT_CYCLE_FORMAT.format(i + 1)
            self.assertEqual(comp_cycles[i], result.values[itemName])

            itemName = FronstorConstants.ITEM_BAT_TEMP_FORMAT.format(i + 1)
            self.assertEqual(comp_temps[i], result.values[itemName])

        self.assertEqual(result.values[FronstorConstants.ITEM_BAT_CYCLE_SPAN], '310-312')
        self.assertEqual(result.values[FronstorConstants.ITEM_INV_TEMP], 26.150000000000034)



if __name__ == '__main__':
    unittest.main()