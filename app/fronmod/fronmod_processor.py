import logging
from . import *
from prend.channel import Channel, ChannelType
from prend.oh.oh_send_data import OhSendFlags, OhSendData


# /home/mnt/nextcloud/ebooks/Technik/Haus/Fronius/Fronius_Datamanager_Modbus_TCP-RTU_DE_20181025.pdf


_logger = logging.getLogger(__name__)


class FronmodProcessor:

    def __init__(self):
        self._reader = None

        self._send_quick = {}  # 10s
        self._send_medium = {}  # 60s
        self._send_slow = {}  # 300s

        self.eflow_inv_dc = EflowChannel(FronmodConfig.TEMP_INV_DC_POWER,
                                         EflowAggregate(FronmodConfig.EFLOW_INV_DC_OUT),
                                         EflowAggregate(FronmodConfig.EFLOW_INV_DC_IN))
        self.eflow_inv_ac = EflowChannel(FronmodConfig.TEMP_INV_AC_POWER,
                                         EflowAggregate(FronmodConfig.EFLOW_INV_AC_OUT),
                                         EflowAggregate(FronmodConfig.EFLOW_INV_AC_IN))
        self.eflow_bat = EflowChannel(FronmodConfig.TEMP_MPPT_BAT_POWER,
                                      EflowAggregate(FronmodConfig.EFLOW_BAT_OUT),
                                      EflowAggregate(FronmodConfig.EFLOW_BAT_IN))
        self.eflow_mod = EflowChannel(FronmodConfig.ITEM_MPPT_MOD_POWER,
                                      EflowAggregate(FronmodConfig.EFLOW_MOD_OUT),
                                      None)

    def set_reader(self, reader):
        self._reader = reader

    def open(self):
        self._reader.open()

    def close(self):
        self._reader.close()

    def _get_queue_dict(self, flags):
        if flags is None:
            return

        queue_dict = None
        if flags & MobuFlag.Q_QUICK:
            queue_dict = self._send_quick
        elif flags & MobuFlag.Q_MEDIUM:
            queue_dict = self._send_medium
        elif flags & MobuFlag.Q_SLOW:
            queue_dict = self._send_slow

        return queue_dict

    def get_send_data(self, flags):
        send_data_list = []
        queue_dict = self._get_queue_dict(flags)
        for key, send_data in queue_dict.items():
            send_data_list.append(send_data)
        return send_data_list

    def process_model(self, read_conf: MobuBatch):
        try:
            results = self._reader.read(read_conf)
        except FronmodException as ex:
            _logger.error('read_model failed ({})!'.format(read_conf))
            _logger.exception(ex)
            results = {}

        for key, result in results.items():
            self.queue_send(result)

        return results  # used for loading and analysing real values from test context

    def process_inverter_model(self):
        results = self.process_model(FronmodConfig.INVERTER_BATCH)

        self.process_factor_scale(results, FronmodConfig.ITEM_INV_AC_ENERGY_TOT
                                  , 0.001, FronmodConfig.SHOW_INV_AC_ENERGY_TOT),
        self.process_factor_scale(results, FronmodConfig.TEMP_INV_AC_POWER
                                  , 0.001, FronmodConfig.SHOW_INV_AC_POWER),
        self.process_factor_scale(results, FronmodConfig.TEMP_INV_DC_POWER
                                  , 0.001, FronmodConfig.SHOW_INV_DC_POWER),

        self.push_eflow(results, FronmodConfig.TEMP_INV_DC_POWER, self.eflow_inv_dc)
        self.push_eflow(results, FronmodConfig.TEMP_INV_AC_POWER, self.eflow_inv_ac)

        return results

    def process_storage_model(self):
        results = self.process_model(FronmodConfig.STORAGE_BATCH)

        self.process_modbus_scale(results, FronmodConfig.RAW_BAT_FILL_STATE, FronmodConfig.RAW_BAT_FILL_STATE_SF
                                  , FronmodConfig.ITEM_BAT_FILL_STATE)
        return results

    def process_mppt_model(self):
        results = self.process_model(FronmodConfig.MPPT_BATCH)

        self.process_modbus_scale(results, FronmodConfig.RAW_MPPT_MOD_VOLTAGE, FronmodConfig.RAW_MPPT_VOLTAGE_SF
                                  , FronmodConfig.ITEM_MPPT_MOD_VOLTAGE)

        self.process_modbus_scale(results, FronmodConfig.RAW_MPPT_MOD_POWER, FronmodConfig.RAW_MPPT_POWER_SF
                                  , FronmodConfig.ITEM_MPPT_MOD_POWER)

        self.process_modbus_scale(results, FronmodConfig.RAW_MPPT_BAT_POWER, FronmodConfig.RAW_MPPT_POWER_SF
                                  , FronmodConfig.TEMP_MPPT_BAT_POWER)

        self.process_factor_scale(results, FronmodConfig.TEMP_MPPT_BAT_POWER
                                  , 0.001, FronmodConfig.SHOW_MPPT_BAT_POWER),

        self.process_factor_scale(results, FronmodConfig.ITEM_MPPT_MOD_POWER
                                  , 0.001, FronmodConfig.SHOW_MPPT_MOD_POWER),

        self.push_eflow(results, FronmodConfig.TEMP_MPPT_BAT_POWER, self.eflow_bat)
        self.push_eflow(results, FronmodConfig.ITEM_MPPT_MOD_POWER, self.eflow_mod)

        return results

    def process_meter_model(self):
        results = self.process_model(FronmodConfig.METER_BATCH)

        self.process_factor_scale(results, FronmodConfig.ITEM_MET_AC_POWER
                                  , 0.001, FronmodConfig.SHOW_MET_AC_POWER),
        self.process_factor_scale(results, FronmodConfig.ITEM_MET_ENERGY_EXP_TOT
                                  , 0.001, FronmodConfig.SHOW_MET_ENERGY_EXP_TOT),
        self.process_factor_scale(results, FronmodConfig.ITEM_MET_ENERGY_IMP_TOT
                                  , 0.001, FronmodConfig.SHOW_MET_ENERGY_IMP_TOT),

        return results

    def process_modbus_scale(self, results: dict, value_name: str, scale_name: str, target_name: str):

        try:
            value_temp = results[value_name]
            scale_temp = results[scale_name]
            value_target = self.scale_item(value_temp, scale_temp)
        except (FronmodException, TypeError, ValueError) as ex:
            _logger.error('process_modbus_scale failed (%s + %s => %s)!', value_name, scale_name, target_name)
            _logger.exception(ex)
            value_target = None

        target_result = results[target_name]
        target_result.value = value_target
        target_result.ready = True
        self.queue_send(target_result)

    def process_factor_scale(self, results: dict, value_name: str, scale_factor: float, target_name: str):

        value_target = None
        try:
            result = results.get(value_name)
            if result:
                value_target = result.value * scale_factor
        except (TypeError, ValueError) as ex:
            _logger.error('process_factor_scale failed (%s + %s => %s)!', value_name, scale_factor, target_name)
            _logger.exception(ex)
            value_target = None

        target_result = results[target_name]
        target_result.value = value_target
        target_result.ready = True
        self.queue_send(target_result)

    @classmethod
    def push_eflow(cls, results, value_name, eflow):
        result = results[value_name]
        if not result.ready:
            raise FronmodException('can only push ready values!')
        eflow.push_value(result.value)

    def persist_eflow_aggregates(self):
        eflow_list = [self.eflow_inv_dc, self.eflow_inv_ac, self.eflow_bat, self.eflow_mod]
        for eflow in eflow_list:
            agg_list = eflow.get_aggregates_and_reset()
            for agg in agg_list:
                if agg.value_agg != 0:
                    # todo
                    channel = Channel.create(ChannelType.ITEM, agg.item_name)
                    self._oh_gateway.send(OhSendFlags.COMMAND | OhSendFlags.SEND_ONLY_IF_DIFFER, channel, agg.value_agg)
                    # self.queue_send(item_name, value)

    def queue_send(self, result: MobuResult):
        if not result or not result.ready:
            return

        queue_dict = self._get_queue_dict(result.item.flags)
        if queue_dict is not None:
            channel = Channel.create(ChannelType.ITEM, result.name)
            send_data = OhSendData(OhSendFlags.COMMAND | OhSendFlags.SEND_ONLY_IF_DIFFER, channel, result.value)
            queue_dict[result.name] = send_data

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


