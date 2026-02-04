#!/usr/bin/python3
"""
Red Pitaya Analog Output Setting Example
=========================================

This example demonstrates setting output voltages on Red Pitaya's slow analog
outputs (AO0-AO3). These outputs can generate DC voltages in the range of 0-1.8V
and are useful for controlling external circuits, providing reference voltages,
or interfacing with other analog systems.

Features:
- Sets voltage on all 4 slow analog outputs (AO0-AO3)
- Configurable output voltage per channel
- Two implementation methods: generic analog pin function and dedicated AO function
- Persistent voltage output (remains until changed or reset)

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)
- Optional: Multimeter or oscilloscope to verify output voltages
- Optional: External circuits connected to AO0-AO3 pins

Software Requirements:
- Red Pitaya Python API (rp module)

Usage:
    python ana_2_set_analog_outs.py
    
    Modify the out_voltage array to set desired voltages.
    Connect measurement tools or external circuits to AO pins (E2 connector).
    The program will set the voltages and exit (voltages persist).

Important Note:
    Slow analog outputs can generate voltages from 0V to 1.8V only.
    Voltage resolution: approximately 0.0004V (1.8V / 4096)
    Output impedance: 50Ω
    Maximum current: ±10mA per output

Pinout Reference:
    AO0-AO3: Extension connector E2
    See Red Pitaya documentation for exact pin locations.

Author: Red Pitaya
"""

import rp


# ==============================================================================
# CONFIGURATION - Set your analog output parameters here
# ==============================================================================

# Analog output parameters
num_analog_outputs = 4          # Number of analog outputs to configure (0-3 = AO0-AO3)
analog_out = [rp.RP_AOUT0, rp.RP_AOUT1, rp.RP_AOUT2, rp.RP_AOUT3]

# Output voltages for each channel (0.0 to 1.8V)
out_voltage = [1.0, 1.0, 1.0, 1.0]  # Modify these values as needed

print("=" * 70)
print("Red Pitaya Analog Output Setting Configuration")
print("=" * 70)
print(f"Analog outputs:      AO0 through AO{num_analog_outputs-1}")
print(f"Voltage range:       0 to 1.8V")
print(f"Output impedance:    50Ω")
print(f"Max current:         ±10mA per output")
print(f"Resolution:          ~0.0004V (12-bit DAC)")
print()
print("Output voltages to be set:")
for i in range(num_analog_outputs):
    print(f"  AO[{i}] = {out_voltage[i]:.3f} V")
print()
print("WARNING: Do not exceed 1.8V or draw more than ±10mA per output!")
print("=" * 70)


# ==============================================================================
# INITIALIZATION - Initialize Red Pitaya
# ==============================================================================

print("\nInitializing Red Pitaya...")

# Initialize the Red Pitaya interface
rp.rp_Init()
print("Red Pitaya initialized")


# ==============================================================================
# ANALOG PIN CONFIGURATION - Reset analog pins to default state
# ==============================================================================

print("\nConfiguring analog pins...")

# Reset analog pins to default state (0V on all outputs)
rp.rp_ApinReset()
print("Analog pins reset to default state (0V)")


# ==============================================================================
# ANALOG OUTPUT SETTING - Set voltage on analog outputs
# ==============================================================================

print("\nSetting analog output voltages...")
print("Choose one of two methods below (comment out the other)\n")

# METHOD 1: Setting voltages using generic analog pin function
# This method can set any analog pin (AI or AO) using pin identifiers
print("Method 1: Using generic analog pin function (rp_ApinSetValue)")
print("-" * 70)

for i in range(num_analog_outputs):
    # Validate voltage is within acceptable range
    if not 0.0 <= out_voltage[i] <= 1.8:
        print(f"WARNING: AO[{i}] voltage {out_voltage[i]}V is out of range (0-1.8V)")
        out_voltage[i] = max(0.0, min(1.8, out_voltage[i]))  # Clamp to valid range
        print(f"         Clamped to {out_voltage[i]:.3f}V")
    
    # Set the output voltage
    rp.rp_ApinSetValue(analog_out[i], out_voltage[i])
    print(f"Set voltage on AO[{i}] to {out_voltage[i]:.3f} V")

print("\nAll analog outputs configured successfully")
print("Voltages will persist until changed or board is reset")


# METHOD 2: Setting voltages using dedicated AO function
# This method is specific to analog outputs and uses index numbers (0-3)
# Uncomment this block and comment the METHOD 1 block above to use
"""
print("Method 2: Using dedicated analog output function (rp_AOpinSetValue)")
print("-" * 70)

for i in range(num_analog_outputs):
    # Validate voltage is within acceptable range
    if not 0.0 <= out_voltage[i] <= 1.8:
        print(f"WARNING: AO[{i}] voltage {out_voltage[i]}V is out of range (0-1.8V)")
        out_voltage[i] = max(0.0, min(1.8, out_voltage[i]))  # Clamp to valid range
        print(f"         Clamped to {out_voltage[i]:.3f}V")
    
    # Set the output voltage using index (0-3) instead of pin identifier
    rp.rp_AOpinSetValue(i, out_voltage[i])
    print(f"Set voltage on AO[{i}] to {out_voltage[i]:.3f} V")

print("\nAll analog outputs configured successfully")
print("Voltages will persist until changed or board is reset")
"""


# ==============================================================================
# CLEANUP - Release resources
# ==============================================================================

print("\nCleaning up...")

# Release Red Pitaya resources
# Note: Analog output voltages will remain at their set values
rp.rp_Release()

print("Resources released - program complete")
print("\nNote: Analog outputs will maintain their voltages until changed")
print("      Use rp_ApinReset() to set all outputs back to 0V")
