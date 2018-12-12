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
        if text:
            text = text.strip().upper()
            for e in OnOffValue:
                if e.name == text:
                    return e
        raise ValueError()


class ThingStatusValue(Enum):
    ONLINE = 1
    OFFLINE = 2
    INITIALIZING = 3

    def __str__(self):
        return self.__repr__()

    def __repr__(self) -> str:
        return '{}.{}'.format(self.__class__.__name__, self.name)

    @staticmethod
    def parse(text):
        if text:
            text = text.strip().upper()
            for e in ThingStatusValue:
                if e.name == text:
                    return e

        raise ValueError()


class UpDownValue(Enum):
    UP = 1
    DOWN = 2

    def __str__(self):
        return self.__repr__()

    def __repr__(self) -> str:
        return '{}.{}'.format(self.__class__.__name__, self.name)

    @staticmethod
    def parse(text):
        if text:
            text = text.strip().upper()
            for e in UpDownValue:
                if e.name == text:
                    return e

        raise ValueError()


