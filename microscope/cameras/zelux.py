import numpy as np
import cv2
import microscope
import microscope.abc
from thorlabs_tsi_sdk.tl_camera import TLCameraSDK, OPERATION_MODE, TRIGGER_POLARITY  #, TLCamera

NUM_FRAMES = 10

class ZeluxCamera(microscope.abc.Camera):
    def __init__(self):
        self._fetch_thread = None
        self.zelux = TLCameraSDK()
        #self.zeltest = TLCamera()
        available_cameras = self.zelux.discover_available_cameras()
        if len(available_cameras) < 1:
            raise RuntimeError("No cameras detected")

        self.camera = self.zelux.open_camera(available_cameras[0])
        print(f"Camera serial number: {self.camera.serial_number}")
        print(f"hdw trigger rising edge 0, falling edge 1: {self.camera.trigger_polarity}")
        #print(f"the hardware trigger is supported: {self.zeltest.get_is_operation_mode_supported}")
        self.camera.exposure_time_us = 11000
        self.camera.frames_per_triffer_zero_for_unlimited = 0
        self.camera.image_poll_timeout_ms = 30000
        self.old_roi = self.camera.roi 

    def _do_shutdown(self):
        if self.camera.is_armed:
            self.camera.disarm()
        self.camera.dispose()
        self.zelux.dispose()

    def _do_trigger(self):
        self.camera.issue_software_trigger()
        #self.camera.issue_hardware_trigger()

    def _fetch_data(self):
        frame = self.camera.get_pending_frame_or_null()
        if frame:
            return np.copy(frame.image_buffer), frame.frame_count
        return None

    def _get_binning(self):
        return self.camera.biny_range

    def _set_binning(self, binx, biny): 
        return self.camera.biny,  self.camera.binx

    def _get_roi(self):
        return self.camera.roi

    def _set_roi(self, roi):
        self.camera.roi = roi

    def _get_sensor_shape(self):
        # Return sensor shape width and hight
        return (self.camera.sensor_width_pixels, self.camera.sensor_height_pixels)

    def abort(self):
        # Abort any ongoing acquisition
        self.camera.disarm()

    def set_exposure_time(self, exposure_time):
        # Set the camera exposure time in seconds
        self.camera.exposure_time_us = 50000     #int(exposure_time * 1e6)

    def set_trigger(self, trigger_type, trigger_mode):
        # Set the camera's trigger type and mode
        if trigger_type == 'hardware':
            self.camera.operation_mode = OPERATION_MODE.HARDWARE_TRIGGERED
            self.camera.trigger_polarity = TRIGGER_POLARITY.ACTIVE_HIGH
        else:
            self.camera.operation_mode = OPERATION_MODE.SOFTWARE_TRIGGERED

    def trigger_mode(self):
        return self.camera.operation_mode

    def trigger_type(self):
        if self.camera.operation_mode == OPERATION_MODE.HARDWARE_TRIGGERED:
            return 'hardware'
        elif self.camera.operation_mode == OPERATION_MODE.SOFTWARE_TRIGGERED:
            return 'software'

    def start_acquisition(self):
        print("Starting acquisition")
        self.camera.arm(2)
        print("Camera is armed: ", self.camera.is_armed)

    def stop_acquisition(self):
        self.camera.disarm()

    def _fetch_data_continuously(self):
        frame_count = 0
        while self._fetch_thread is not None:
            # Fetch the frame
            frame_data, count = self._fetch_data()

            if frame_data is not None:
                frame_count += 1

                # Display the frame live
                cv2.imshow("Live Camera Feed", frame_data)
                
                # Save frames
                file_name = f"frame_{frame_count}.png"
                cv2.imwrite(file_name, frame_data)
                print(f"Frame #{count} displayed and saved as {file_name}")

                # Press q to exit live display
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break 

            else:
                print("No frame received or timeout reached")

        cv2.destroyAllWindows()

    def grab_frame(self):
        if not self.camera.is_armed:
            print("Camera is not armed. Arming now...")
            self.camera.arm(2)
        print("camera is armed: ", self.camera.is_armed)
        
        for _ in range(5):
            frame = self.camera.get_pending_frame_or_null()
            if frame is not None:
                print(f"Frame #{frame.frame_count} received")
                # Make a deep copy of the image buffer
                return np.copy(frame.image_buffer)
            else:
                print("No frames received, retrying...")
            print("Timeout reached during polling")
            return None

    def acquire_images(self, num_frames=NUM_FRAMES):
        # Acquire multiple frames from the camera
        self.start_acquisition()
        for i in range(num_frames):
            image = self.grab_frame()
            if image is None:
                print(f"No frames received for {i+1}")
            else:
                print(f"Frame {i+1} acquired")
        self.stop_acquisition()
    
    def close(self):
        if self.camera.is_armed:
            self.camera.disarm()
        # Close the camera and SDK when done
        self.camera.dispose()
        self.zelux.dispose()

camera = ZeluxCamera()
#try:
camera.acquire_images(NUM_FRAMES)
#camera.set_trigger('hardware', 'rising_edge')
camera.set_trigger('software', None)
#finally:
#    camera.dispose()