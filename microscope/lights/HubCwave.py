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
        try:
            self.cwave.connect(address="192.168.0.4", port=10001)
            _logger.info(f"Connected to CWave at {address}:{port}")
        except Exception as e:
            _logger.error(f"Falied to connect to CWave: {e}")
            raise

    def get_status(self) -> typing.List[str]:
        try:
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
        except Exception as e:
            _logger.error(f"Failed to get status: {e}")
            raise

    def enable(self) -> None:
        try:
            self.cwave.set_laser(True)
            _logger.info("Laser enabled")
        except Exception as e:
            _logger.error(f"Failed to enable laser: {e}")
            raise

    def get_is_on(self) -> bool:
        try:
            return self.cwave.get_laser()
        except Exception as e:
            _logger.error(f"Failed to get laser status")
            raise
    
    def _do_get_power(self) -> float:
        try:
            log = self.cwave.get_log()
            pd_signal = log.pdSignal
            max_pd_signal = 1000.0
            return min(max(pd_signal / max_pd_signal, 0.0), 1.0)
        except Exception as e:
            _logger.error(f"Failed to get power: {e}")
            raise
    
    def set_pd_signal(self, pd_signal: int) -> None:
        # Sets the photodiode signal
        assert isinstance(pd_signal, int)
        if pd_signal < 0 or pd_signal > 1000:
            raise ValueError("pd_signal must be between 0 and 1000")
        try:
            response = self.cwave.__query_value("pd_signal", pd_signal)
            if response != "OK":
                raise RuntimeError(f"Failed to set pd_signal. Device response: {response}")
            _logger.info(f"Set pd_signal to {pd_signal}")
        except Exception as e:
            _logger.error(f"Failed to set pd_signal: {e}")
            raise
    
    def _do_set_power(self, power: float) -> None:
        max_pd_signal = 1000.0
        pd_signal = int(power * max_pd_signal)
        self.set_pd_signal(pd_signal)

    def get_set_power(self) -> float:
        return super().get_set_power()
    
    def disable(self) -> None:
        try:
            self.cwave.set_laser(False)
            self.cwave.disconnect()
            _logger.info("Laser disabled and disconnected")
        except Exception as e:
            _logger.error(f"Failed to disable laser: {e}")
            raise
    
    def hardware_bits(self):
        try:
            return self.cwave.test_status_bits()
        except Exception as e:
            _logger.error(f"Failed to test status bits: {e}")
            raise
    
    def set_initial_mode(self, mode):
        try:
            if mode =="VIS":
                self.cwave.set_shutter(ShutterChannel.LaserOut, True) 
                self.cwave.set_shutter(ShutterChannel.OpoOut, False)
            elif mode =="IR":
                self.cwave.set_shutter(ShutterChannel.OpoOut, True)
                self.cwave.set_shutter(ShutterChannel.LaserOut, False)
            else:
                raise ValueError("Invalid mode. Expected 'VIS' or 'IR'")
            _logger.info(f"Initial mode set to {mode}")
        except Exception as e:
            _logger.error(f"Failed to set initial mode: {e}")
            raise
    
    def change_wavelength(self, wavelength):
        try:
            self.cwave.dial(wavelength, request_shg=False)
            while not self.cwave.get_dial_done():
                _logger.info("Waiting for dial operation to complete...")
                time.sleep(20)
            _logger.info(f"Wavelength changed to {wavelength} nm")
        except Exception as e:
            _logger.error(f"Failed to change wavelength: {e}")
            raise

    def input_wavelength(self):
        while True:
            try:
                wavelength = float(input("Enter the desired wavelength in nm: ").strip())
                self.change_wavelength(self.cwave, wavelength)
                break
            except ValueError:
                print("Invalid input. Please enter a numeric value.")
            except Exception as e:
                _logger.error(f"Failed to input wavelength: {e}")
                raise

    def get_temp_setpoint(self, channel: TemperatureChannel) -> float:
        try:
            return self.cwave.get_temperature_setpoint(channel)
        except Exception as e:
            _logger.error(f"Failed to get temperature setpoint for {channel}")
            raise

    def set_temp_setpoint(self, channel:TemperatureChannel, setpoint: float) -> None:
        assert isinstance(setpoint, (float, int))
        if setpoint < 0:
            raise ValueError("setpoint must be positive")
        try:
            self.cwave.set_temperature_setpoint(channel, setpoint)
            _logger.info(f"Set temperature setpoint for {channel} to {setpoint}")
        except Exception as e:
            _logger.error(f"Failed to set temperature setpoint for {channel}: {e}")
            raise

    def get_shutter(self, shutter: ShutterChannel) -> bool:
        try:
            return self.cwave.get_shutter(shutter)
        except Exception as e:
            _logger.error(f"Failed to get shutter state for {shutter}")
            raise

    def set_shutter(self, shutter: ShutterChannel, open_shutter: bool) -> None:
        try: 
            self.cwave.set_shutter(shutter, open_shutter)
            state = "open" if open_shutter else "closed"
            _logger.info(f"Set shutter {shutter} to {state}")
        except Exception as e:
            _logger.error(f"Failed to set shutter state for {shutter}: {e}")
            raise

    def get_piezo_mode(self, channel:PiezoChannel) -> PiezoMode:
        try:
            return self.cwave.get_piezo_mode(channel)
        except Exception as e:
            _logger.error(f"Failed to get piezo mode for {channel}: {e}")
            raise

    def set_piezo_mode(self, channel: PiezoChannel, mode: PiezoMode) -> None:
        try:
            self.cwave.set_piezo_mode(channel, mode)
            _logger.info(f"Set piezo mode for {channel} to {mode}")
        except Exception as e:
            _logger.error(f"Failed to set piezo mode for {channel}: {e}")

    def get_galvo_position(self) -> int:
        try:
            return self.cwave.get_galvo_position()
        except Exception as e:
            _logger.error(f"Failed to get galvo position: {e}")
            raise

    def set_galvo_position(self, position: int) -> None:
        assert isinstance (position, int)
        try:
            self.cwave.set_galvo_position(position)
            _logger.info(f"Set galvo position to {position}")
        except Exception as e:
            _logger.error(F"Failed to set galvo position: {e}")
            raise

    def get_mirror_position(self) -> bool:
        try:
            return self.cwave.get_mirror()
        except Exception as e:
            _logger.error(f"Failed to get mirror position: {e}")

    def set_mirror_position(self, position: bool) -> None:
        assert isinstance(position, bool)
        try:
            self.cwave.set_mirror(position)
            state = "position 1" if position else "position 0"
            _logger.info(f"Set mirror to {state}")
        except Exception as e:
            _logger.error(f"Failed to set mirror position: {e}")
            raise

    def status_summary(self):
        return self.cwave.get_log()


    


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