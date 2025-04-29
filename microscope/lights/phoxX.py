from ast import List
import serial
import logging
from enum import Enum
import microscope
import microscope.abc
from microscope.lights import LightSourceStatus

def is_bit_set(byte: bytes, position:int) -> bool:
    return int(byte) & (1 << position) != 0

class Status:
    def __init__(self, bytes) -> None:
        "Status indicators for the device"
        self.error = is_bit_set(bytes[0], 0)
        self.on = is_bit_set(bytes[0], 1)
        self.preheating = is_bit_set(bytes[0], 2)
        self.attention_required = is_bit_set(bytes[0], 4)
        self.enabled_pin = is_bit_set(bytes[0], 6)
        self.key_switch = is_bit_set(bytes[0], 7)
        self.toggle_key = is_bit_set(bytes[1], 0)
        self.system_power = is_bit_set(bytes[1], 1)
        self.external_sensor_connected = is_bit_set(bytes[1], 5)

    def __repr__(self) -> str:
        "Used for easy inspection of the objects' states"
        return(
            f'{{ "error": {self.error}, "on": {self.on}, "preheating": {self.preheating}, '
            f'"attention_required": {self.attention_required}, "enabled_pin": {self.enabled_pin}, '
            f'"key_switch": {self.key_switch}, "toggle_key": {self.toggle_key}, '
            f'"system_power": {self.system_power}, "external_sensor_connected": {self.external_sensor_connected} }}'
        )
    
class LatchedFailure:
    def __init__(self, data: bytes) -> None:
        """
        Latched failure indicators for the laser/LED device.
        """
        self.error_state = is_bit_set(data[0], 0)
        self.CDRH = is_bit_set(data[0], 4)
        self.internal_communication_error = is_bit_set(data[0], 5)
        self.k1_relay_error = is_bit_set(data[0], 6)
        self.high_power = is_bit_set(data[0], 7)
        self.under_over_voltage = is_bit_set(data[1], 0)
        self.external_interlock = is_bit_set(data[1], 1)
        self.diode_current = is_bit_set(data[1], 2)
        self.ambient_temp = is_bit_set(data[1], 3)
        self.diode_temp = is_bit_set(data[1], 4)
        self.test_error = is_bit_set(data[1], 5)
        self.internal_error = is_bit_set(data[1], 6)
        self.diode_power = is_bit_set(data[1], 7)

    def __repr__(self) -> str:
        return (
            f'{{ "error_state": {self.error_state}, "CDRH_error": {self.CDRH}, '
            f'"internal_communication_error": {self.internal_communication_error}, "k1_relay_error": {self.k1_relay_error}, '
            f'"high_power": {self.high_power}, "under_over_voltage": {self.under_over_voltage}, '
            f'"external_interlock": {self.external_interlock}, "diode_current": {self.diode_current}, '
            f'"ambient_temp": {self.ambient_temp}, "diode_temp": {self.diode_temp}, "test_error": {self.test_error}, '
            f'"internal_error": {self.internal_error}, "diode_power": {self.diode_power} }}'
        )


class OperationMode:
    def __init__(self, data: bytes) -> None:
        """
        Operation mode settings for the laser/LED device.
        """
        self.internal_clock_generator = is_bit_set(data[0], 2)
        self.bias_level_release = is_bit_set(data[0], 3)
        self.operating_level_release = is_bit_set(data[0], 4)
        self.digital_input_release = is_bit_set(data[0], 5)
        self.analog_input_release = is_bit_set(data[0], 7)
        self.APC_mode = is_bit_set(data[1], 0)
        self.digital_input_impedance = is_bit_set(data[1], 3)
        self.analog_input_impedance = is_bit_set(data[1], 4)
        self.usb_adhoc_mode = is_bit_set(data[1], 5)
        self.auto_startup = is_bit_set(data[1], 6)
        self.auto_powerup = is_bit_set(data[1], 7)

    def __repr__(self) -> str:
        return (
            f'{{ "internal_clock_generator": {self.internal_clock_generator}, '
            f'"bias_level_release": {self.bias_level_release}, '
            f'"operating_level_release": {self.operating_level_release}, '
            f'"digital_input_release": {self.digital_input_release}, '
            f'"analog_input_release": {self.analog_input_release}, '
            f'"APC_mode": {self.APC_mode}, '
            f'"digital_input_impedance": {self.digital_input_impedance}, '
            f'"analog_input_impedance": {self.analog_input_impedance}, '
            f'"usb_adhoc_mode": {self.usb_adhoc_mode}, '
            f'"auto_startup": {self.auto_startup}, '
            f'"auto_powerup": {self.auto_powerup} }}'
        )

    def __int__(self) -> int:
        return (
            (self.internal_clock_generator << 2) |
            (self.bias_level_release << 3) |
            (self.operating_level_release << 4) |
            (self.digital_input_release << 5) |
            (self.analog_input_release << 7) |
            (self.APC_mode << 8) |
            (self.digital_input_impedance << 10) |
            (self.analog_input_impedance << 12) |
            (self.usb_adhoc_mode << 13) |
            (self.auto_startup << 14) |
            (self.auto_powerup << 15)
        )

    def __bytes__(self) -> bytes:
        return hex(self.__int__())[2:].encode("Latin1")


class CalibrationResult(Enum):
    SUCCESS = 0
    MAX_POWER_UNREACHABLE = 1
    KEY_SWITCH_OFF = 2
    LASER_ENABLE_INPUT_LOW = 3
    INTERLOCK_OCCURRED = 4
    DIODE_TEMP_ERROR = 5
    CONTROLLER_HEAD_COMM_ERROR = 6
    BIAS_OUT_OF_RANGE = 7
    NO_BIAS_POINT = 8
    LESS_THAN_PREV_95 = 9
    LASER_SWITCHED_OFF = 10
    NO_CALIBRATION_SENSOR = 11
    NO_LIGHT_DETECTED = 12
    OVER_POWER_OCCURRED = 13
    UNKNOWN_ERROR = 14


class PhoxXLaser(microscope.abc.SerialDeviceMixin, microscope.abc.LightSource):
    """Control and query an Omicron laser/LED device."""

    def __init__(self, com, baud=9600, timeout=2.0, **kwargs):
        super().__init__(**kwargs)
        self.connection = serial.Serial(
            port=com,
            baudrate=baud,
            timeout=timeout,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE
        )
        self._conn = self.connection
        self.temporal_power = 0.0
        self._initialize_device()

    @microscope.abc.SerialDeviceMixin.lock_comms
    def _initialize_device(self):
        firmware = self._ask(b"GFw")
        self.model_code, self.device_id, self.firmware_version = firmware[:3]
        self.serial_number = self._ask(b"GSN")[0]
        specs = self._ask(b"GSI")
        self.wavelength, self.power = specs[:2]
        self.max_power = float(self._ask(b"GMP")[0])

    @microscope.abc.SerialDeviceMixin.lock_comms
    def _ask(self, command: bytes) -> list[str]:
        self._conn.write(b"?" + command + b"|\r")
        return self._conn.read_until(b'\r').decode("Latin1")[4:].strip().split("|")

    @microscope.abc.SerialDeviceMixin.lock_comms
    def _ask_bytes(self, command: bytes) -> bytes:
        self._conn.write(b"?" + command + b"|\r")
        return self._conn.read_until(b'\r')[4:-1]

    @microscope.abc.SerialDeviceMixin.lock_comms
    def _set(self, command: bytes, value: bytes) -> list[str]:
        self._conn.write(b"?" + command + value + b"|\r")
        return self._conn.read_until(b'\r').decode("Latin1")[4:].strip().split("|")

    @microscope.abc.SerialDeviceMixin.lock_comms
    def _process_adhoc(self):
        while (raw := self._conn.read_until(b'\r')) != b'':
            decoded = raw[:-1].decode("Latin1")
            command, content = decoded[:4], decoded[4:].split("|")
            if command.startswith("$TPP"):
                self.temporal_power = float(content[0])

    @microscope.abc.SerialDeviceMixin.lock_comms
    def get_working_hours(self) -> str:
        return self._ask(b"GWH")[0]

    @microscope.abc.SerialDeviceMixin.lock_comms
    def measure_diode_power(self) -> float:
        return float(self._ask(b"MDP")[0])

    @microscope.abc.SerialDeviceMixin.lock_comms
    def measure_temperature_diode(self) -> float:
        return float(self._ask(b"MTD")[0])

    @microscope.abc.SerialDeviceMixin.lock_comms
    def measure_temperature_ambient(self) -> float:
        return float(self._ask(b"MTA")[0])

    @microscope.abc.SerialDeviceMixin.lock_comms
    def get_status(self) -> List[str]:
        raw_status = self._ask_bytes(b"GAS")
        status = Status(raw_status)
        return [f"{key}={value}" for key, value in vars(status).items()]
    #def get_status(self) -> Status:
    #    return Status(self._ask_bytes(b"GAS"))

    @microscope.abc.SerialDeviceMixin.lock_comms
    def get_failure_bytes(self) -> bytes:
        return self._ask_bytes(b"GFB")

    @microscope.abc.SerialDeviceMixin.lock_comms
    def get_latched_failure(self) -> LatchedFailure:
        return LatchedFailure(self._ask_bytes(b"GLF"))

    @microscope.abc.SerialDeviceMixin.lock_comms
    def get_level_power(self) -> int:
        return int(self._ask(b"GLP")[0], 16)  

    def _do_get_power(self) -> float:
         return self.get_level_power() / 65535.0
    
    @microscope.abc.SerialDeviceMixin.lock_comms
    def set_level_power(self, level: int) -> None:
        self._set(b"SLP", hex(level)[2:].encode("Latin1"))

    @microscope.abc.SerialDeviceMixin.lock_comms
    def set_level_power_percent(self, percent: float) -> None:
        level = int((percent / 100.0) * 65535)
        self.set_level_power(level)

    def _do_set_power(self, power: float) -> None:
        percent = max(min(power, 1.0), 0.0) * 100.0
        self.set_level_power_percent(percent)

    @microscope.abc.SerialDeviceMixin.lock_comms
    def get_operation_mode(self) -> OperationMode:
        return OperationMode(self._ask_bytes(b"GOM"))

    @microscope.abc.SerialDeviceMixin.lock_comms
    def set_operation_mode(self, mode: OperationMode) -> None:
        self._set(b"SOM", bytes(mode))

    @microscope.abc.SerialDeviceMixin.lock_comms
    def get_name(self) -> str:
        return self._ask(b"GNA")[0]

    @microscope.abc.SerialDeviceMixin.lock_comms
    def set_name(self, name: str) -> None:
        self._set(b"SNA", name.encode("Latin1"))

    @microscope.abc.SerialDeviceMixin.lock_comms
    def power_off(self) -> None:
        self._set(b"SPO", b"1")

    @microscope.abc.SerialDeviceMixin.lock_comms
    def power_on(self) -> None:
        self._set(b"SPO", b"0")

    @microscope.abc.SerialDeviceMixin.lock_comms
    def get_calibration_wavelengths(self) -> list[int]:
        return [int(w) for w in self._ask(b"GCW")]

    @microscope.abc.SerialDeviceMixin.lock_comms
    def start_calibration(self, wavelength: int) -> CalibrationResult:
        res = int(self._set(b"SCP", hex(wavelength)[2:].encode("Latin1"))[0], 16)
        return CalibrationResult(res)

    @microscope.abc.SerialDeviceMixin.lock_comms
    def start_calibration_safety(self, wavelength: int) -> CalibrationResult:
        res = int(self._set(b"SCS", hex(wavelength)[2:].encode("Latin1"))[0], 16)
        return CalibrationResult(res)

    @microscope.abc.SerialDeviceMixin.lock_comms
    def enable_adhoc_mode(self) -> None:
        self._set(b"SAH", b"1")

    @microscope.abc.SerialDeviceMixin.lock_comms
    def disable_adhoc_mode(self) -> None:
        self._set(b"SAH", b"0")

    @microscope.abc.SerialDeviceMixin.lock_comms
    def _calculate_target_value(self, percent: float, bits: int) -> int:
        return int((percent / 100.0) * (2 ** bits - 1))

    @microscope.abc.SerialDeviceMixin.lock_comms
    def set_power_level_percent(self, percent: float) -> None:
        self._set(b"SLP", f"{self._calculate_target_value(percent, 16):04x}".encode("Latin1"))

    @microscope.abc.SerialDeviceMixin.lock_comms
    def get_is_on(self) -> bool:
        return self.get_status().on

    @microscope.abc.SerialDeviceMixin.lock_comms
    def enable(self) -> None:
        if not self.get_is_on():
            self._set(b"LC1", b"")

    @microscope.abc.SerialDeviceMixin.lock_comms
    def disable(self) -> None:
        if self.get_is_on():
            self._set(b"LC0", b"")

@microscope.abc.SerialDeviceMixin.lock_comms
def run_omicron_laser_example():
    logging.basicConfig(level=logging.DEBUG)

    try:
        with serial.Serial('COM14', 9600, timeout=1) as connection:
            omicron_laser = PhoxXLaser(connection)

            logging.info(f"Laser Model: {omicron_laser.model_code}")
            logging.info(f"Serial Number: {omicron_laser.serial_number}")
            logging.info(f"Firmware Version: {omicron_laser.firmware_version}")

            omicron_laser.enable()
            logging.info(f"Laser Power (before setting): {omicron_laser.get_level_power()}")

            omicron_laser.set_level_power_percent(50.0)
            logging.info(f"Laser Power (after setting to 50%): {omicron_laser.get_level_power()}")

            omicron_laser.power_off()

    except Exception as e:
        logging.error(f"An error occurred: {e}")


#if __name__ == "__main__":
#    run_omicron_laser_example()
        
    