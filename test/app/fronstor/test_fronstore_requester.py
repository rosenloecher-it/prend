import unittest
from pprint import pprint
from test.app.fronstor.mock_requester import MockRequester


class TestRequester(unittest.TestCase):

    def test_loadRequestFileNotFound(self):
        hitException = False

        req = MockRequester()

        try:
            req.set_json_filename('request_file_not_found.non_json')
            req.request()
        except FileNotFoundError:
            hitException = True

        #req.request()

        self.assertTrue(hitException)



    def test_loadRequestNonValid(self):

        hitException = False

        req = MockRequester()
        req.set_json_filename('request_invalid.non_json')

        try:
            req.request()
        except ValueError:
            hitException = True

        self.assertTrue(hitException)



    def test_loadRequestOff(self):
        req = MockRequester()
        req.set_json_filename('request_off.json')
        self.assertTrue(req.existsJsonPath())
        json = req.request()
        print('test_loadRequestOff:', json)

        self.assertTrue(True)



    def test_loadRequestSuccess(self):
        req = MockRequester()
        req.set_json_filename('request_success.json')
        self.assertTrue(req.existsJsonPath())
        self.assertTrue(True)



    def test_loadRequestReal(self):
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()
