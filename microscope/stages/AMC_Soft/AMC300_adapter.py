import time
import sys
import microscope

sys.path.append('../')
import AMC

class AMC300Adapter(microscope.abc.Stage):

    def __init__(self, ip, port):
        super().__init__()
        self.ip = ip
        self.port = port
        self.amc = AMC.Device(ip, port)
        self.timeout = 30 #TODO: check this value
        self._axis_map = {'x' : 0, 'y' : 1, 'z' : 2}

    def connect(self):
        self.amc.connect()

    def close(self):
        self.amc.close()


    def move_to(self, axis_name, position_um):
        if axis_name not in self.axes:
            print("Invalid axis name. Command not sent")
            return
        
        axis = self.axes[axis_name]
        position_nm = position_um * 1000
        if axis_name in ['x', 'y']:
            if not (100 * 1000 <= position_nm <= 5900 * 1000):
                print("Position out of permitted range. Command not sent")
                return
        elif axis_name == 'z':
            if not (1000 * 1000 <= position_nm <= 5000 * 1000):
                print("Position out of permitted range. Command not sent")
                return
        else:
            print("Invalid axis. Command not sent")
            return
        
        # If the AMC methods cannot handle strings and require numericals as axis,
        # we can map back to numerical to pass the command, 
        # using: axis_index = axis.index instead of axis_name in the self.amc.methods
        self.amc.move.setControlTargetPosition(axis_name, position_nm)
        self.amc.control.setControlMove(axis_name, True)

        # Check if the axis starts moving within the timeout period
        if not self.get_moving_status(axis_name):
            print(f"Timeout: Axis {axis_name} did not start moving within {self.timeout} seconds")
            self.amc.control.setControlMove(axis_name, False) # stop the axis
            return

        # Get the current time
        start_time = time.time()
        
        # Wait for the axis to reach the target position
        while not self.amc.status.getStatusTargetRange(axis_name):
            # Check for timeout
            if time.time() - start_time > self.timeout:
                print(f"Timeout: axis {axis_name} did not reach the target position within {self.timeout} seconds.")
                self.amc.control.setControlMove(axis_name, False)
                return
            
            # Read out position in nm
            current_position = self.amc.move.getPosition(axis_name)
            print(current_position)
            time.sleep(0.1)

        # Stop approach
        self.amc.control.setControlMove(axis_name, False)
        print(f"Axis {axis_name} reached the target position successfully")

    # Implementing this function to be compatible with python-microscope structure
    def get_position(self, axis_name):
        # Retrieve the current position of the specified axis
        current_position_nm = self.amc.move.getPosition(axis_name)
        current_position_um = current_position_nm / 1000.0
        return current_position_um

    def get_moving_status(self, axis_name):
        start_time = time.time()

        while True:
            # Call getStatusMoving method to retrieve the moving status of all axes
            moving_status = self.amc.control.getStatusMovingAllAxes()

            # Print status for debugging
            print("Moving Status:", moving_status)

            # Check if any axis is moving
            if any(moving_status):
                print("At least one axis is moving")
                return True
            
            # Check for timeout
            if time.time() - start_time > self.timeout:
                print("Timeout: No axis is moving within", self.timeout, "seconds")
                return False
            
            # Add short delay before checking again
            time.sleep(0.1)

    def move_by_rough(self, axis_name, direction):
        if axis_name == 'x' or axis_name == 'y':
            distance = 100  #TODO: ask Tom/Benji about sensible values
            if direction == "positive":
                self.move_to_position(axis_name, self.amc.move.getPosition(axis_name) + distance)
            elif direction == "negative":
                self.move_to_position(axis_name, self.amc.move.getPosition(axis_name) - distance)
            else:
                print("Invalid direction. Please specify 'positive' or 'negative' for axis x and y")
        elif axis_name == 'z':
            distance = 50 #TODO: ask Tom/Benji about sensible values
            if direction == "positive":
                self.move_to_position(axis_name, self.amc.move.getPosition(axis_name) + distance)
            elif direction == "negative":
                self.move_to_position(axis_name, self.amc.move.getPosition(axis_name) - distance)
            else:
                print("Invalid axis. Please specify axis x, y or z")

    def move_by_fine(self, axis_name, direction):
        if axis_name == 'x' or axis_name == 'y':
            distance = 10 #TODO: ask Tom/Benji about sensible values
            if direction == "positive":
                self.move_to_position(axis_name, self.amc.move.getPosition(axis_name) + distance)
            elif direction == "negative":
                self.move_to_position(axis_name, self.amc.move.getPosition(axis_name) - distance)
            else:
                print("Invalid direction. Please specify a 'positive' or 'negative' direction")
        elif axis_name == 'z':
            distance = 5 #TODO: ask Tom/Benji about sensible values
            if direction == "positive":
                self.move_to_position(axis_name, self.amc.move.getPosition(axis_name) + distance)
            elif direction == "negative":
                self.move_to_position(axis_name, self.amc.move.getPosition(axis_name) - distance)
            else:
                print("invalid axis. Please specify axis x, y or z")

    def set_frequency(self, axis_name, frequency):
        if not (3 <= frequency <= 5000):
            print("Frequency out of permitted range. Command not sent")
            return 
        if self.amc.control.setControlFrequency(axis_name, frequency):
            print(f"Frequency set successfully for axis {axis_name}")
        else:
            print(f"Failed to set frequency fpr axis {axis_name}")

    def set_amplitude(self, axis_name, amplitude):
        if not (0 <= amplitude <= 60):
            print("Amplitude out of permitted range. Command not sent")
            return 
        if self.amc.control.setControlAmplitude(axis_name, amplitude):
            print(f"Amplitude set successfully for axis {axis_name}")
        else:
            print(f"Failed to set amplitude for axis {axis_name}")

    def get_frequency(self, axis_name):
        return self.amc.control.getControlFrequency(axis_name)

    def get_pos_and_freq(self):    #, axis, position, frequency):
        return self.amc.control.getPositionsAndVoltages()

    def get_amplitude(self, axis_name):
        return self.amc.control.getControlAmplitude(axis_name)

    def get_piezo_amplitude(self, axis_name):
        return self.amc.control.getCurrentOutputVoltage(axis_name)

    def home(self):
        self.move_to_position(self.axes('x'), 3984.1)
        self.move_to_position(self.axes('y'), 3075.7)
        self.move_to_position(self.axes('z'), 4539.6)
        print("Axes homed successfully.")

    def _do_shutdown(self) -> None:
        pass

    @property
    def axes(self):
        # Mapping from string axis names to their corresponding hardware indices
        return {name: self.amc.move.getAxis(index) for name, index in self._axis_map.items()}

    @property
    def limits(self):
        return {name: axis.limits for name, axis in self.axes.items()}
    
    def may_move_on_enable(self):
        pass

    def process_user_input(self):
        while True:
            print("\nCommands:")
            print("1. Move to position")
            print("2. Get moving status")
            print("3. Rough jog")
            print("4. Fine jog")
            print("5. Set frequency")
            print("6. Set amplitude")
            print("7. Get frequency")
            print("8. Get amplitude")
            print("9. Get position and frequency")
            print("10. Get piezo amplitude (mV)")
            print("11. Home axes")
            print("12. Exit")

            choice = input("Enter your choice: ")

            if choice == '1':
                axis = int(input("Enter axis number (x, y, or z): "))
                position_um = float(input("Enter target position (um): "))
                self.move_to(axis, position_um)

            elif choice == '2':
                #axis = int(input("Enter axis number (0, 1, or 2): "))
                self.get_moving_status()

            elif choice == '3':
                axis = int(input("Enter axis number (x, y, or z): "))
                direction = input("Enter 'positive' or 'negative' direction: ")
                self.move_by_rough(axis, direction)

            elif choice == '4':
                axis = int(input("Enter axis number (x, y, or z): "))
                direction = input("Enter a 'positive' or 'negative' direction: ")
                self.move_by_fine(axis, direction)

            elif choice == '5':
                axis = int(input("Enter axis number (x, y, or z): "))
                frequency = float(input("Enter frequency (Hz): "))
                self.set_frequency(axis, frequency)

            elif choice == '6':
                axis = int(input("Enter axis number (x, y, or z): "))
                amplitude = float(input("Enter amplitude (V): "))
                self.set_amplitude(axis, amplitude)

            elif choice == '7':
                axis = int(input("Enter axis number (x, y, or z): "))
                print(f"Frequency for axis {axis}: {self.get_frequency(axis)}")

            elif choice == '8':
                axis = int(input("Enter axis number (x, y, or z): "))
                print(f"Amplitude for axis {axis}: {self.get_amplitude(axis)}")

            elif choice == '9':
                #axis = int(input("Enter axis number (0, 1, or 2): "))
                #position = float(input("Enter target position (um): "))
                #frequency = float(input("Enter frequency (Hz): "))
                print(f"Position and Frequency for the three axes are: {self.get_pos_and_freq()}")
            
            elif choice == '10':
                axis = int(input("Enter axis number (x, y, or z): "))
                print(f"The piezo amplitude for axis {axis} is: {self.get_piezo_amplitude(axis)} mV")

            elif choice == '11':
                self.home()
            elif choice == '12':
                break
            else:
                print("Invalid choice. Please try again.")

if __name__ == "__main__":
    ip = "192.168.0.2"
    port = 9090
    controller = AMC300Adapter(ip, port)
    controller.connect()
    try:
        controller.process_user_input()
    finally:
        controller.close()
