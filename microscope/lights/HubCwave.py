import time
import sys
import traceback
import typing
import inspect
import logging
import microscope
from cwave import *
import microscope.abc

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
_logger = logging.getLogger(__name__)

 

#def error_handling(self):
#    def wrapper(*args, **kwargs):
#        error_message = ""
#        try:
#            result = function()
#            return result
#        except Exception as e:
#            _logger.error(f"Exception type: {type(e).__name__}")
#            _logger.error(f"Exception args: {e.args}")
#            _logger.error("Traceback:")
#            traceback.print_tb(e.__traceback__)
#            tracebackmessage = traceback.format_tb(e.__traceback__)
#            # Retrieve the last n lines of code from the traceback
#            stack = traceback.extract_tb(sys.exc_info()[2])
#            line_number = stack[-1].lineno
#            function = stack[-1].name
#            source_code = inspect.getsourcelines(inspect.getmodule(inspect.currentframe()))[0]
#            relevant_code = source_code[line_number-10: line_number]
#            _logger.error(f"Formatted Traceback Message:")
#            _logger.error("".join(tracebackmessage))
#            _logger.error(f"line {line_number}, in {function}:")
#            _logger.error("Relevant code snippet:")
#            _logger.error("".join(relevant_code))
#    return wrapper


#class HubCwave(microscope.abc.LightSource)
class HubCwave():      
    def __init__(self, address, port, **kwargs):
        super().__init__(**kwargs)
        self.address = address
        self.port = port
        self._cwave = CWave()
        self.hubconnect()
        #try:
        #    self.cwave.connect(address, port)
        #    _logger.info(f"Connected to CWave at {address}:{port}")
        #except ConnectionError as e:
        #    _logger.error(f"Falied to connect to CWave: {e}", exc_info=True)
        #    raise

#    @error_handling
    def hubconnect(self):
        self._cwave.connect(address, port)
        print("Connection established successfully")

#    @error_handling
    def get_status(self) -> typing.List[str]:
        log = self._cwave.get_log()
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

#    @error_handling
    def enable(self) -> None:
        self._cwave.set_laser(True)
        _logger.info("Laser enabled")
        
#    @error_handling    
    def get_is_on(self) -> bool:
        return self._cwave.get_laser()
        
#    @error_handling    
    def _do_get_power(self) -> float:
        log = self._cwave.get_log()
        pd_signal = log.pdSignal
        max_pd_signal = 1000.0
        return min(max(pd_signal / max_pd_signal, 0.0), 1.0)
        
#    @error_handling
    def set_pd_signal(self, pd_signal: int) -> None:
        # Sets the photodiode signal
        assert isinstance(pd_signal, int)
        if pd_signal < 0 or pd_signal > 1000:
            raise ValueError("pd_signal must be between 0 and 1000")
        response = self._cwave.__query_value("pd_signal", pd_signal)
        if response != "OK":
            raise RuntimeError(f"Failed to set pd_signal. Device response: {response}")
        _logger.info(f"Set pd_signal to {pd_signal}")
        
#    @error_handling
    def _do_set_power(self, power: float) -> None:
        max_pd_signal = 1000.0
        pd_signal = int(power * max_pd_signal)
        self.set_pd_signal(pd_signal)

    def get_set_power(self) -> float:
        return super().get_set_power()
    
#    @error_handling
    def disable(self) -> None:
        self._cwave.set_laser(False)
        self._cwave.disconnect()
        _logger.info("Laser disabled and disconnected")

#    @error_handling        
    def hardware_bits(self) -> bool:
        return self._cwave.test_status_bits()
        
#    @error_handling
    def set_initial_mode(self, mode: str) -> None:
        if mode =="VIS":
            self._cwave.set_shutter(ShutterChannel.LaserOut, True) 
            self._cwave.set_shutter(ShutterChannel.OpoOut, False)
        elif mode =="IR":
            self._cwave.set_shutter(ShutterChannel.OpoOut, True)
            self._cwave.set_shutter(ShutterChannel.LaserOut, False)
        else:
            raise ValueError("Invalid mode. Expected 'VIS' or 'IR'")
        _logger.info(f"Initial mode set to {mode}")
            
#    @error_handling        
    def change_wavelength(self, wavelength: float) -> None:
        self._cwave.dial(wavelength, request_shg=False)
        while not self._cwave.get_dial_done():
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
            
#    @error_handling
    def get_temp_setpoint(self, channel: TemperatureChannel) -> float:
        return self._cwave.get_temperature_setpoint(channel)

#    @error_handling
    def set_temp_setpoint(self, channel:TemperatureChannel, setpoint: float) -> None:
        assert isinstance(setpoint, (float, int))
        if setpoint < 0:
            raise ValueError("setpoint must be positive")
        self._cwave.set_temperature_setpoint(channel, setpoint)
        _logger.info(f"Set temperature setpoint for {channel} to {setpoint}")
        
#    @error_handling
    def get_shutter(self, shutter: ShutterChannel) -> bool:
        return self._cwave.get_shutter(shutter)
        
#    @error_handling
    def set_shutter(self, shutter: ShutterChannel, open_shutter: bool) -> None:
        self._cwave.set_shutter(shutter, open_shutter)
        state = "open" if open_shutter else "closed"
        _logger.info(f"Set shutter {shutter} to {state}")
        
#    @error_handling
    def get_piezo_mode(self, channel:PiezoChannel) -> PiezoMode:
        return self._cwave.get_piezo_mode(channel)
        
#    @error_handling
    def set_piezo_mode(self, channel: PiezoChannel, mode: PiezoMode) -> None:
        self._cwave.set_piezo_mode(channel, mode)
        _logger.info(f"Set piezo mode for {channel} to {mode}")
        
#    @error_handling
    def get_galvo_position(self) -> int:
        return self._cwave.get_galvo_position()
        
#    @error_handling
    def set_galvo_position(self, position: int) -> None:
        assert isinstance (position, int)
        self._cwave.set_galvo_position(position)
        _logger.info(f"Set galvo position to {position}")
        
#    @error_handling
    def get_mirror_position(self) -> bool:
        return self._cwave.get_mirror()
        
#    @error_handling
    def set_mirror_position(self, position: bool) -> None:
        assert isinstance(position, bool)
        self._cwave.set_mirror(position)
        state = "position 1" if position else "position 0"
        _logger.info(f"Set mirror to {state}")

    def status_summary(self):
        return self._cwave.get_log()
    
    def process_user_input(self):
        while True:
            print("\nCommands:")
            print("1. Get Dial done")
            print("2. Get Temperature setpoint")
            print("3. Get Logs")
            print("4. Get Shutters")
            print("5. Get Piezo mode")
            print("6. Get Galvo position")
            print("7. Get Mirror position")
            print("12. Exit")

            choice = input("Enter your choice: ")
            if choice == '1':
                dial = self.change_wavelength()
                print(dial)

            elif choice == '2':
                temp_setpoint = self.get_temp_setpoint()
                print(temp_setpoint)

            elif choice == '3':
                print(self.get_status())


            elif choice == '4':
                print(self.get_shutter())

            elif choice == '5':
                print(self.get_piezo_mode)


            elif choice == '6':
                print(self.get_galvo_position())


            elif choice == '7':
                print(self.get_mirror_position())

            elif choice == '12':
                break
            else:
                print("Invalid choice. Please try again.")

# Example of usage:
if __name__ == "__main__":
    address = "192.168.0.4"
    port = 10001
    controller = HubCwave(address, port)
    controller.hubconnect()
    controller.enable()
    