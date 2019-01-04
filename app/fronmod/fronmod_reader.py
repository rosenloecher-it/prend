from enum import IntFlag
from .fronmod_exception import FronmodException
from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder


class MobuFlag(IntFlag):
    INT16 = 0x01
    UINT16 = 0x02
    FLOAT32 = 0x04
    STRING8 = 0x08
    RAW = 0x10

    def __str__(self):
        return self.__repr__()

    def __repr__(self) -> str:
        return self.name


class MobuItem:
    def __init__(self, docu_offset: int, flags: MobuFlag, name: str, lambda_convert=None):
        if docu_offset > 0:
            self.offset = docu_offset - 1  # fronius start position are not 0 terminated
        else:
            self.offset = 0
        self.flags = flags
        self.name = name
        self.lambda_convert = lambda_convert

    def __repr__(self) -> str:
        return '{}({},{})'.format(self.__class__.__name__, self.name
                                  , hex(self.flags) if self.flags is not None else 'None')


class MobuBulk:
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

    def __repr__(self) -> str:
        return '{}({},{})'.format(self.__class__.__name__, self.name, self.value)


class FronmodReader:
    BYTEORDER = Endian.Big

    def __init__(self, url: str, port: int):
        self._client = None
        self._url = url
        self._port = port

    def open(self):
        self._client = ModbusClient(self._url, port=self._port)
        self._client.connect()

    def is_open(self) -> bool:
        if self._client is None:
            return False
        if not self._client.is_socket_open():
            return False
        return True

    def close(self):
        if self._client:
            self._client.close()
            self._client = None

    def _extract(self, read_item: MobuItem, registers):
        if read_item.offset == 0:
            buffer = registers
            decoder = BinaryPayloadDecoder.fromRegisters(registers, byteorder=self.BYTEORDER)
        else:
            offset = read_item.offset
            if read_item.flags & MobuFlag.INT16:
                buffer = registers[offset:offset+1]
                decoder = BinaryPayloadDecoder.fromRegisters(buffer, byteorder=self.BYTEORDER)
            elif read_item.flags & MobuFlag.UINT16:
                buffer = registers[offset:offset + 1]
                decoder = BinaryPayloadDecoder.fromRegisters(buffer, byteorder=self.BYTEORDER)
            elif read_item.flags & MobuFlag.FLOAT32:
                buffer = registers[offset:offset+2]
                decoder = BinaryPayloadDecoder.fromRegisters(buffer, byteorder=self.BYTEORDER)
            else:
                decoder = None  # error

        result = MobuResult(read_item.name)

        if read_item.flags & MobuFlag.INT16:
            result.value = decoder.decode_16bit_int()
        elif read_item.flags & MobuFlag.UINT16:
            result.value = decoder.decode_16bit_uint()
        elif read_item.flags & MobuFlag.FLOAT32:
            result.value = decoder.decode_32bit_float()
        elif read_item.flags & MobuFlag.STRING8:
            raise NotImplementedError()
        else:
            raise ValueError()

        return result

    def _read_remote_registers(self, read: MobuBulk):
        if self._client is None or not self.is_open():
            raise FronmodException('ModbusClient not open!')

        response = self._client.read_holding_registers(read.pos, read.length, unit=read.unit_id)
        if response.isError():
            raise FronmodException('read_holding_registers failed!')

        print('response.registers: ', response.registers)
        return response.registers

    def read(self, read: MobuBulk):
        registers = self._read_remote_registers(read)

        results = {}
        for item in read.items:
            result = self._extract(item, registers)
            if results.get(item.name) is not None:
                raise FronmodException('wrong configuration - duplicate read names!')
            results[item.name] = result

        return results




