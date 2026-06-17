#!/usr/bin/env python3

"""
AWG Waveform CSV Generator for Red Pitaya ARB Manager
======================================================

This script generates custom arbitrary waveform files in CSV and WAV formats
that can be uploaded to Red Pitaya's Arbitrary Waveform Manager (ARB Manager)
application.

Features:
- Creates multiple custom waveforms with different mathematical functions
- Exports waveforms as CSV files for ARB Manager
- Generates signed 16-bit WAV files for audio-based applications
- Visual preview of waveforms using matplotlib

Output Files:
-------------
CSV Format (for ARB Manager):
  - arb_waveform1_sdr.csv: Half-sine wave (0 to π)
  - arb_waveform2_sdr.csv: Composite sine (1/2·sin(t) + 1/4·sin(4t))
  - arb_waveform3_sdr.csv: Amplitude modulated sine (sin(t/2)·sin(10t))

WAV Format (16-bit signed):
  - arb_waveform_signed16.wav: Single period sine wave

Usage:
    python AWG_waveform_csv_gen.py

Requirements:
- numpy
- pandas
- matplotlib
- scipy

Note:
    CSV waveforms are scaled by 0.2 for amplitude control.
    WAV format uses 16-bit signed integers (range: -32768 to 32767).
    Red Pitaya FPGA divides the WAV signal by 4 internally.
"""

import numpy as np
import pandas as pd
import math
from matplotlib import pyplot as plt
from scipy.io import wavfile


# ==============================================================================
# CSV WAVEFORM GENERATION (for ARB Manager)
# ==============================================================================

print("=" * 70)
print("Red Pitaya - AWG Waveform CSV Generator")
print("=" * 70)

# Configuration
N = 16384                               # Number of samples (16K points)
t = np.linspace(0, 1, N) * 2 * np.pi    # Time vector from 0 to 2π

print("\nCSV Waveform Configuration:")
print("  Number of samples:     {N}")
print("  Time range:            0 to 2π")
print("  Amplitude scaling:     0.2 (20%)")

# Define custom waveforms
print("\nGenerating waveforms...")

# Waveform 1: Half-sine wave (0 to π only)
x = np.zeros(N)
x[0:int(N/2+1)] = np.sin(t[0:int(N/2+1)])
print("  Waveform 1:            Half-sine (0 to π)")

# Waveform 2: Composite sine wave
y = 1/2 * np.sin(t) + 1/4 * np.sin(4*t)
print("  Waveform 2:            Composite (1/2·sin(t) + 1/4·sin(4t))")

# Waveform 3: Amplitude modulated sine
z = np.sin(1/2 * t) * np.sin(10*t)
print("  Waveform 3:            AM sine (sin(t/2)·sin(10t))")

# Waveform 4: Additional composite (not exported, for reference)
a = 3/4 * np.sin(t) + 1/4 * np.sin(3*t)

# Preview waveforms
print("\nDisplaying waveform preview...")
plt.plot(t, x, label='Half-sine')
plt.plot(t, z, label='AM sine')
plt.plot(t, y, label='Composite')
plt.title('Custom Waveforms Preview')
plt.xlabel('Time (radians)')
plt.ylabel('Amplitude')
plt.legend()
plt.grid(True)
plt.show()

# Export waveforms to CSV format for ARB Manager
print("\nExporting CSV files for ARB Manager...")
pd.DataFrame(x*0.2).to_csv('arb_waveform1_sdr.csv', index=False, header=False, float_format=np.float64)
print("  Created: arb_waveform1_sdr.csv")

pd.DataFrame(y*0.2).to_csv('arb_waveform2_sdr.csv', index=False, header=False, float_format=np.float64)
print("  Created: arb_waveform2_sdr.csv")

pd.DataFrame(z*0.2).to_csv('arb_waveform3_sdr.csv', index=False, header=False, float_format=np.float64)
print("  Created: arb_waveform3_sdr.csv")


# ==============================================================================
# WAV WAVEFORM GENERATION (16-bit signed format)
# ==============================================================================

print("\n" + "=" * 70)
print("Generating WAV Format Waveform (16-bit signed)")
print("=" * 70)

# Configuration for 16-bit signed WAV
N = 1024                                    # Number of samples
num_periods = 1                             # Number of sine periods
num_bits = 16                               # Bit depth
max_val = 2**(num_bits-1) - 1               # Maximum value:  32767
min_val = -2**(num_bits-1)                  # Minimum value: -32768

print("\nWAV Waveform Configuration:")
print(f"  Number of samples:     {N}")
print(f"  Number of periods:     {num_periods}")
print(f"  Bit depth:             {num_bits}-bit signed")
print(f"  Value range:           {min_val} to {max_val}")
print("  Note:                  FPGA divides signal by 4")

# Generate sine wave scaled to 16-bit range
t = np.linspace(0, 1, N*num_periods) * 2 * np.pi
y = np.sin(num_periods*t) * max_val

# Convert to signed 16-bit integers
sample_rate = 44100                         # Standard audio sample rate (doesn't affect Red Pitaya)
y_signed16 = np.int16(y)

# Preview waveform
print("\nDisplaying WAV waveform preview...")
plt.figure()
plt.plot(y_signed16)
plt.title('16-bit Signed Waveform')
plt.xlabel('Sample')
plt.ylabel('Amplitude (signed 16-bit)')
plt.grid(True)
plt.show()

# Export to WAV file
print("\nExporting WAV file...")
wavfile.write('arb_waveform_signed16.wav', sample_rate, y_signed16)
print("  Created: arb_waveform_signed16.wav")

print("\n" + "=" * 70)
print("Waveform Generation Complete")
print("=" * 70)
print("\nGenerated files can be uploaded to Red Pitaya ARB Manager:")
print("  - CSV files: Use with standard ARB Manager")
print("  - WAV file:  Use with audio-compatible generators")
print("\nUpload these files through the Red Pitaya web interface.")
print("=" * 70)
