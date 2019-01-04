import logging
from .fronmod_constants import FronmodConstants
from .fronmod_exception import FronmodException
from .fronmod_reader import MobuItem, MobuBulk, MobuFlag, MobuResult
from prend.channel import Channel, ChannelType
from prend.oh.oh_send_data import OhSendFlags
from pymodbus.constants import Endian


# /home/mnt/nextcloud/ebooks/Technik/Haus/Fronius/Fronius_Datamanager_Modbus_TCP-RTU_DE_20181025.pdf


_logger = logging.getLogger(__name__)


class FronmodProcessor:
    BYTEORDER = Endian.Big

    # Common & Inverter Model (ab Seite 29)
    START_INVERTER = 40070  # start pos
    FETCH_INVERTER = MobuBulk(1, START_INVERTER, 60, [
        # fronius: 40092 40093 2 R 0x03 W float32 W AC Power value
        # openhab: "WR-Ausgangsleistung  (AC) [%,.0f W]"
        MobuItem(40092 - START_INVERTER, MobuFlag.FLOAT32, FronmodConstants.ITEM_INV_AC_POWER),
        # fronius: 40102 40103 2 R 0x03 WH float32 Wh AC Lifetime
        # openhab: "valPvInvAcEnergyTot [%,.0f Wh]"

# todo 0.001
        MobuItem(40102 - START_INVERTER, MobuFlag.FLOAT32, FronmodConstants.ITEM_INV_AC_ENERGY_TOT),
        # fronius: 40108 40109 2 R 0x03 DCW float32 W DC Power value | Total DC power of all available MPPT
        # openhab: "WR-Eingangsleistung (DC) [%,.0f W]
        MobuItem(40108 - START_INVERTER, MobuFlag.FLOAT32, FronmodConstants.ITEM_INV_DC_POWER),
        # fronius: 40118 40118 1 R 0x03 St enum16 Enumerated Operating State 1)
        # openhab: Number valPvInvSunSpecState "WR-SunSpec-Status [MAP(pv_state_inv_sunspec.map):%s]"
        MobuItem(40118 - START_INVERTER, MobuFlag.INT16, FronmodConstants.ITEM_INV_STATE_SUNSPEC),
        # fronius: 40119 40119 1 R 0x03 StVnd enum16 Enumerated Vendor Defined Operating State 2)
        # openhab: Number valPvInvFroniusState   "WR-Fronius-Status [MAP(pv_state_inv_fronius.map):%s]"
        MobuItem(40119 - START_INVERTER, MobuFlag.INT16, FronmodConstants.ITEM_INV_STATE_FRONIUS),
    ])

    # Basic Storage Control Model (IC124) (ab Seite 52)
    START_STORAGE = 40313
    FETCH_STORAGE = MobuBulk(1, START_STORAGE, 26, [
        # fronius: 9 9 1 R 0x03 ChaState uint16 % AhrRtg ChaState_SF
        #       Currently available energy as a percent of the capacity rating
        # openhab: Number rawPvBatFillState  "rawPvBatFillState [%d]"   {modbus="<[storage:8]"} // 40303 + 9
        # openhab: Number valPvBatState  "Batterie-Status [MAP(pv_state_batt.map):%s]"
        #       {modbus="<[storage:11:valueType=uint16]"} // 40303 + 12
        MobuItem(9, MobuFlag.UINT16 | MobuFlag.RAW, FronmodConstants.RAW_BAT_FILL_STATE),
        # fronius: 23 23 1 R 0x03 0x06 0x10 ChaState_SF sunssf Scale factor for available energy percent.
        MobuItem(23, MobuFlag.INT16 | MobuFlag.RAW, FronmodConstants.RAW_BAT_FILL_STATE_SF),
    ])

    # Multiple MPPT Inverter Extension Model (I160) (ab Seite 57)
    START_MPPT = 40263
    FETCH_MPPT = MobuBulk(1, START_MPPT, 48, [
        # fronius: 4 4 1 R 0x03 DCV_SF sunssf Voltage Scale Factor
        # openhab: Number rawPvMpptVoltageSfBase   "rawPvMpptVoltageSfBase [%d]" {modbus="<[mppt:3:valueType=int16]"}
        MobuItem(4, MobuFlag.INT16 | MobuFlag.RAW, FronmodConstants.RAW_MPPT_VOLTAGE_SF),
        # fronius: 5 5 1 R 0x03 DCW_SF sunssf Power Scale Factor
        # openhab: Number rawPvMpptPowerSfBase     "rawPvMpptPowerSfBase [%d]" {modbus="<[mppt:4:valueType=int16]"}
        MobuItem(5, MobuFlag.INT16 | MobuFlag.RAW, FronmodConstants.RAW_MPPT_POWER_SF),
        # fronius: 21 21 1 R 0x03 1_DCV uint16 V DCV_SF DC Voltage
        # Number rawPvMpptModVoltage "rawPvMpptModVoltage [%d]"   {modbus="<[mppt:20:valueType=uint16]"}
        MobuItem(21, MobuFlag.UINT16 | MobuFlag.RAW, FronmodConstants.RAW_MPPT_MOD_VOLTAGE),
        # fronius: 22 22 1 R 0x03 1_DCW uint16 W DCW_SF DC Power
        # Number rawPvMpptModPower "rawPvMpptModPower [%d]"  {modbus="<[mppt:21:valueType=uint16]"}
        MobuItem(22, MobuFlag.UINT16 | MobuFlag.RAW, FronmodConstants.RAW_MPPT_MOD_POWER),
        # fronius: 28 28 1 R 0x03 1_DCSt enum16 Operating State
        # Number valPvMpptModState "MPPT-Modul-Status [MAP(pv_state_mppt.map):%s]" {modbus="<[mppt:27]"}
        MobuItem(28, MobuFlag.INT16, FronmodConstants.ITEM_MPPT_MOD_STATE),
        # fronius: 42 42 1 R 0x03 - 2_DCW - uint16 - W - DCW_SF - DC Power
        # Number rawPvMpptBattPower  "rawPvMpptBattPower [%d]"  {modbus="<[mppt:41:valueType=uint16]"}
        MobuItem(42, MobuFlag.UINT16 | MobuFlag.RAW, FronmodConstants.RAW_MPPT_BAT_POWER),
        # fronius: 8 48 1 R 0x03 2_DCSt enum16 Operating State
        # openhab: Number valPvMpptBatState "MPPT-Batterie-Status [MAP(pv_state_mppt.map):%s]" {modbus="<[mppt:47]"}
        MobuItem(48, MobuFlag.INT16, FronmodConstants.ITEM_MPPT_BAT_STATE),
    ])

    # Meter Model (ab Seite 62)
    START_METER = 40070
    FETCH_METER = MobuBulk(240, START_METER, 124, [
        # 40096 40097 2 R 0x03 Hz float32 Hz AC Frequency value
        # Number valPvMetAcFrequency   "valPvMetAcFrequency [%.2f]"  {modbus="<[met_40096:0:valueType=float32]"}
        MobuItem(40096 - START_METER, MobuFlag.FLOAT32, FronmodConstants.ITEM_MET_AC_FREQUENCY),
        # 40098 40099 2 R 0x03 W float32 W AC Power value
        # Number valPvMetAcPower  "Netz-Leistung (- Einspeisen) [%,.0f W]"  {modbus="<[met_40098:0:valueType=float32]"}
        MobuItem(40098 - START_METER, MobuFlag.FLOAT32, FronmodConstants.ITEM_MET_AC_POWER),
        # 40130 40131 2 R 0x03 TotWhExp float32 Wh Total Watt-hours Exported
        # Number valPvMetEnergyExpTot "valPvMetEnergyExpTot [%d Wh]"   {modbus="<[met_40130:0:valueType=float32]"}
        MobuItem(40130 - START_METER, MobuFlag.FLOAT32, FronmodConstants.ITEM_MET_ENERGY_EXP_TOT),
        # 40138 40139 2 R 0x03 TotWhImp float32 Wh Total Watt-hours Imported
        # Number valPvMetEnergyImpTot    "valPvMetEnergyImpTot [%d Wh]"  {modbus="<[met_40138:0:valueType=float32]"}
        MobuItem(40138 - START_METER, MobuFlag.FLOAT32, FronmodConstants.ITEM_MET_ENERGY_IMP_TOT),
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

    def process_model(self, read_conf: MobuBulk):
        try:
            results = self._reader.read(read_conf)
        except FronmodConstants as ex:
            _logger.error('read_model failed ({})!'.format(read_conf))
            _logger.exception(ex)
            results = {}

        for item in read_conf.items:
            if not item.flags & MobuFlag.RAW:
                channel = Channel.create(ChannelType.ITEM, item.name)
                result = results[item.name]
                self._oh_gateway.send(OhSendFlags.COMMAND | OhSendFlags.SEND_ONLY_IF_DIFFER, channel, result.value)

        return results  # used for loading and analysing real values from test context

    def process_inverter_model(self):

        # todo
        # FronmodConstants.ITEM_MPPT_MOD_VOLTAGE = 'valPvModVoltage'
        # FronmodConstants.ITEM_MPPT_BAT_POWER = 'valPvBatPower'
        # valPvModVoltage <= rawPvMpptModVoltage + rawPvMpptVoltageSfReal <= rawPvMpptVoltageSfBase)
        # valPvBatPower <= rawPvMpptBattPower + rawPvMpptPowerSfReal <= rawPvMpptPowerSfBase


        # todo eflow: valPvInvDcPower => valPvEflowInvDcIn, valPvEflowInvDcOut (gEflowInvDcOutTemp, gEflowInvDcInTemp)
        # todo eflow: valPvInvAcPower => valPvEflowInvAcIn, valPvEflowInvAcOut (gEflowInvAcOutTemp, gEflowInvAcInTemp)
        #
        return self.process_model(self.FETCH_INVERTER)

    def process_storage_model(self):
        try:
            results = self._reader.read(self.FETCH_STORAGE)

            raw_state = results[FronmodConstants.RAW_BAT_FILL_STATE]
            raw_state_sf = results[FronmodConstants.RAW_BAT_FILL_STATE_SF]

            fill_state = self.scale_item(raw_state, raw_state_sf)

        except FronmodConstants as ex:
            _logger.exception(ex)
            fill_state = None

        channel = Channel.create(ChannelType.ITEM, FronmodConstants.ITEM_BAT_FILL_STATE)
        self._oh_gateway.send(OhSendFlags.COMMAND | OhSendFlags.SEND_ONLY_IF_DIFFER, channel, fill_state)

        return results

    def process_mppt_model(self):
        return self.process_model(self.FETCH_MPPT)

    def process_meter_model(self):
        return self.process_model(self.FETCH_METER)

    @classmethod
    def scale_item(cls, value_item: MobuResult, scale_item: MobuResult):
        if value_item is None or value_item.value is None:
            raise ValueError()

        scale = cls.convert_scale_factor(scale_item)
        value = value_item.value * scale
        return value

    @classmethod
    def convert_scale_factor(cls, data_in, default_value=None):
        sunssf = None
        if isinstance(data_in, MobuResult):
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



