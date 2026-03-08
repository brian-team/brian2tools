import importlib.util
from brian2 import all_devices

# The exact path based on your 'dir' result
file_path = r"C:\Users\ANISHA\OneDrive\Desktop\brian2tools\brian2tools\baseexport\furyexport\device.py"

# Load the module
spec = importlib.util.spec_from_file_location("fury_module", file_path)
device_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(device_module)

# Register the device
all_devices['fury'] = device_module.fury_device

print("--- Device Registration Check ---")
if 'fury' in all_devices:
    print("SUCCESS: 'fury' device is registered!")
else:
    print("FAILURE: 'fury' not found.")