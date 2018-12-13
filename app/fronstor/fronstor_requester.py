import requests
import json
from abc import ABC, abstractmethod


class FronstorRequesterBase(ABC):

    @abstractmethod
    def request(self):
        pass


class FronstorRequester(FronstorRequesterBase):

    def __init__(self, url = None):
        super().__init__()
        self._url = url


    def request(self):
        req = requests.get(self._url)
        json_data = json.loads(req.text)
        return json_data

