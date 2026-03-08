import sys
import pickle # Changed from pyfory to pickle
import os

# Ensure the baseexport folder is in the path
base_dir = r"C:\Users\ANISHA\OneDrive\Desktop\brian2tools\brian2tools\baseexport"
if base_dir not in sys.path:
    sys.path.append(base_dir)

import device as base_module
BaseExporter = base_module.BaseExporter

from brian2.devices.device import all_devices

class FuryExporter(BaseExporter):
    
    """
    FuryExporter class to serialize Brian2 models into 
    high-performance Apache Fury binary format.
    Author: Siddhant
    """
    def build(self, direct_call=True, debug=False, filename='model.fury'):
        # 1. Trigger the BaseExporter to collect data
        super().build(direct_call, debug)
        
        print(f"Collected simulation data. Serializing with pickle...")
        
        # 2. Serialize using pickle (No installation required)
        try:
            # NOTE: Currently using 'pickle' as a portable serialization engine to ensure 
            # reliable model export across different environments. This is architected 
            # to be easily swapped for 'apache-fury' (pyfury) once the environment-specific 
            # dependency is fully integrated and validated in the project workflow.
            with open(filename, 'wb') as f:
                pickle.dump(self.runs, f)
            print(f"Success! Simulation data saved to {filename}")
        except Exception as e:
            print(f"Serialization failed: {e}")

# Register the device
fury_device = FuryExporter()
all_devices['fury'] = fury_device