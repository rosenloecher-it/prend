from .mobu import MobuBatch, MobuFlag, MobuItem
from pymodbus.constants import Endian


class FronmodConfig:
    BYTEORDER = Endian.Big

    # inverter
    ITEM_INV_AC_ENERGY_TOT = 'valPvInvAcEnergyTot'
    ITEM_INV_EFFICIENCY = 'valPvInvEfficiency'
    ITEM_INV_STATE_FRONIUS = 'valPvInvFroniusState'
    ITEM_INV_STATE_SUNSPEC = 'valPvInvSunSpecState'
    SHOW_INV_AC_ENERGY_TOT = 'showPvInvAcEnergyTot'
    SHOW_INV_AC_POWER = 'showPvInvAcPower'
    SHOW_INV_DC_POWER = 'showPvInvDcPower'
    TEMP_INV_AC_POWER = 'tempPvInvAcPower'
    TEMP_INV_DC_POWER = 'tempPvInvDcPower'

    # storage
    ITEM_BAT_FILL_STATE = 'valPvBatFillState'
    ITEM_BAT_STATE = 'valPvBatState'
    RAW_BAT_FILL_STATE = 'rawPvBatFillState'
    RAW_BAT_FILL_STATE_SF = 'rawPvBatFillStateSf'

    # mppt
    ITEM_MPPT_BAT_STATE = 'valPvMpptBatState'
    ITEM_MPPT_MOD_POWER = 'valPvModPower'
    ITEM_MPPT_MOD_STATE = 'valPvMpptModState'
    ITEM_MPPT_MOD_VOLTAGE = 'valPvModVoltage'
    RAW2_MPPT_BAT_POWER = 'raw2PvBatPower'
    RAW_MPPT_BAT_POWER = 'rawPvMpptBattPower'
    RAW_MPPT_MOD_POWER = 'rawPvMpptModPower'
    RAW_MPPT_MOD_VOLTAGE = 'rawPvMpptModVoltage'
    RAW_MPPT_POWER_SF = 'rawPvMpptPowerSfBase'
    RAW_MPPT_VOLTAGE_SF = 'rawPvMpptVoltageSfBase'
    SHOW_MPPT_BAT_POWER = 'showPvBatPower'
    SHOW_MPPT_MOD_POWER = 'showPvModPower'
    TEMP_MPPT_BAT_POWER = 'tempPvBatPower'

    # meter
    ITEM_MET_AC_FREQUENCY = 'valPvMetAcFrequency'
    ITEM_MET_AC_POWER = 'valPvMetAcPower'  # W
    ITEM_MET_ENERGY_EXP_TOT = 'valPvMetEnergyExpTot'
    ITEM_MET_ENERGY_IMP_TOT = 'valPvMetEnergyImpTot'
    SHOW_MET_AC_POWER = 'showPvMetAcPower'  # kW
    SHOW_MET_ENERGY_EXP_TOT = 'showPvMetEnergyExpTot'  # kW
    SHOW_MET_ENERGY_IMP_TOT = 'showPvMetEnergyImpTot'  # kW

    # eflow
    EFLOW_BAT_IN = 'valPvEflowBatIn'
    EFLOW_BAT_OUT = 'valPvEflowBatOut'
    EFLOW_INV_AC_IN = 'valPvEflowInvAcIn'
    EFLOW_INV_AC_OUT = 'valPvEflowInvAcOut'
    EFLOW_INV_DC_IN = 'valPvEflowInvDcIn'
    EFLOW_INV_DC_OUT = 'valPvEflowInvDcOut'
    EFLOW_MOD_OUT = 'valPvEflowModOut'

    # comprehensive
    ITEM_SELF_CONSUMPTION = 'valPvSelfConsumption'  # = -1.0 * (TEMP_INV_AC_POWER + ITEM_MET_AC_POWER)
    MOBU_SELF_CONSUMPTION = MobuItem(None, MobuFlag.NONE | MobuFlag.Q_QUICK, ITEM_SELF_CONSUMPTION)

    # Common & Inverter Model (ab Seite 29)
    INVERTER_START = 40070  # start pos
    INVERTER_BATCH = MobuBatch(1, INVERTER_START, 60, [
        # fronius: 40092 40093 2 R 0x03 W float32 W AC Power value
        # openhab: "WR-Ausgangsleistung  (AC) [%,.0f W]"
        MobuItem(40092 - INVERTER_START, MobuFlag.FLOAT32, TEMP_INV_AC_POWER),
        # fronius: 40102 40103 2 R 0x03 WH float32 Wh AC Lifetime
        # openhab: "valPvInvAcEnergyTot [%,.0f Wh]"
        MobuItem(40102 - INVERTER_START, MobuFlag.FLOAT32 | MobuFlag.Q_MEDIUM, ITEM_INV_AC_ENERGY_TOT),
        # fronius: 40108 40109 2 R 0x03 DCW float32 W DC Power value | Total DC power of all available MPPT
        # openhab: "WR-Eingangsleistung (DC) [%,.0f W]
        MobuItem(40108 - INVERTER_START, MobuFlag.FLOAT32, TEMP_INV_DC_POWER),
        # fronius: 40118 40118 1 R 0x03 St enum16 Enumerated Operating State 1)
        # openhab: Number valPvInvSunSpecState "WR-SunSpec-Status [MAP(pv_state_inv_sunspec.map):%s]"
        MobuItem(40118 - INVERTER_START, MobuFlag.INT16 | MobuFlag.Q_MEDIUM, ITEM_INV_STATE_SUNSPEC),
        # fronius: 40119 40119 1 R 0x03 StVnd enum16 Enumerated Vendor Defined Operating State 2)
        # openhab: Number valPvInvFroniusState   "WR-Fronius-Status [MAP(pv_state_inv_fronius.map):%s]"
        MobuItem(40119 - INVERTER_START, MobuFlag.INT16 | MobuFlag.Q_MEDIUM, ITEM_INV_STATE_FRONIUS),

        MobuItem(None, MobuFlag.Q_QUICK, ITEM_INV_EFFICIENCY),
        MobuItem(None, MobuFlag.Q_MEDIUM, SHOW_INV_AC_ENERGY_TOT),
        MobuItem(None, MobuFlag.Q_QUICK, SHOW_INV_AC_POWER),
        MobuItem(None, MobuFlag.Q_QUICK, SHOW_INV_DC_POWER),

    ])

    # Basic Storage Control Model (IC124) (ab Seite 52)
    STORAGE_START = 40313
    STORAGE_BATCH = MobuBatch(1, STORAGE_START, 26, [
        # fronius: 9 9 1 R 0x03 ChaState uint16 % AhrRtg ChaState_SF
        MobuItem(9, MobuFlag.UINT16, RAW_BAT_FILL_STATE),
        # fronius: 23 23 1 R 0x03 0x06 0x10 ChaState_SF sunssf Scale factor for available energy percent.
        MobuItem(23, MobuFlag.INT16, RAW_BAT_FILL_STATE_SF),
        # openhab: Number valPvBatFillState "Batterie-Ladung [%.0f %%]" <battery> (gRawPvMod, gPers5Minutes)
        MobuItem(None, MobuFlag.Q_QUICK, ITEM_BAT_FILL_STATE),
        # Number valPvBatState "Batterie-Status [MAP(pv_state_batt.map):%s]"
        #  {modbus = "<[storage:11:valueType=uint16]"} // 40303 + 12
        MobuItem(12, MobuFlag.UINT16 | MobuFlag.Q_QUICK, ITEM_BAT_STATE),


    ])

    # Multiple MPPT Inverter Extension Model (I160) (ab Seite 57)
    MPPT_START = 40263
    MPPT_BATCH = MobuBatch(1, MPPT_START, 48, [
        # fronius: 4 4 1 R 0x03 DCV_SF sunssf Voltage Scale Factor
        # openhab: Number rawPvMpptVoltageSfBase   "rawPvMpptVoltageSfBase [%d]" {modbus="<[mppt:3:valueType=int16]"}
        MobuItem(4, MobuFlag.INT16, RAW_MPPT_VOLTAGE_SF),
        # fronius: 5 5 1 R 0x03 DCW_SF sunssf Power Scale Factor
        # openhab: Number rawPvMpptPowerSfBase     "rawPvMpptPowerSfBase [%d]" {modbus="<[mppt:4:valueType=int16]"}
        MobuItem(5, MobuFlag.INT16, RAW_MPPT_POWER_SF),
        # fronius: 21 21 1 R 0x03 1_DCV uint16 V DCV_SF DC Voltage
        # Number rawPvMpptModVoltage "rawPvMpptModVoltage [%d]"   {modbus="<[mppt:20:valueType=uint16]"}
        MobuItem(21, MobuFlag.UINT16, RAW_MPPT_MOD_VOLTAGE),
        # fronius: 22 22 1 R 0x03 1_DCW uint16 W DCW_SF DC Power
        # Number rawPvMpptModPower "rawPvMpptModPower [%d]"  {modbus="<[mppt:21:valueType=uint16]"}
        MobuItem(22, MobuFlag.UINT16, RAW_MPPT_MOD_POWER),
        # fronius: 28 28 1 R 0x03 1_DCSt enum16 Operating State
        # Number valPvMpptModState "MPPT-Modul-Status [MAP(pv_state_mppt.map):%s]" {modbus="<[mppt:27]"}
        MobuItem(28, MobuFlag.INT16 | MobuFlag.Q_MEDIUM, ITEM_MPPT_MOD_STATE),
        # fronius: 42 42 1 R 0x03 - 2_DCW - uint16 - W - DCW_SF - DC Power
        # Number rawPvMpptBattPower  "rawPvMpptBattPower [%d]"  {modbus="<[mppt:41:valueType=uint16]"}
        MobuItem(42, MobuFlag.UINT16, RAW_MPPT_BAT_POWER),
        # fronius: 8 48 1 R 0x03 2_DCSt enum16 Operating State
        # openhab: Number valPvMpptBatState "MPPT-Batterie-Status [MAP(pv_state_mppt.map):%s]" {modbus="<[mppt:47]"}
        MobuItem(48, MobuFlag.INT16 | MobuFlag.Q_MEDIUM, ITEM_MPPT_BAT_STATE),

        MobuItem(None, MobuFlag.NONE, RAW2_MPPT_BAT_POWER),
        MobuItem(None, MobuFlag.NONE, TEMP_MPPT_BAT_POWER),
        MobuItem(None, MobuFlag.NONE, ITEM_MPPT_MOD_POWER),
        MobuItem(None, MobuFlag.Q_QUICK, ITEM_MPPT_MOD_VOLTAGE),
        MobuItem(None, MobuFlag.Q_QUICK, SHOW_MPPT_BAT_POWER),
        MobuItem(None, MobuFlag.Q_QUICK, SHOW_MPPT_MOD_POWER),
    ])

    # Meter Model (ab Seite 62)
    METER_START = 40070
    METER_BATCH = MobuBatch(240, METER_START, 124, [
        # 40096 40097 2 R 0x03 Hz float32 Hz AC Frequency value
        # Number valPvMetAcFrequency   "valPvMetAcFrequency [%.2f]"  {modbus="<[met_40096:0:valueType=float32]"}
        MobuItem(40096 - METER_START, MobuFlag.FLOAT32 | MobuFlag.Q_MEDIUM, ITEM_MET_AC_FREQUENCY),
        # 40098 40099 2 R 0x03 W float32 W AC Power value
        # Number valPvMetAcPower  "Netz-Leistung (- Einspeisen) [%,.0f W]"  {modbus="<[met_40098:0:valueType=float32]"}
        MobuItem(40098 - METER_START, MobuFlag.FLOAT32, ITEM_MET_AC_POWER),
        # 40130 40131 2 R 0x03 TotWhExp float32 Wh Total Watt-hours Exported
        # Number valPvMetEnergyExpTot "valPvMetEnergyExpTot [%d Wh]"   {modbus="<[met_40130:0:valueType=float32]"}
        MobuItem(40130 - METER_START, MobuFlag.FLOAT32 | MobuFlag.Q_MEDIUM, ITEM_MET_ENERGY_EXP_TOT),
        # 40138 40139 2 R 0x03 TotWhImp float32 Wh Total Watt-hours Imported
        # Number valPvMetEnergyImpTot    "valPvMetEnergyImpTot [%d Wh]"  {modbus="<[met_40138:0:valueType=float32]"}
        MobuItem(40138 - METER_START, MobuFlag.FLOAT32 | MobuFlag.Q_MEDIUM, ITEM_MET_ENERGY_IMP_TOT),

        MobuItem(None, MobuFlag.Q_QUICK, SHOW_MET_AC_POWER),
        MobuItem(None, MobuFlag.Q_MEDIUM, SHOW_MET_ENERGY_EXP_TOT),
        MobuItem(None, MobuFlag.Q_MEDIUM, SHOW_MET_ENERGY_IMP_TOT),
    ])

    RESET_ITEM_LIST = [
        # inverter
        ITEM_INV_EFFICIENCY,
        ITEM_INV_STATE_FRONIUS,
        ITEM_INV_STATE_SUNSPEC,
        SHOW_INV_AC_ENERGY_TOT,
        SHOW_INV_AC_POWER,
        SHOW_INV_DC_POWER,

        # storage
        ITEM_BAT_FILL_STATE,
        ITEM_BAT_STATE,

        # mppt
        ITEM_MPPT_BAT_STATE,
        ITEM_MPPT_MOD_POWER,
        ITEM_MPPT_MOD_STATE,
        ITEM_MPPT_MOD_VOLTAGE,
        SHOW_MPPT_BAT_POWER,
        SHOW_MPPT_MOD_POWER,

        # meter
        ITEM_MET_AC_FREQUENCY,
        ITEM_MET_AC_POWER,
        ITEM_MET_ENERGY_EXP_TOT,
        ITEM_MET_ENERGY_IMP_TOT,
        SHOW_MET_AC_POWER,
        SHOW_MET_ENERGY_EXP_TOT,
        SHOW_MET_ENERGY_IMP_TOT,

        # eflow
        EFLOW_BAT_IN,
        EFLOW_BAT_OUT,
        EFLOW_INV_AC_IN,
        EFLOW_INV_AC_OUT,
        EFLOW_INV_DC_IN,
        EFLOW_INV_DC_OUT,
        EFLOW_MOD_OUT,

        ITEM_SELF_CONSUMPTION
    ]
