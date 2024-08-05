import time
import logging
import microscope
from cwave import *

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
_logger = logging.getLogger(__name__)

class HubnerCwave(microscope.abc.LightSource):
    # Cwave tunable lasers offer several tuning mechanisms, 
    # ranging from a fully automated wavelength approach 
    # to truly continuous mode-hop free scans over tens of GHz

    def __init__(self, ip='192.168.0.4', port=10001):
        self.ip = ip
        self.port = port
        self._cwave = CWave(ip, port)
        self.connect()
        _logger.info(f"Laser started at {self.ip}:{self.port}")

    def connect(self):
        self._cwave.connect()

    def disconnect(self):
        self._cwave.disconnect()

    def set_initial_mode(self, simulator, mode):
        if mode =="VIS":
            simulator.set_shutter(ShutterChannel.LaserOut, True) 
            simulator.set_shutter(ShutterChannel.OpoOut, False)
        elif mode =="IR":
            simulator.set_shutter(ShutterChannel.OpoOut, True)
            simulator.set_shutter(ShutterChannel.LaserOut, False)
        _logger.info(f"Initial mode set to {mode}.")

    def choose_mode(self):
        mode = input("Choose mode (VIS or IR): ").strip().upper()
        if mode not in ["VIS", "IR"]:
            print("Invalid mode. Please choose 'VIS' or 'IR'")
            return
        self.set_initial_mode(self.simulator, mode)

    def change_wavelength(self, simulator, wavelength):
        simulator.dial(wavelength, request_shg=False)
        while not simulator.get_dial_done():
            _logger.info("Waiting for dial operation to complete...")
            time.sleep(20)
        _logger.info(f"Wavelength changed to {wavelength} nm")

    def input_wavelength(self):
        while True:
            try:
                wavelength = float(input("Enter the desired wavelength in nm: ").strip())
                self.change_wavelength(self.simulator, wavelength)
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
        temperature_setpoint = float(self.simulator.__query('t{}_set?'.format(channel.value)))/1000
        _logger.debug(f"Temperature setpoint for channel {channel.value}: {temperature_setpoint}")
        return temperature_setpoint

    def get_mapping_temperature(self, channel: MappingChannel, wavelength: float) -> float:
        '''Gets corresponding temperature of a wavelength according to mapping'''
        assert isinstance(wavelength, (int, float))
        mapping_temperature = float(
            self.simulator.__query('mapping_{}?{}'.format(channel.value, int(wavelength*100))).split(':')[1]
        )/1000
        _logger.debug(f"Mapping temperature for channel {channel.value} at wavelength {wavelength}: {mapping_temperature}")
        return mapping_temperature

    def get_opoLock_status(self) -> bool:
        '''Gets the OpoLock status'''
        status = self.simulator.opoLock()
        _logger.debug(f"OpoLock status: {status}")
        return status

# Example of usage:
if __name__ == "__main__":
    controller = HubnerCwave()
    controller.process_user_input()