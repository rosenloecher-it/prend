from enum import Enum
from .fronmod_exception import FronmodException
from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder


class ModbusType(Enum):
    INT16 = 1
    UINT16 = 2
    FLOAT32 = 3
    STRING8 = 4

    def __str__(self):
        return self.__repr__()

    def __repr__(self) -> str:
        return self.name


class ModbusReadItem:
    def __init__(self, docu_offset: int, modbus_type: ModbusType, name: str, lambda_convert=None):
        if docu_offset > 0:
            self.offset = docu_offset - 1  # fronius start position are not 0 terminated
        else:
            self.offset = 0
        self.type = modbus_type
        self.name = name
        self.lambda_convert = lambda_convert

    def __repr__(self) -> str:
        return '{}({},{})'.format(self.__class__.__name__, self.name, self.type)


class ModbusRead:
    def __init__(self, unit_id: int, pos: int, length: int, items: list):
        self.unit_id = unit_id
        self.pos = pos
        self.length = length
        self.items = items

    def __repr__(self) -> str:
        return '{}({},{},{})'.format(self.__class__.__name__, self.unit_id, self.pos, self.items)

    def __hash__(self):
        return hash((self.unit_id, self.pos, self.length))


class ModbusResultItem:
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

    def _extract(self, read_item, registers):
        if read_item.offset == 0:
            buffer = registers
            decoder = BinaryPayloadDecoder.fromRegisters(registers, byteorder=self.BYTEORDER)
        else:
            offset = read_item.offset
            if read_item.type == ModbusType.INT16:
                buffer = registers[offset:offset+1]
                decoder = BinaryPayloadDecoder.fromRegisters(buffer, byteorder=self.BYTEORDER)
            elif read_item.type == ModbusType.UINT16:
                buffer = registers[offset:offset + 1]
                decoder = BinaryPayloadDecoder.fromRegisters(buffer, byteorder=self.BYTEORDER)
            elif read_item.type == ModbusType.FLOAT32:
                buffer = registers[offset:offset+2]
                decoder = BinaryPayloadDecoder.fromRegisters(buffer, byteorder=self.BYTEORDER)
            else:
                decoder = None  # error

        result = ModbusResultItem(read_item.name)

        if read_item.type == ModbusType.INT16:
            result.value = decoder.decode_16bit_int()
        elif read_item.type == ModbusType.UINT16:
            result.value = decoder.decode_16bit_uint()
        elif read_item.type == ModbusType.FLOAT32:
            result.value = decoder.decode_32bit_float()
        elif read_item.type == ModbusType.STRING8:
            raise NotImplementedError()
        else:
            raise ValueError()

        return result

    def _read_remote_registers(self, read: ModbusRead):
        if self._client is None or not self.is_open():
            raise FronmodException('ModbusClient not open!')

        response = self._client.read_holding_registers(read.pos, read.length, unit=read.unit_id)
        if response.isError():
            raise FronmodException('read_holding_registers failed!')

        print('response.registers: ', response.registers)
        return response.registers

    def read(self, read: ModbusRead):
        registers = self._read_remote_registers(read)

        results = {}
        for item in read.items:
            result = self._extract(item, registers)
            if results.get(item.name) is not None:
                raise FronmodException('wrong configuration - duplicate read names!')
            results[item.name] = result

        return results

    @staticmethod
    def print_register(text, value):
        type_name = None
        if value is not None:
            type_name = type(value)
        print('{}: "{}" ({})'.format(text, value, type_name))  # int16

    @staticmethod
    def print_decoded(text, value):
        type_name = None
        if value is not None:
            type_name = type(value)
        print('decoded - {}: "{}" ({})'.format(text, value, type_name))  # int16

    def get_decoder(self, registers, pos):
        conv_registers = registers[pos:]
        decoder = BinaryPayloadDecoder.fromRegisters(conv_registers,
                                                     byteorder=self.BYTEORDER)
        return decoder

    def read_float(self):

        response = self._client.read_holding_registers(40101, 2, unit=1)
        assert (not response.isError())  # test that we are not an error
        self.print_register('registers', response.registers)

        decoder = BinaryPayloadDecoder.fromRegisters(response.registers, byteorder=self.BYTEORDER)

        self.print_decoded('valPvInvAcEnergyTot', decoder.decode_32bit_float())

        # 	# 40102 40103 2 R 0x03 WH float32 Wh AC Lifetime
        # 	tcp.inv_40102.connection=192.168.12.42:502
        # 	tcp.inv_40102.start=40101
        # 	tcp.inv_40102.id=1
        # 	tcp.inv_40102.length=2
        # 	tcp.inv_40102.type=holding
        # 	tcp.inv_40102.valuetype=float32
        # 	tcp.inv_40102.postundefinedonreaderror=true

        # Number valPvInvAcEnergyTot   "valPvInvAcEnergyTot [%,.0f Wh]"  {modbus="<[inv_40102:0:valueType=float32]"}

        pass

    def read_mppt(self):
        print("Reading Coils")
        # rr = self.mclient.read_coils(1, 1, unit=ModbusClient.UNIT)
        # print(rr)

        # # Multiple MPPT Inverter Extension Model (I160) (ab Seite 57)
        #     tcp.mppt.connection=192.168.12.42
        #     tcp.mppt.start=40263
        #     tcp.mppt.id=1
        #     tcp.mppt.length=48
        #     tcp.mppt.type=holding
        #     tcp.mppt.postundefinedonreaderror=true
	    #     tcp.mppt=uint16

        response = self._client.read_holding_registers(40263, 48, unit=1)
        assert (not response.isError())  # test that we are not an error

        self.print_register('registers', response.registers)

        print("-" * 60)

        # Number rawPvMpptBattPower       "rawPvMpptBattPower [%d]"            {modbus="<[mppt:41:valueType=uint16]"}
        # Number rawPvMpptModPower        "rawPvMpptModPower [%d]"             {modbus="<[mppt:21:valueType=uint16]"}
        # Number rawPvMpptModVoltage      "rawPvMpptModVoltage [%d]"           {modbus="<[mppt:20:valueType=uint16]"}
        # Number rawPvMpptPowerSfBase     "rawPvMpptPowerSfBase [%d]"          {modbus="<[mppt:4:valueType=int16]"}
        # Number rawPvMpptVoltageSfBase   "rawPvMpptVoltageSfBase [%d]"        {modbus="<[mppt:3:valueType=int16]"}
        # Number valPvMpptBatState        "MPPT-Batterie-Status [MAP(pv_state_mppt.map):%s]" {modbus="<[mppt:47]"}
        # Number valPvMpptModState        "MPPT-Modul-Status [MAP(pv_state_mppt.map):%s]"    {modbus="<[mppt:27]"}

        self.print_register('rawPvMpptBattPower', response.registers[41])
        self.print_register('rawPvMpptModPower', response.registers[21])
        self.print_register('rawPvMpptModVoltage', response.registers[20])
        self.print_register('rawPvMpptPowerSfBase', response.registers[4])
        self.print_register('rawPvMpptVoltageSfBase', response.registers[3])
        self.print_register('valPvMpptBatState (MPPT-Batterie-Status)', response.registers[47])
        self.print_register('valPvMpptModState (MPPT-Modul-Status)', response.registers[27])

        print("-" * 60)

        self.print_decoded('rawPvMpptBattPower', self.get_decoder(response.registers, 41).decode_16bit_uint())
        self.print_decoded('rawPvMpptModPower', self.get_decoder(response.registers, 21).decode_16bit_uint())
        self.print_decoded('rawPvMpptModVoltage', self.get_decoder(response.registers, 20).decode_16bit_uint())
        self.print_decoded('rawPvMpptPowerSfBase', self.get_decoder(response.registers, 4).decode_16bit_int())
        self.print_decoded('rawPvMpptVoltageSfBase', self.get_decoder(response.registers, 3).decode_16bit_int())
        self.print_decoded('valPvMpptBatState (MPPT-Batterie-Status)'
                           , self.get_decoder(response.registers, 47).decode_16bit_int())
        self.print_decoded('valPvMpptModState (MPPT-Modul-Status)'
                           , self.get_decoder(response.registers, 27).decode_16bit_int())





