from microscope.device_server import device
from microscope.cameras.pvcam import PVCamera
from microscope.filterwheels.thorlabs import ThorlabsFilterWheel
from microscope.stages.AMC300 import AMC300Adapter


DEVICES = [
    device(PVCamera, "localhost", 1, uid= "A19J203005"),
    device(PVCamera, "localhost", 2, uid= "A19F203039"),
    #device(ThorlabsFilterWheel, "localhost", 65130, conf={"com": "COM5", "baud": 115200, "timeout": 1}),
    device(ThorlabsFilterWheel, "localhost", 65131, conf={"com": "COM10", "baud": 115200, "timeout": 1}),
]
