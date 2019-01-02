import logging
from .fronmod_constants import FronmodConstants
from .fronmod_exception import FronmodException
from .fronmod_reader import ModbusReadItem, ModbusRead, ModbusType, ModbusResultItem
from prend.channel import Channel, ChannelType
from prend.oh.oh_send_data import OhSendFlags
from pymodbus.constants import Endian


# /home/mnt/nextcloud/ebooks/Technik/Haus/Fronius/Fronius_Datamanager_Modbus_TCP-RTU_DE_20181025.pdf


_logger = logging.getLogger(__name__)


class FronmodProcessor:
    BYTEORDER = Endian.Big

    # Common & Inverter Model (ab Seite 29)
    START_INVERTER = 40070  # start pos
    FETCH_INVERTER = ModbusRead(1, START_INVERTER, 60, [
        # fronius: 40092 40093 2 R 0x03 W float32 W AC Power value
        # openhab: "WR-Ausgangsleistung  (AC) [%,.0f W]"
        ModbusReadItem(40092 - START_INVERTER, ModbusType.FLOAT32, 'valPvInvAcPower'),
        # fronius: 40102 40103 2 R 0x03 WH float32 Wh AC Lifetime
        # openhab: "valPvInvAcEnergyTot [%,.0f Wh]"
        ModbusReadItem(40102 - START_INVERTER, ModbusType.FLOAT32, 'valPvInvAcEnergyTot'),
        # fronius: 40108 40109 2 R 0x03 DCW float32 W DC Power value | Total DC power of all available MPPT
        # openhab: "WR-Eingangsleistung (DC) [%,.0f W]
        ModbusReadItem(40108 - START_INVERTER, ModbusType.FLOAT32, 'valPvInvDcPower'),
        # fronius: 40118 40118 1 R 0x03 St enum16 Enumerated Operating State 1)
        # openhab: Number valPvInvSunSpecState "WR-SunSpec-Status [MAP(pv_state_inv_sunspec.map):%s]"
        ModbusReadItem(40118 - START_INVERTER, ModbusType.INT16, 'valPvInvSunSpecState'),  # WR-SunSpec-Status
        # fronius: 40119 40119 1 R 0x03 StVnd enum16 Enumerated Vendor Defined Operating State 2)
        # openhab: Number valPvInvFroniusState   "WR-Fronius-Status [MAP(pv_state_inv_fronius.map):%s]"
        ModbusReadItem(40119 - START_INVERTER, ModbusType.INT16, 'valPvInvFroniusState'),  # WR-Fronius-Status
    ])

    # Basic Storage Control Model (IC124) (ab Seite 52)
    START_STORAGE = 40313
    FETCH_STORAGE = ModbusRead(1, START_STORAGE, 26, [
        # fronius: 9 9 1 R 0x03 ChaState uint16 % AhrRtg ChaState_SF
        #       Currently available energy as a percent of the capacity rating
        # openhab: Number rawPvBatFillState  "rawPvBatFillState [%d]"   {modbus="<[storage:8]"} // 40303 + 9
        # openhab: Number valPvBatState  "Batterie-Status [MAP(pv_state_batt.map):%s]"
        #       {modbus="<[storage:11:valueType=uint16]"} // 40303 + 12
        ModbusReadItem(9, ModbusType.UINT16, FronmodConstants.RAW_BAT_FILL_STATE),
        # fronius: 23 23 1 R 0x03 0x06 0x10 ChaState_SF sunssf Scale factor for available energy percent.
        ModbusReadItem(23, ModbusType.INT16, FronmodConstants.RAW_BAT_FILL_STATE_SF),
    ])

    # Multiple MPPT Inverter Extension Model (I160) (ab Seite 57)
    START_MPPT = 40263
    FETCH_MPPT = ModbusRead(1, START_MPPT, 48, [
        # fronius: 4 4 1 R 0x03 DCV_SF sunssf Voltage Scale Factor
        # openhab: Number rawPvMpptVoltageSfBase   "rawPvMpptVoltageSfBase [%d]" {modbus="<[mppt:3:valueType=int16]"}
        ModbusReadItem(4, ModbusType.INT16, 'rawPvMpptVoltageSfBase'),
        # fronius: 5 5 1 R 0x03 DCW_SF sunssf Power Scale Factor
        # openhab: Number rawPvMpptPowerSfBase     "rawPvMpptPowerSfBase [%d]" {modbus="<[mppt:4:valueType=int16]"}
        ModbusReadItem(5, ModbusType.INT16, 'rawPvMpptPowerSfBase'),
        # fronius: 21 21 1 R 0x03 1_DCV uint16 V DCV_SF DC Voltage
        # Number rawPvMpptModVoltage "rawPvMpptModVoltage [%d]"   {modbus="<[mppt:20:valueType=uint16]"}
        ModbusReadItem(21, ModbusType.UINT16, 'rawPvMpptModVoltage'),
        # fronius: 22 22 1 R 0x03 1_DCW uint16 W DCW_SF DC Power
        # Number rawPvMpptModPower "rawPvMpptModPower [%d]"  {modbus="<[mppt:21:valueType=uint16]"}
        ModbusReadItem(22, ModbusType.UINT16, 'rawPvMpptModPower'),
        # fronius: 28 28 1 R 0x03 1_DCSt enum16 Operating State
        # Number valPvMpptModState "MPPT-Modul-Status [MAP(pv_state_mppt.map):%s]" {modbus="<[mppt:27]"}
        ModbusReadItem(28, ModbusType.INT16, 'valPvMpptModState'),
        # fronius: 42 42 1 R 0x03 - 2_DCW - uint16 - W - DCW_SF - DC Power
        # Number rawPvMpptBattPower  "rawPvMpptBattPower [%d]"  {modbus="<[mppt:41:valueType=uint16]"}
        ModbusReadItem(42, ModbusType.UINT16, 'rawPvMpptBattPower'),
        # fronius: 8 48 1 R 0x03 2_DCSt enum16 Operating State
        # openhab: Number valPvMpptBatState "MPPT-Batterie-Status [MAP(pv_state_mppt.map):%s]" {modbus="<[mppt:47]"}
        ModbusReadItem(48, ModbusType.INT16, 'valPvMpptBatState'),
    ])

    # Meter Model (ab Seite 62)
    START_METER = 40070
    FETCH_METER = ModbusRead(240, START_METER, 124, [
        # 40096 40097 2 R 0x03 Hz float32 Hz AC Frequency value
        # Number valPvMetAcFrequency   "valPvMetAcFrequency [%.2f]"  {modbus="<[met_40096:0:valueType=float32]"}
        ModbusReadItem(40096 - START_METER, ModbusType.FLOAT32, 'valPvMetAcFrequency'),
        # 40098 40099 2 R 0x03 W float32 W AC Power value
        # Number valPvMetAcPower  "Netz-Leistung (- Einspeisen) [%,.0f W]"  {modbus="<[met_40098:0:valueType=float32]"}
        ModbusReadItem(40098 - START_METER, ModbusType.FLOAT32, 'valPvMetAcPower'),
        # 40130 40131 2 R 0x03 TotWhExp float32 Wh Total Watt-hours Exported
        # Number valPvMetEnergyExpTot "valPvMetEnergyExpTot [%d Wh]"   {modbus="<[met_40130:0:valueType=float32]"}
        ModbusReadItem(40130 - START_METER, ModbusType.FLOAT32, 'valPvMetEnergyExpTot'),
        # 40138 40139 2 R 0x03 TotWhImp float32 Wh Total Watt-hours Imported
        # Number valPvMetEnergyImpTot    "valPvMetEnergyImpTot [%d Wh]"  {modbus="<[met_40138:0:valueType=float32]"}
        ModbusReadItem(40138 - START_METER, ModbusType.FLOAT32, 'valPvMetEnergyImpTot'),
    ])

    def __init__(self):
        self._oh_gateway = None
        self._reader = None
        pass

    def set_oh_gateway(self, oh_gateway):
        self._oh_gateway = oh_gateway
        pass

    def set_reader(self, reader):
        self._reader = reader

    def open(self):
        self._reader.open()

    def close(self):
        self._reader.close()

    def read_inverter_model(self):
        return self._reader.read(self.FETCH_INVERTER)

    def read_storage_model(self):

        results = self._reader.read(self.FETCH_STORAGE)

        raw_state = results[FronmodConstants.RAW_BAT_FILL_STATE]
        raw_state_sf = results[FronmodConstants.RAW_BAT_FILL_STATE_SF]

        fill_state = ModbusResultItem(FronmodConstants.ITEM_BAT_FILL_STATE)
        fill_state.value = self.scale_item(raw_state, raw_state_sf)
        if results.get(FronmodConstants.ITEM_BAT_FILL_STATE) is not None:
            raise FronmodException('result item name already exists!')
        results[FronmodConstants.ITEM_BAT_FILL_STATE] = fill_state

        return results

    def process_storage(self):
        try:
            results = self._reader.read(self.FETCH_STORAGE)

            raw_state = results[FronmodConstants.RAW_BAT_FILL_STATE]
            raw_state_sf = results[FronmodConstants.RAW_BAT_FILL_STATE_SF]

            fill_state = self.scale_item(raw_state, raw_state_sf)

        except FronmodConstants as ex:
            _logger.exception(ex)
            fill_state = None

        channel = Channel.create(ChannelType.ITEM, FronmodConstants.ITEM_BAT_FILL_STATE)
        state = self._oh_gateway.get_state(channel)
        if state is None:
            raise FronmodException('no state for "{}" found!'.format(FronmodConstants.ITEM_BAT_FILL_STATE))
        elif state.value != fill_state:
            state.value = fill_state
            self._oh_gateway.send(OhSendFlags.COMMAND, channel, state)
        else:
            # do nothing
            pass

    def read_mppt_model(self):
        return self._reader.read(self.FETCH_MPPT)

    def read_meter_model(self):
        return self._reader.read(self.FETCH_METER)

    @classmethod
    def scale_item(cls, value_item, scale_item):

        if value_item is None or value_item.value is None:
            raise ValueError()

        scale = cls.convert_scale_factor(scale_item)
        value = value_item.value * scale
        return value

    @classmethod
    def convert_scale_factor(cls, data_in, default_value=None):
        sunssf = None
        if isinstance(data_in, ModbusResultItem):
            sunssf = data_in.value
        else:
            sunssf = data_in

        if sunssf is None:
            raise ValueError()
        sunssf = round(sunssf)
        if sunssf > 10 or sunssf < -10:
            raise ValueError()

        scale_factor = pow(10, sunssf)
        return scale_factor



