import errno
import json
import os
from app.fronstor.fronstor_requester import FronstorRequesterBase


class MockRequester(FronstorRequesterBase):

    def __init__(self):
        super().__init__()
        self.json_path = None

    def set_json_filename(self, filename):
        path_test = os.path.dirname(os.path.abspath(__file__))
        self.json_path = os.path.join(path_test, 'json', filename)

    def get_json_path(self):
        return self.json_path

    def exists_json_path(self):
        check = os.path.isfile(self.json_path)
        if not check:
            print(self.json_path)
        return check

    def request(self):
        # print('jsonPath', self.jsonPath)
        if not os.path.isfile(self.json_path):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), self.json_path)
        with open(self.json_path) as f:
            json_data = json.load(f)
        # print(jsonData)
        return json_data

