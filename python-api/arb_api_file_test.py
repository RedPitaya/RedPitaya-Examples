#!/usr/bin/python3

from rp_arb import *
import numpy as np

# Initialize ARB system
rp_ARBInit()

# Load ARB files
rp_ARBLoadFiles()

# Get file count
count = rp_ARBGetCount()[1]

if count > 0:
    # Create buffer for signal data
    signal_data = np.zeros(1024 * 16, dtype=np.float32)

    # Get first signal data
    rp_ARBGetSignalNP(0, signal_data)

    # Print signal data
    with np.printoptions(threshold=np.inf, suppress=True, precision=6):
        print(signal_data)
else:
    print("No files found.")