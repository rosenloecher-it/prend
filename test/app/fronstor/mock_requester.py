import errno
import json
import os
from app.fronstor.fronstor_requester import FronstorRequesterBase


class MockRequester(FronstorRequesterBase):

    def set_json_filename(self, filename):
        path_test = os.path.dirname(os.path.abspath(__file__))
        self.jsonPath = os.path.join(path_test, 'json', filename)

    def get_json_path(self):
        return self.jsonPath

    def exists_json_path(self):
        check = os.path.isfile(self.jsonPath)
        if not check:
            print(self.jsonPath)
        return check

    def request(self):
        # print('jsonPath', self.jsonPath)
        if not os.path.isfile(self.jsonPath):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), self.jsonPath)
        with open(self.jsonPath) as f:
            json_data = json.load(f)
        # print(jsonData)
        return json_data

