from enum import IntFlag
from typing import Optional


class MobuFlag(IntFlag):
    NONE = 0
    INT16 = 0x01
    UINT16 = 0x02
    FLOAT32 = 0x04
    STRING8 = 0x08
    Q_QUICK = 0x10  # 10s
    Q_MEDIUM = 0x40  # 60s
    Q_SLOW = 0x80  # 300s

    def __str__(self):
        return self.__repr__()

    def __repr__(self) -> str:
        return self.name


class MobuItem:
    def __init__(self, docu_offset: Optional[int], flags: MobuFlag, name: str, lambda_convert=None):
        if docu_offset is not None and docu_offset > 0:
            self.offset = docu_offset - 1  # fronius start position are not 0 terminated
        else:
            self.offset = docu_offset
        self.flags = flags
        self.name = name
        self.lambda_convert = lambda_convert

    def __repr__(self) -> str:
        return '{}({},{})'.format(self.__class__.__name__, self.name
                                  , hex(self.flags) if self.flags is not None else 'None')


class MobuBatch:
    def __init__(self, unit_id: int, pos: int, length: int, items: list):
        self.unit_id = unit_id
        self.pos = pos
        self.length = length
        self.items = items

    def __repr__(self) -> str:
        return '{}({},{},{})'.format(self.__class__.__name__, self.unit_id, self.pos, self.items)

    def __hash__(self):
        return hash((self.unit_id, self.pos, self.length))


class MobuResult:
    def __init__(self, name: str, value=None):
        self.name = name
        self.value = value
        self.item = None
        self.ready = False

    def __repr__(self) -> str:
        return '{}({},{})'.format(self.__class__.__name__, self.name, self.value)
