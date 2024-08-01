from microscope.device_server import device
from microscope.cameras.pvcam import PVCamera
from microscope.filterwheels.thorlabs import ThorlabsFilterWheel
from microscope.stages.AMC300 import AMC300Adapter


DEVICES = [
    
    device(PVCamera, "localhost", 1, uid= "A19J203005"),
    device(PVCamera, "localhost", 2, uid= "A19F203039"),
    #device(ThorlabsFilterWheel, "localhost", 65130, conf={"com": "COM5", "baud": 115200, "timeout": 1}),
    device(ThorlabsFilterWheel, "localhost", 65131, conf={"com": "COM10", "baud": 115200, "timeout": 1}),
    device(AMC300Adapter, "localhost", 3, conf={"ip":"192.168.0.2", "port":9090, "x_limits": (100000, 5900000), "y_limits": (100000, 5900000), "z_limits": (100000, 5000000)}),
]
