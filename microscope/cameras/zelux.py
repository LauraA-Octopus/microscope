import numpy as np
from thorlabs_tsi_sdk.tl_camera import TLCameraSDK, OPERATION_MODE

NUM_FRAMES = 10

with TLCameraSDK as sdk:
    available_cameras = sdk.discover_available_cameras()
    if len(available_cameras) < 1:
        print("No cameras detected")

    with sdk.open_camera(available_cameras[0]) as camera:
        camera.exposure_time_us = 11000
        # start the camera in continuous mode
        camera.frames_per_triffer_zero_for_unlimited = 0 
        # 1s polling timeout
        camera.image_poll_timeout_ms = 1000
        # store the current ROI
        old_roi = camera.roi

        camera.arm(2)

        # Uncomment if we want the camera software triggered
        # camera.issue_software_trigger()

        for i in range(NUM_FRAMES):
            frame = camera.get_pending_frame_or_null()
            if frame is not None:
                print("frame #{} received!".format(frame.frame_count))

                frame.image_buffer
                #NOTE: the above is a temporary memory buffer
                # that may be overwritten during the next call
                # to get_pending_frame_or_null the following line
                # makes a deep copy of the image data:
                image_buffer_copy = np.copy(frame.image_buffer)
            else:
                print("Timeout reached during polling, program exiting...")
                break
        camera.disarm()
        # Reset the ROI back to the original ROI
        camera.roi = old_roi

print("program completed")  