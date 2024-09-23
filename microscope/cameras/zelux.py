import numpy as np
from thorlabs_tsi_sdk.tl_camera import TLCameraSDK, OPERATION_MODE

import microscope
import microscope.abc

NUM_FRAMES = 10

class ZeluxCamera(microscope.abc.Camera):
    def __init__(self):
        self.zelux = TLCameraSDK()
        available_cameras = self.zelux.discover_available_cameras()
        if len(available_cameras) < 1:
            raise RuntimeError("No cameras detected")

        self.camera = self.zelux.open_camera(available_cameras[0])
        self.camera.exposure_time_us = 11000
        self.camera.frames_per_triffer_zero_for_unlimited = 0
        self.camera.image_poll_timeout_ms = 1000
        self.old_roi = self.camera.roi 

    def _do_shutdown(self):
        self.camera.disarm()
        self.camera.close()
        self.zelux.dispose()

    def _do_trigger(self):
        self.camera.issue_software_trigger()

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
        self.camera.exposure_time_us = int(exposure_time * 1e6)

    def set_trigger(self, trigger_type, trigger_mode):
        # Set the camera's trigger type and mode
        self.camera.operation_mode = OPERATION_MODE.SOFTWARE_TRIGGERED

    def trigger_mode(self):
        return OPERATION_MODE.SOFTWARE_TRIGGERED

    def trigger_type(self):
        return 'software'

    def start_acquisition(self):
        self.camera.arm(2)

    def stop_acquisition(self):
        self.camera.disarm()

    def grab_frame(self):
        # Grab a frame from the camera
        frame = self.camera.get_pending_frame_or_null()
        if frame is not None:
            print(f"Frame #{frame.frame_count} received")
            # Make a deep copy of the image buffer
            return np.copy(frame.image_buffer)
        else:
            print("Timeout reached during polling")
            return None

    def acquire_images(self, num_frames=NUM_FRAMES):
        # Acquire multiple frames from the camera
        self.start_acquisition()
        for i in range(num_frames):
            image = self.grab_frame()
            if image is None:
                print("No more frames received, exiting")
                break
        self.stop_acquisition()
    
    def close(self):
        # Close the camera and SDK when done
        self.camera.close()
        self.zelux.dispose()

camera = ZeluxCamera()
try:
    camera.acquire_images(NUM_FRAMES)
finally:
    camera.close()