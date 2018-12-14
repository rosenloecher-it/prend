
class FronstorConstants:

    URL_FRONIUS_STORAGE = 'http://192.168.12.42/solar_api/v1/GetStorageRealtimeData.cgi?Scope=System'

    ITEM_INV_TEMP = 'valPvInvTemp'

    ITEM_BAT_TEMP_MAX = 'valPvBatTmax'
    ITEM_BAT_CYCLE_SPAN = 'valPvBatCycles'

    ITEM_BAT_COUNT = 4
    ITEM_BAT_CYCLE_FORMAT = 'valPvBat{}Cycle'
    ITEM_BAT_TEMP_FORMAT = 'valPvBat{}Temp'

