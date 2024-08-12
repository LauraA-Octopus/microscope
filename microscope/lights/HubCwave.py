import time
import logging
import microscope
from cwave import *
import microscope.abc

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
_logger = logging.getLogger(__name__)


def SomeSpecificException(Exception):
    # Define here specific exceptions for specific items (not sure this is needed)
    pass

def with_error_handling(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SomeSpecificException as e:
            _logger.error(f"An error occurred in {func.__name__}: {e}")
            raise
        except Exception as e:
            _logger.error(f"Unexpected error in {func.__name__}: {e}")
            raise
    return wrapper
class HubCwave(microscope.abc.LightSource):
    def __init__(self, address: str, port: int):
        super().__init__()
        self.cwave = CWave()
        try:
            self.cwave.connect(address="192.168.0.4", port=10001)
            _logger.info(f"Connected to CWave at {address}:{port}")
        except ConnectionError as e:
            _logger.error(f"Falied to connect to CWave: {e}", exc_info=True)
            raise

    @with_error_handling
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

    @with_error_handling
    def enable(self) -> None:
        self.cwave.set_laser(True)
        _logger.info("Laser enabled")
        
    @with_error_handling    
    def get_is_on(self) -> bool:
        return self.cwave.get_laser()
        
    @with_error_handling    
    def _do_get_power(self) -> float:
        log = self.cwave.get_log()
        pd_signal = log.pdSignal
        max_pd_signal = 1000.0
        return min(max(pd_signal / max_pd_signal, 0.0), 1.0)
        
    @with_error_handling
    def set_pd_signal(self, pd_signal: int) -> None:
        # Sets the photodiode signal
        assert isinstance(pd_signal, int)
        if pd_signal < 0 or pd_signal > 1000:
            raise ValueError("pd_signal must be between 0 and 1000")
        response = self.cwave.__query_value("pd_signal", pd_signal)
        if response != "OK":
            raise RuntimeError(f"Failed to set pd_signal. Device response: {response}")
        _logger.info(f"Set pd_signal to {pd_signal}")
        
    @with_error_handling
    def _do_set_power(self, power: float) -> None:
        max_pd_signal = 1000.0
        pd_signal = int(power * max_pd_signal)
        self.set_pd_signal(pd_signal)

    def get_set_power(self) -> float:
        return super().get_set_power()
    
    @with_error_handling
    def disable(self) -> None:
        self.cwave.set_laser(False)
        self.cwave.disconnect()
        _logger.info("Laser disabled and disconnected")

    @with_error_handling        
    def hardware_bits(self) -> bool:
        return self.cwave.test_status_bits()
        
    @with_error_handling
    def set_initial_mode(self, mode: str) -> None:
        if mode =="VIS":
            self.cwave.set_shutter(ShutterChannel.LaserOut, True) 
            self.cwave.set_shutter(ShutterChannel.OpoOut, False)
        elif mode =="IR":
            self.cwave.set_shutter(ShutterChannel.OpoOut, True)
            self.cwave.set_shutter(ShutterChannel.LaserOut, False)
        else:
            raise ValueError("Invalid mode. Expected 'VIS' or 'IR'")
        _logger.info(f"Initial mode set to {mode}")
            
    @with_error_handling        
    def change_wavelength(self, wavelength: float) -> None:
        self.cwave.dial(wavelength, request_shg=False)
        while not self.cwave.get_dial_done():
            _logger.info("Waiting for dial operation to complete...")
            #time.sleep(20)
        _logger.info(f"Wavelength changed successfully to {wavelength} nm")

    def input_wavelength(self) -> None:
        while True:
            try:
                wavelength = float(input("Enter the desired wavelength in nm: ").strip())
                self.change_wavelength(wavelength)
                break
            except ValueError:
                print("Invalid input. Please enter a numeric value.")
            except Exception as e:
                _logger.error(f"Falied to input wavelength: {e}", exc_info=True)
                raise
            
    @with_error_handling
    def get_temp_setpoint(self, channel: TemperatureChannel) -> float:
        return self.cwave.get_temperature_setpoint(channel)

    @with_error_handling
    def set_temp_setpoint(self, channel:TemperatureChannel, setpoint: float) -> None:
        assert isinstance(setpoint, (float, int))
        if setpoint < 0:
            raise ValueError("setpoint must be positive")
        self.cwave.set_temperature_setpoint(channel, setpoint)
        _logger.info(f"Set temperature setpoint for {channel} to {setpoint}")
        
    @with_error_handling
    def get_shutter(self, shutter: ShutterChannel) -> bool:
        return self.cwave.get_shutter(shutter)
        
    @with_error_handling
    def set_shutter(self, shutter: ShutterChannel, open_shutter: bool) -> None:
        self.cwave.set_shutter(shutter, open_shutter)
        state = "open" if open_shutter else "closed"
        _logger.info(f"Set shutter {shutter} to {state}")
        
    @with_error_handling
    def get_piezo_mode(self, channel:PiezoChannel) -> PiezoMode:
        return self.cwave.get_piezo_mode(channel)
        
    @with_error_handling
    def set_piezo_mode(self, channel: PiezoChannel, mode: PiezoMode) -> None:
        self.cwave.set_piezo_mode(channel, mode)
        _logger.info(f"Set piezo mode for {channel} to {mode}")
        
    @with_error_handling
    def get_galvo_position(self) -> int:
        return self.cwave.get_galvo_position()
        
    @with_error_handling
    def set_galvo_position(self, position: int) -> None:
        assert isinstance (position, int)
        self.cwave.set_galvo_position(position)
        _logger.info(f"Set galvo position to {position}")
        
    @with_error_handling
    def get_mirror_position(self) -> bool:
        return self.cwave.get_mirror()
        
    @with_error_handling
    def set_mirror_position(self, position: bool) -> None:
        assert isinstance(position, bool)
        self.cwave.set_mirror(position)
        state = "position 1" if position else "position 0"
        _logger.info(f"Set mirror to {state}")
        

    def status_summary(self):
        return self.cwave.get_log()

# Example of usage:
if __name__ == "__main__":
    controller = HubCwave(address="192.168.0.4",port= 10001)
    controller.enable()
    #controller.process_user_input()
    


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
