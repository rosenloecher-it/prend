import unittest
from test.app.fronstor.mock_requester import MockRequester


class TestRequester(unittest.TestCase):

    def test_loadRequestFileNotFound(self):
        hit_exception = False
        req = MockRequester()
        try:
            req.set_json_filename('request_file_not_found.non_json')
            req.request()
        except FileNotFoundError:
            hit_exception = True
        self.assertTrue(hit_exception)

    def test_loadRequestNonValid(self):
        hit_exception = False
        req = MockRequester()
        req.set_json_filename('request_invalid.non_json')
        try:
            req.request()
        except ValueError:
            hit_exception = True
        self.assertTrue(hit_exception)

    def test_loadRequestOff(self):
        req = MockRequester()
        req.set_json_filename('request_off.json')
        self.assertTrue(req.exists_json_path())
        json = req.request()
        print('test_loadRequestOff:', json)
        self.assertTrue(True)

    def test_loadRequestSuccess(self):
        req = MockRequester()
        req.set_json_filename('request_success.json')
        self.assertTrue(req.exists_json_path())
        self.assertTrue(True)

    def test_loadRequestReal(self):
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()
