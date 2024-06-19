import time
import microscope
import microscope.abc
import microscope._utils
import os

AMC_files = 'C:\\Users\\LSFMICRO\\Documents\\microscope\\microscope\\stages\\AMCsoft\\AMC.py'
AMC = os.path.realpath(AMC_files)
 
class AMC300Adapter(microscope.abc.Stage):
    def __init__(self, ip, port):
        super().__init__(self, ip, port)
        self.ip = ip
        self.port = port
        self.amc = AMC.Device(ip, port)
        self.timeout = 30 #TODO: check this value

    def connect(self):
        self.amc.connect()

    def close(self):
        self.amc.close()


    def move_to(self, axis, position_um):
        position_nm = position_um * 1000
        if axis in [0, 1]:
            if not (100 * 1000 <= position_nm <= 5900 * 1000):
                print("Position out of permitted range. Command not sent")
                return
        elif axis == 2:
            if not (1000 * 1000 <= position_nm <= 5000 * 1000):
                print("Position out of permitted range. Command not sent")
                return
        else:
            print("Invalid axis. Command not sent")
            return
        
        self.amc.move.setControlTargetPosition(axis, position_nm)
        self.amc.control.setControlMove(axis, True)

        # Check if the axis starts moving within the timeout period
        if not self.get_moving_status(axis):
            print(f"Timeout: Axis {axis} did not start moving within {self.timeout} seconds")
            self.amc.control.setControlMove(axis, False) # stop the axis
            return

        # Get the current time
        start_time = time.time()
        
        # Wait for the axis to reach the target position
        while not self.amc.status.getStatusTargetRange(axis):
            # Check for timeout
            if time.time() - start_time > self.timeout:
                print(f"Timeout: axis {axis} did not reach the target position within {self.timeout} seconds.")
                self.amc.control.setControlMove(axis, False)
                return
            
            # Read out position in nm
            current_position = self.amc.move.getPosition(axis)
            print(current_position)
            time.sleep(0.1)

        # Stop approach
        self.amc.control.setControlMove(axis, False)
        print(f"Axis {axis} reached the target position successfully")

    # Implementing this function to be compatible with python-microscope structure
    def get_position(self, axis):
        # Retrieve the current position of the specified axis
        current_position_nm = self.amc.move.getPosition(axis)
        current_position_um = current_position_nm / 1000.0
        return current_position_um

    def get_moving_status(self, axis):
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

    def rough_jog(self, axis, direction):
        if axis == 0 or axis == 1:
            distance = 100  #TODO: ask Tom/Benji about sensible values
            if direction == "positive":
                self.move_to_position(axis, self.amc.move.getPosition(axis) + distance)
            elif direction == "negative":
                self.move_to_position(axis, self.amc.move.getPosition(axis) - distance)
            else:
                print("Invalid direction. Please specify 'positive' or 'negative' for axis 0 and 1")
        elif axis == 2:
            distance = 50 #TODO: ask Tom/Benji about sensible values
            if direction == "positive":
                self.move_to_position(axis, self.amc.move.getPosition(axis) + distance)
            elif direction == "negative":
                self.move_to_position(axis, self.amc.move.getPosition(axis) - distance)
            else:
                print("Invalid axis. Please specify axis 0, 1 or 2")

    def fine_jog(self, axis, direction):
        if axis == 0 or axis == 1:
            distance = 10 #TODO: ask Tom/Benji about sensible values
            if direction == "positive":
                self.move_to_position(axis, self.amc.move.getPosition(axis) + distance)
            elif direction == "negative":
                self.move_to_position(axis, self.amc.move.getPosition(axis) - distance)
            else:
                print("Invalid direction. Please specify a 'positive' or 'negative' direction")
        elif axis == 2:
            distance = 5 #TODO: ask Tom/Benji about sensible values
            if direction == "positive":
                self.move_to_position(axis, self.amc.move.getPosition(axis) + distance)
            elif direction == "negative":
                self.move_to_position(axis, self.amc.move.getPosition(axis) - distance)
            else:
                print("invalid axis. Please specify axis 0, 1 or 2")

    def set_frequency(self, axis, frequency):
        if not (3 <= frequency <= 5000):
            print("Frequency out of permitted range. Command not sent")
            return 
        if self.amc.control.setControlFrequency(axis, frequency):
            print(f"Frequency set successfully for axis {axis}")
        else:
            print(f"Failed to set frequency fpr axis {axis}")

    def set_amplitude(self, axis, amplitude):
        if not (0 <= amplitude <= 60):
            print("Amplitude out of permitted range. Command not sent")
            return 
        if self.amc.control.setControlAmplitude(axis, amplitude):
            print(f"Amplitude set successfully for axis {axis}")
        else:
            print(f"Failed to set amplitude for axis {axis}")

    def get_frequency(self, axis):
        return self.amc.control.getControlFrequency(axis)

    def get_pos_and_freq(self):    #, axis, position, frequency):
        return self.amc.control.getPositionsAndVoltages()

    def get_amplitude(self, axis):
        return self.amc.control.getControlAmplitude(axis)

    def get_piezo_amplitude(self, axis):
        return self.amc.control.getCurrentOutputVoltage(axis)

    def home(self):
        self.move_to_position(0, 3984.1)
        self.move_to_position(1, 3075.7)
        self.move_to_position(2, 4539.6)
        print("Axes homed successfully.")

    def _do_shutdown(self) -> None:
        pass

    def axes(self):
        pass

    def move_by(self, axis, distance):
        pass

    def may_move_on_enable(self):
        pass

#    def process_user_input(self):
#        while True:
#            print("\nCommands:")
#            print("1. Move to position")
#            print("2. Get moving status")
#            print("3. Rough jog")
#            print("4. Fine jog")
#            print("5. Set frequency")
#            print("6. Set amplitude")
#            print("7. Get frequency")
#            print("8. Get amplitude")
#            print("9. Get position and frequency")
#            print("10. Get piezo amplitude (mV)")
#            print("11. Home axes")
#            print("12. Exit")

#            choice = input("Enter your choice: ")

#            if choice == '1':
#                axis = int(input("Enter axis number (0, 1, or 2): "))
#                position_um = float(input("Enter target position (um): "))
#                self.move_to_position(axis, position_um)

#            elif choice == '2':
#                #axis = int(input("Enter axis number (0, 1, or 2): "))
#                self.get_moving_status()

#            elif choice == '3':
#                axis = int(input("Enter axis number (0, 1, or 2): "))
#                direction = input("Enter 'positive' or 'negative' direction: ")
#                self.rough_jog(axis, direction)

#            elif choice == '4':
#                axis = int(input("Enter axis number (0, 1, or 2): "))
#                direction = input("Enter a 'positive' or 'negative' direction: ")
#                self.fine_jog(axis, direction)

#            elif choice == '5':
#                axis = int(input("Enter axis number (0, 1, or 2): "))
#                frequency = float(input("Enter frequency (Hz): "))
#                self.set_frequency(axis, frequency)

#            elif choice == '6':
#                axis = int(input("Enter axis number (0, 1, or 2): "))
#                amplitude = float(input("Enter amplitude (V): "))
#                self.set_amplitude(axis, amplitude)

#            elif choice == '7':
#                axis = int(input("Enter axis number (0, 1, or 2): "))
#                print(f"Frequency for axis {axis}: {self.get_frequency(axis)}")

#            elif choice == '8':
#                axis = int(input("Enter axis number (0, 1, or 2): "))
#                print(f"Amplitude for axis {axis}: {self.get_amplitude(axis)}")

#            elif choice == '9':
                #axis = int(input("Enter axis number (0, 1, or 2): "))
                #position = float(input("Enter target position (um): "))
                #frequency = float(input("Enter frequency (Hz): "))
#                print(f"Position and Frequency for the three axes are: {self.get_pos_and_freq()}")
            
#            elif choice == '10':
#                axis = int(input("Enter axis number (0, 1, or 2): "))
#                print(f"The piezo amplitude for axis {axis} is: {self.get_piezo_amplitude(axis)} mV")

#            elif choice == '11':
#                self.home()
#            elif choice == '12':
#                break
#            else:
#                print("Invalid choice. Please try again.")

if __name__ == "__main__":
    ip = "192.168.0.2"
    port = 9090
    controller = AMC300Adapter(ip, port)
    controller.connect()
    try:
        controller.process_user_input()
    finally:
        controller.close()
