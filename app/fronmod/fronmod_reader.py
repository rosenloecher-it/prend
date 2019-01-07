from . import *
from .mobu import MobuBatch, MobuFlag, MobuItem, MobuResult
from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from pymodbus.payload import BinaryPayloadDecoder


class FronmodReader:

    def __init__(self, url, port):
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
            decoder = BinaryPayloadDecoder.fromRegisters(registers, byteorder=FronmodConfig.BYTEORDER)
        else:
            offset = read_item.offset
            if read_item.flags & MobuFlag.INT16:
                buffer = registers[offset:offset+1]
                decoder = BinaryPayloadDecoder.fromRegisters(buffer, byteorder=FronmodConfig.BYTEORDER)
            elif read_item.flags & MobuFlag.UINT16:
                buffer = registers[offset:offset + 1]
                decoder = BinaryPayloadDecoder.fromRegisters(buffer, byteorder=FronmodConfig.BYTEORDER)
            elif read_item.flags & MobuFlag.FLOAT32:
                buffer = registers[offset:offset+2]
                decoder = BinaryPayloadDecoder.fromRegisters(buffer, byteorder=FronmodConfig.BYTEORDER)
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

        result.ready = True
        return result

    def _read_remote_registers(self, read: MobuBatch):
        if self._client is None or not self.is_open():
            raise FronmodException('ModbusClient not open!')

        response = self._client.read_holding_registers(read.pos, read.length, unit=read.unit_id)
        if response.isError():
            raise FronmodException('read_holding_registers failed!')

        print('response.registers: ', response.registers)
        return response.registers

    def read(self, read: MobuBatch):
        registers = self._read_remote_registers(read)

        results = {}
        for item in read.items:
            if item.offset is not None:
                result = self._extract(item, registers)
                if results.get(item.name) is not None:
                    raise FronmodException('wrong configuration - duplicate read names!')
            else:
                result = MobuResult(item.name)  # empty result!

            result.item = item
            results[item.name] = result

        return results




