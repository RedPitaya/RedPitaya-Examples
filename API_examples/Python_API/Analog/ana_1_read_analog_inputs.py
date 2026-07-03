#!/usr/bin/python3
"""
Red Pitaya Analog Input Reading Example
========================================

This example demonstrates reading analog voltages from Red Pitaya's slow analog
inputs (AI0-AI3). These inputs can measure voltages in the range of 0-3.5V and
are useful for monitoring sensors, control signals, or other analog sources.

Features:
- Reads all 4 slow analog inputs (AI0-AI3)
- Displays voltage readings in volts
- Two implementation methods: generic analog pin function and dedicated AI function
- Single-shot measurement (one reading per input)

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)
- Optional: Analog voltage sources (0-3.5V) connected to AI0-AI3 pins

Software Requirements:
- Red Pitaya Python API (rp module)

Usage:
    python ana_1_read_analog_inputs.py
    
    Connect analog voltage sources to AI pins (E2 connector).
    The program will read and display the voltage on each input.

Important Note:
    Slow analog inputs accept voltages from 0V to 3.5V only.
    Do not exceed 3.5V to avoid damage to the board.
    Negative voltages are not supported.

Pinout Reference:
    AI0-AI3: Extension connector E2
    See Red Pitaya documentation for exact pin locations.

Author: Red Pitaya
Date: May 2026
"""

import rp


# ==============================================================================
# CONFIGURATION - Set your analog input parameters here
# ==============================================================================

# Analog input parameters
num_analog_inputs = 4           # Number of analog inputs to read (0-3 = AI0-AI3)
analog_in = [rp.RP_AIN0, rp.RP_AIN1, rp.RP_AIN2, rp.RP_AIN3]

print("=" * 70)
print("Red Pitaya Analog Input Reading Configuration")
print("=" * 70)
print(f"Analog inputs:       AI0 through AI{num_analog_inputs-1}")
print("Voltage range:       0 to 3.5V")
print("Input impedance:     100 kΩ")
print()
print("WARNING: Do not exceed 3.5V on any analog input!")
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

# Reset analog pins to default state
rp.rp_ApinReset()
print("Analog pins reset to default state")


# ==============================================================================
# ANALOG INPUT READING - Read voltage from analog inputs
# ==============================================================================

print("\nReading analog inputs...")
print("Choose one of two methods below (comment out the other)\n")

# METHOD 1: Reading all analog pins using generic analog pin function
# This method can read any analog pin (AI or AO) using pin identifiers
print("Method 1: Using generic analog pin function (rp_ApinGetValue)")
print("-" * 70)

for i in range(num_analog_inputs):
    # rp_ApinGetValue returns an array: [status, voltage_in_V, voltage_RAW]
    # Index [1] contains the voltage in volts
    value = rp.rp_ApinGetValue(analog_in[i])[1]
    print(f"Measured voltage on AI[{i}] = {value:.6f} V")

print()


# METHOD 2: Reading analog inputs using dedicated AI function
# This method is specific to analog inputs and uses index numbers (0-3)
# Uncomment this block and comment the METHOD 1 block above to use
print("Method 2: Using dedicated analog input function (rp_AIpinGetValue)")
print("-" * 70)

for i in range(num_analog_inputs):
    # rp_AIpinGetValue returns an array: [status, voltage_in_V, voltage_RAW]
    # Index [1] contains the voltage in volts
    # This function takes an index (0-3) instead of a pin identifier
    value = rp.rp_AIpinGetValue(i)[1]
    print(f"Measured voltage on AI[{i}] = {value:.6f} V")

print()


# ==============================================================================
# CLEANUP - Release resources
# ==============================================================================

print("\nCleaning up...")

# Release Red Pitaya resources
rp.rp_Release()

print("Resources released - program complete")
print("\nNote: Analog input values are now displayed above")
    