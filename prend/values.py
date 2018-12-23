import logging
from abc import ABC, abstractmethod
from enum import Enum


_logger = logging.getLogger(__name__)


class FormatToJson(ABC):
    @abstractmethod
    def format_to_json(self) -> str:
        """format value to json string
        """
        pass


class OnOffValue(Enum):

    ON = 1
    OFF = 2

    def __str__(self):
        return self.__repr__()

    def __repr__(self) -> str:
        return '{}.{}'.format(self.__class__.__name__, self.name)

    def format_to_json(self) -> str:
        return self.name

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

    def format_to_json(self) -> str:
        return self.name

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

    def format_to_json(self) -> str:
        return self.name

    @staticmethod
    def parse(text):
        if text:
            text = text.strip().upper()
            for e in UpDownValue:
                if e.name == text:
                    return e

        raise ValueError()


class HsbValue(FormatToJson):

    def __init__(self, hue, saturation, brightness):
        self.hue = self.convert(hue)
        self.saturation = self.convert(saturation)
        self.brightness = self.convert(brightness)

    def __repr__(self) -> str:
        return '{}(h={},s={},b={})'.format(self.__class__.__name__, self.hue, self.saturation, self.brightness)

    def __eq__(self, other) -> bool:
        if not other:
            return False
        if type(self) != type(other):
            return False
        if self.hue != other.hue:
            return False
        if self.saturation != other.saturation:
            return False
        if self.brightness != other.brightness:
            return False
        return True

    def is_on(self):
        if self.brightness is None or self.brightness < 0:
            raise ValueError()
        if self.brightness > 0:
            return True
        return False

    def format_to_json(self) -> str:
        return '{},{},{}'.format(int(self.hue), int(self.saturation), int(self.brightness))

    @staticmethod
    def convert(value):
        return int(float(value) + 0.5)

    @staticmethod
    def parse(text):
        text = text.strip()

        parts = text.split(',')
        if len(parts) != 3:
            raise ValueError()

        value = HsbValue(parts[0], parts[1], parts[2])
        return value


class OpeningValue(Enum):

    CLOSED = 1
    TILTED = 2
    OPEN = 3

    def __str__(self):
        return self.__repr__()

    def __repr__(self) -> str:
        return '{}.{}'.format(self.__class__.__name__, self.name)

    def format_to_json(self) -> str:
        return self.name

    @staticmethod
    def parse(text):
        if text:
            text = text.strip().upper()
            for e in OpeningValue:
                if e.name == text:
                    return e
        raise ValueError()

