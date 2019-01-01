from app.fronmod.fronmod_reader import FronmodReader, ModbusRead


class MockData:
    def __init__(self, read: ModbusRead, registers):
        self.read = read
        self.registers = registers


class MockFronmodReader(FronmodReader):

    def __init__(self):
        super().__init__(None, None)
        self._is_open = False
        self.mock_reads = {}
        pass

    def open(self):
        self._is_open = True

    def is_open(self) -> bool:
        return self._is_open

    def close(self):
        self._is_open = False

    def _read_remote_registers(self, read: ModbusRead):
        mock_data = self.mock_reads.get(read)
        if mock_data is None:
            raise ValueError('no mock data configured!')
        return mock_data.registers

    def set_mock_read(self, read, registers):
        data = MockData(read, registers)
        self.mock_reads[data.read] = data

    def clear_mock_reads(self):
        self.mock_reads.clear()
