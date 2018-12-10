from enum import Enum
import logging


_logger = logging.getLogger(__name__)


class OnOffValue(Enum):
    ON = 1
    OFF = 2

    def __str__(self):
        return self.__repr__()

    def __repr__(self) -> str:
        return '{}.{}'.format(self.__class__.__name__, self.name)

    @staticmethod
    def parse(text):
        result = None

        if text:
            text = text.strip().upper()
            for e in OnOffValue:
                if e.name == text:
                    result = e
                    break

        return result


class OnlineOfflineValue(Enum):
    ONLINE = 1
    OFFLINE = 2

    def __str__(self):
        return self.__repr__()

    def __repr__(self) -> str:
        return '{}.{}'.format(self.__class__.__name__, self.name)

    @staticmethod
    def parse(text):
        result = None

        if text:
            text = text.strip().upper()
            for e in OnlineOfflineValue:
                if e.name == text:
                    result = e
                    break

        return result
