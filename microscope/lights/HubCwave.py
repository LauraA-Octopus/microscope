import time
import logging
import microscope
from cwave import *
import microscope.abc

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
_logger = logging.getLogger(__name__)

class Log(typing.NamedTuple):
    temoOpo: float
    tempShg1: float
    tempShg2: float
    tempRef: float
    tempBase: float
    tempBase: float
    tempFpga:float
    pdPump: float
    pdSignal: float
    pdShg: float
    pdReserve: float
    statusBits: int

class HubCwave(microscope.abc.LightSource):
    def __init__(self, address: str, port: int = 10001):
        super().__init__()
        self.cwave = CWave()
        self.cwave.connect(address="192.168.0.4", port=10001)

    def get_status(self) -> typing.List[str]:
        log = self.cwave.get_log()
        return[
            f"TempOpo: {log.tempOpo}",
            f"TempShg1: {log.tempShg1}",
            f"TempShg2: {log.tempShg2}",
            f"TempRef: {log.tempRef}",
            f"TempBase: {log.tempBase}",
            f"TempFpga: {log.tempFpga}",
            f"PdPump: {log.pdPump}",
            f"PdSignal: {log.pdSignal}",
            f"PdShg: {log.pdShg}",
            f"PdReserve: {log.pdReserve}",
            f"StatusBits: {log.statusBits}"
        ]

    def get_is_on(self) -> bool:
        return self.cwave.get_laser()
    
    def _do_get_power(self) -> float:
        log = self.cwave.get_log()
        pd_signal = log.pdSignal
        max_pd_signal = 1000.0
        return min(max(pd_signal / max_pd_signal, 0.0), 1.0)
    
    def set_pd_signal(self, pd_signal: int) -> None:
        # Sets the photodiode signal
        assert isinstance(pd_signal, int)
        self.__query_value('pd_signal', pd_signal)
    
    def _do_set_power(self, power: float) -> None:
        max_pd_signal = 1000.0
        pd_signal = int(power * max_pd_signal)
        self.cwave.set_pd_signal(pd_signal)
    
    def enable(self) -> None:
        return self.cwave.set_laser(True)
    
    def disable(self) -> None:
        return self.cwave.set_laser(False)
    
    def hardware_bits(self):
        return self.cwave.test_status_bits()
    
    def change_wavelength(self, wavelength):
        self.cwave.dial(wavelength, request_shg=False)
        while not self.cwave.get_dial_done():
            _logger.info("Waiting for dial operation to complete...")
            time.sleep(20)
        _logger.info(f"Wavelength changed to {wavelength} nm")

    def input_wavelength(self):
        while True:
            try:
                wavelength = float(input("Enter the desired wavelength in nm: ").strip())
                self.change_wavelength(self.cwave, wavelength)
                break
            except ValueError:
                print("Invalid input. Please enter a numeric value.")


# My first implementation of the class
""" class HubnerCwave(microscope.abc.LightSource):
    # Cwave tunable lasers offer several tuning mechanisms, 
    # ranging from a fully automated wavelength approach 
    # to truly continuous mode-hop free scans over tens of GHz

    def __init__(self, ip='192.168.0.4', port=10001):
        self.ip = ip
        self.port = port
        self.cwave = CWave(ip, port)
        self.cwave.connect()
        _logger.info(f"Laser started at {self.ip}:{self.port}")

    def connect(self):
        self.cwave.connect()

    def disconnect(self):
        self.cwave.disconnect()

    def set_initial_mode(self, mode):
        if mode =="VIS":
            self.cwave.set_shutter(ShutterChannel.LaserOut, True) 
            self.cwave.set_shutter(ShutterChannel.OpoOut, False)
        elif mode =="IR":
            self.cwave.set_shutter(ShutterChannel.OpoOut, True)
            self.cwave.set_shutter(ShutterChannel.LaserOut, False)
        _logger.info(f"Initial mode set to {mode}.")

    def choose_mode(self):
        mode = input("Choose mode (VIS or IR): ").strip().upper()
        if mode not in ["VIS", "IR"]:
            print("Invalid mode. Please choose 'VIS' or 'IR'")
            return
        self.set_initial_mode(self.cwave, mode)

    def change_wavelength(self, wavelength):
        self.cwave.dial(wavelength, request_shg=False)
        while not self.cwave.get_dial_done():
            _logger.info("Waiting for dial operation to complete...")
            time.sleep(20)
        _logger.info(f"Wavelength changed to {wavelength} nm")

    def input_wavelength(self):
        while True:
            try:
                wavelength = float(input("Enter the desired wavelength in nm: ").strip())
                self.change_wavelength(self.cwave, wavelength)
                break
            except ValueError:
                print("Invalid input. Please enter a numeric value.")

    def process_user_input(self):
        while True:
            print("\nCommands:")
            print("1. Choose between VIS or IR")
            print("2. Input wavelength in nm")
            print("3. Exit")

            choice = input("Enter your choice: ")

            if choice == "1":
                self.choose_mode()

            elif choice == "2":
                self.input_wavelength()

            elif choice == "3":
                break

            else:
                print("Invalid choice. Please try again")

    def get_temperature_setpoint(self, channel: TemperatureChannel) -> float:
        '''Gets temperature setpoint'''
        assert isinstance(channel, TemperatureChannel)
        temperature_setpoint = float(self.cwave.__query('t{}_set?'.format(channel.value)))/1000
        _logger.debug(f"Temperature setpoint for channel {channel.value}: {temperature_setpoint}")
        return temperature_setpoint

    def get_mapping_temperature(self, channel: MappingChannel, wavelength: float) -> float:
        '''Gets corresponding temperature of a wavelength according to mapping'''
        assert isinstance(wavelength, (int, float))
        mapping_temperature = float(
            self.cwave.__query('mapping_{}?{}'.format(channel.value, int(wavelength*100))).split(':')[1]
        )/1000
        _logger.debug(f"Mapping temperature for channel {channel.value} at wavelength {wavelength}: {mapping_temperature}")
        return mapping_temperature

    def get_opoLock_status(self) -> bool:
        '''Gets the OpoLock status'''
        status = self.cwave.opoLock()
        _logger.debug(f"OpoLock status: {status}")
        return status
 """
# Example of usage:
if __name__ == "__main__":
    controller = HubCwave()
    controller.process_user_input()