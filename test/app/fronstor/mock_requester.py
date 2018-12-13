import os
import errno
import json
import pprint
from app.fronstor.fronstor_requester import FronstorRequesterBase


class MockRequester(FronstorRequesterBase):

    def set_json_filename(self, filename):
        pathTest = os.path.dirname(os.path.abspath(__file__))
        self.jsonPath = os.path.join(pathTest, 'json', filename)


    def getJsonPath(self):
        return self.jsonPath



    def existsJsonPath(self):
        check = os.path.isfile(self.jsonPath)
        if not check:
            print(self.jsonPath)
        return check


    def request(self):

        jsonData = None

        #print('jsonPath', self.jsonPath)
        if (not os.path.isfile(self.jsonPath)):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), self.jsonPath)

        with open(self.jsonPath) as f:
            jsonData = json.load(f)

        #print(jsonData)

        return jsonData

