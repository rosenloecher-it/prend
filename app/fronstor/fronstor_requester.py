import requests
import json
from abc import ABC, abstractmethod


class FronstorRequesterBase(ABC):

    def __init__(self):
        self._url = None

    @abstractmethod
    def request(self):
        pass

    def set_url(self, url: str):
        self._url = url

    def get_url(self):
        return self._url


class FronstorRequester(FronstorRequesterBase):

    def __init__(self, url=None):
        super().__init__()
        self._url = url

    def request(self):
        req = requests.get(self._url)
        json_data = json.loads(req.text)
        return json_data

