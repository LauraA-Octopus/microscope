import os
import typing
import time
import microscope
import threading
import microscope.abc
import microscope._utils
#from AMC import Device as AMCDevice
from microscope.stages.AMCsoft.AMC import Device as AMCDevice

class AMC300Axis(microscope.abc.StageAxis):

    def __init__(self, amc, index, limits: tuple[float, float], timeout:float, lock):
        self._amc = amc
        self._index = index
        self._limits = microscope.AxisLimits(*limits)
        self._timeout = timeout
        self._lock = lock
        super().__init__()

    def move_by(self, delta: float) -> None:
        """Move axis by given amount."""
        self.move_to(self.position + delta)

    def move_to(self, pos: float) -> None:
        """Move axis to specified position."""
        with self._lock:
            self._amc.move.setControlTargetPosition(self._index, pos)
            self._amc.control.setControlMove(self._index, True)

    @property
    def position(self) -> float:
        """Current axis position."""
        with self._lock:
            x = self._amc.move.getPosition(self._index)
        #print(x)
        return x

    @property
    def limits(self) -> microscope.AxisLimits:
        """Upper and lower limits values for position."""
        return self._limits

    def wait(self):
        timeout = self._timeout + time.time()
        while self._amc.control.getStatusMovingAllAxes()[self._index] and time.time() < timeout:
            time.sleep(0.1)

class AMC300Adapter(microscope.abc.Stage):

    def __init__(self, ip, port, x_limits, y_limits, z_limits, xyz=(0, 1, 2), timeout:float=30, **kwargs):
        super().__init__(**kwargs)
        self.ip = ip
        self.port = port
        self._amc = AMCDevice(ip, port)
        self._lock = threading.RLock()
        self._axes = {
            "x": AMC300Axis(self._amc, xyz[0], x_limits, timeout, self._lock),
            "y": AMC300Axis(self._amc, xyz[1], y_limits, timeout, self._lock),
            "z": AMC300Axis(self._amc, xyz[2], z_limits, timeout, self._lock)
        }
        
        self.connect()
        
        
    def connect(self):
        with self._lock:
            self._amc.connect()

    def close(self):
        with self._lock:
            self._amc.close()


    @property
    def axes(self):
        # Mapping from string axis names to their corresponding hardware indices
        #return {name: self._amc.move.getAxis(index) for name, index in self._axis_map.items()}
        return self._axes

    def may_move_on_enable(self) -> bool:
        """Whether calling :func:`enable` is likely to make the stage move.

        Most stages need to be driven to their limits at startup to
        find a repeatable zero position and sometimes to find their
        limits as well.  This is typically called "homing".

        Stages that need to "home" differ on how often they need it
        but they only do it during :func:`enable`.  They may need to
        move each time `enable` is called, the first time after the
        `Stage` object has been created, or even only the first time
        since the device was powered up.

        Note the "*may*" on "may_move_on_enable".  This is because it
        can be difficult to know for certain if `enable` will cause
        the stage to home.  Still, knowing that the stage *may* move
        is essential for safety.  An unexpected movement of the stage,
        particularly large movements such as moving to the stage
        limits, can destroy a sample on the stage --- or even worse,
        it can damage an objective or the stage itself.  When in
        doubt, implementations should return `True`.

        """
        return False

    @property
    def position(self) -> typing.Mapping[str, float]:
        """Map of axis name to their current position.

        .. code-block:: python

            for name, position in stage.position.items():
                print(f'{name} axis is at position {position}')

        The units of the position is the same as the ones being
        currently used for the absolute move (:func:`move_to`)
        operations.
        """
        return {name: axis.position for name, axis in self._axes.items()}

    def limits(self) -> typing.Mapping[str, microscope.AxisLimits]:
        """Map of axis name to its upper and lower limits.

        .. code-block:: python

            for name, limits in stage.limits.items():
                print(f'{name} axis lower limit is {limits.lower}')
                print(f'{name} axis upper limit is {limits.upper}')

        These are the limits currently imposed by the device or
        underlying software and may change over the time of the
        `StageDevice` object.

        The units of the limits is the same as the ones being
        currently used for the move operations.

        """
        return {name: axis.limits for name, axis in self.axes.items()}

    def move_by(self, delta: typing.Mapping[str, float]) -> None:
        """Move axes by the corresponding amounts.

        Args:
            delta: map of axis name to the amount to be moved.

        .. code-block:: python

            # Move 'x' axis by 10.2 units and the y axis by -5 units:
            stage.move_by({'x': 10.2, 'y': -5})

            # The above is equivalent, but possibly faster than:
            stage.axes['x'].move_by(10.2)
            stage.axes['y'].move_by(-5)

        The axes will not move beyond :func:`limits`.  If `delta`
        would move an axis beyond it limit, no exception is raised.
        Instead, the stage will move until the axis limit.

        """
        # TODO: implement a software fallback that moves the
        # individual axis, for stages that don't have provide
        # simultaneous move of multiple axes.
        for axis_name, axis_delta in delta.items():
            axis = self.axes[axis_name]
            # Set the controller to be in open loop mode
            self._amc.control.getControlMove(self, axis) == False
            axis.move_by(axis_delta)
            axis.wait()
        

    def move_to(self, position: typing.Mapping[str, float]) -> None:
        """Move axes to the corresponding positions.

        Args:
            position: map of axis name to the positions to move to.

        .. code-block:: python

            # Move 'x' axis to position 8 and the y axis to position -5.3
            stage.move_to({'x': 8, 'y': -5.3})

            # The above is equivalent to
            stage.axes['x'].move_to(8)
            stage.axes['y'].move_to(-5.3)

        The axes will not move beyond :func:`limits`.  If `positions`
        is beyond the limits, no exception is raised.  Instead, the
        stage will move until the axes limit.

        """
        for axis_name, axis_position in position.items():
            axis = self.axes[axis_name]
            axis.move_to(axis_position)
            axis.wait()


    # def move_to(self, axis, position_um):
        
    #     position_nm = position_um * 1000

    #     if axis in [0, 1]:
    #         if not (100 * 1000 <= position_nm <= 5900 * 1000):
    #             print("Position out of permitted range. Command not sent")
    #             return
    #     elif axis == 2:
    #         if not (1000 * 1000 <= position_nm <= 5000 * 1000):
    #             print("Position out of permitted range. Command not sent")
    #             return
    #     else:
    #         print("Invalid axis name. Command not sent")
    #         return
        
    #     # NOTE TO SELF: If setControlTargetPosition and setControlMove require numerical,
    #     #               I might need to change it back to int 0, 1, 2 
    #     self._amc.move.setControlTargetPosition(axis, position_nm)
    #     self._amc.control.setControlMove(axis, True)

    #     # Check if the axis starts moving within the timeout period
    #     if not self.get_moving_status(axis):
    #         print(f"Timeout: Axis {axis} did not start moving within {self.timeout} seconds")
    #         self._amc.control.setControlMove(axis, False) # stop the axis
    #         return

    #     # Get the current time
    #     start_time = time.time()
        
    #     # Wait for the axis to reach the target position
    #     while not self._amc.status.getStatusTargetRange(axis):
    #         # Check for timeout
    #         if time.time() - start_time > self.timeout:
    #             print(f"Timeout: axis {axis} did not reach the target position within {self.timeout} seconds.")
    #             self._amc.control.setControlMove(axis, False)
    #             return
            
    #         # Read out position in nm
    #         current_position = self._amc.move.getPosition(axis)
    #         print(current_position)
    #         time.sleep(0.1)

    #     # Stop approach
    #     self._amc.control.setControlMove(axis, False)
    #     print(f"Axis {axis} reached the target position successfully")

    # # Implementing this function to be compatible with python-microscope structure
    # def get_position(self, axis):
    #     # Retrieve the current position of the specified axis
    #     current_position_nm = self._amc.move.getPosition(axis)
    #     current_position_um = current_position_nm / 1000.0
    #     return current_position_um

    # def get_moving_status(self, axis):
    #     start_time = time.time()

    #     while True:
    #         # Call getStatusMoving method to retrieve the moving status of all axes
    #         moving_status = self._amc.control.getStatusMovingAllAxes()

    #         # Print status for debugging
    #         print("Moving Status:", moving_status)

    #         # Check if any axis is moving
    #         if any(moving_status):
    #             print("At least one axis is moving")
    #             return True
            
    #         # Check for timeout
    #         if time.time() - start_time > self.timeout:
    #             print("Timeout: No axis is moving within", self.timeout, "seconds")
    #             return False
            
    #         # Add short delay before checking again
    #         time.sleep(0.1)

    # def rough_jog(self, axis, direction):
    #     if axis == 0 or axis == 1:
    #         distance = 100  #TODO: ask Tom/Benji about sensible values
    #         if direction == "positive":
    #             self.move_to(axis, self._amc.move.getPosition(axis) + distance)
    #         elif direction == "negative":
    #             self.move_to(axis, self._amc.move.getPosition(axis) - distance)
    #         else:
    #             print("Invalid direction. Please specify 'positive' or 'negative' for axis 0 and 1")
    #     elif axis == 2:
    #         distance = 50 #TODO: ask Tom/Benji about sensible values
    #         if direction == "positive":
    #             self.move_to(axis, self._amc.move.getPosition(axis) + distance)
    #         elif direction == "negative":
    #             self.move_to(axis, self._amc.move.getPosition(axis) - distance)
    #         else:
    #             print("Invalid axis. Please specify axis 0, 1 or 2")

    # def fine_jog(self, axis, direction):
    #     if axis == 0 or axis == 1:
    #         distance = 10 #TODO: ask Tom/Benji about sensible values
    #         if direction == "positive":
    #             self.move_to(axis, self._amc.move.getPosition(axis) + distance)
    #         elif direction == "negative":
    #             self.move_to(axis, self._amc.move.getPosition(axis) - distance)
    #         else:
    #             print("Invalid direction. Please specify a 'positive' or 'negative' direction")
    #     elif axis == 2:
    #         distance = 5 #TODO: ask Tom/Benji about sensible values
    #         if direction == "positive":
    #             self.move_to(axis, self._amc.move.getPosition(axis) + distance)
    #         elif direction == "negative":
    #             self.move_to(axis, self._amc.move.getPosition(axis) - distance)
    #         else:
    #             print("invalid axis. Please specify axis 0, 1 or 2")

    def set_frequency(self, axis, frequency):
        if not (3 <= frequency <= 5000):
            print("Frequency out of permitted range. Command not sent")
            return 
        if self._amc.control.setControlFrequency(axis, frequency):
            print(f"Frequency set successfully for axis {axis}")
        else:
            print(f"Failed to set frequency fpr axis {axis}")

    def set_amplitude(self, axis, amplitude):
        if not (0 <= amplitude <= 60):
            print("Amplitude out of permitted range. Command not sent")
            return 
        if self._amc.control.setControlAmplitude(axis, amplitude):
            print(f"Amplitude set successfully for axis {axis}")
        else:
            print(f"Failed to set amplitude for axis {axis}")

    def get_frequency(self, axis):
        return self._amc.control.getControlFrequency(axis)

    def get_pos_and_freq(self):    #, axis, position, frequency):
        return self._amc.control.getPositionsAndVoltages()

    def get_amplitude(self, axis):
        return self._amc.control.getControlAmplitude(axis)

    def get_piezo_amplitude(self, axis):
        return self._amc.control.getCurrentOutputVoltage(axis)

    def home(self):
        self.move_to(0, 3984.1)
        self.move_to(1, 3075.7)
        self.move_to(2, 4539.6)
        print("Axes homed successfully.")

    def _do_shutdown(self) -> None:
        self.close()


if __name__ == "__main__":
    ip = "192.168.0.2"
    port = 9090
    controller = AMC300Adapter(ip, port)
    controller.connect()