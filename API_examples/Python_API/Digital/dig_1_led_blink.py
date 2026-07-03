#!/usr/bin/python3
"""
Red Pitaya LED Blink Example
=============================

This example demonstrates basic LED control on Red Pitaya by blinking LED0.
Two different methods are shown for controlling the LED state: direct register
manipulation and using macro functions.

Features:
- LED control via register manipulation
- LED control via convenience macros
- Configurable blink period

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)
- Built-in LED0 (no external connections required)

Software Requirements:
- Red Pitaya Python API (rp module)

Usage:
    python dig_1_led_blink.py

Note:
    Choose one of the two methods (comment out the other).
    Press Ctrl+C to stop the program.

Author: Red Pitaya
"""

import time
import rp


# ==============================================================================
# CONFIGURATION - Set your LED parameters here
# ==============================================================================

# LED blink parameters
blink_period = 1.0              # Period in seconds (time for one complete on/off cycle)

print("=" * 70)
print("Red Pitaya LED Blink Configuration")
print("=" * 70)
print(f"Blink period:        {blink_period} seconds")
print("LED:                 LED0")
print("Press Ctrl+C to stop")
print("=" * 70)


# ==============================================================================
# INITIALIZATION - Initialize Red Pitaya
# ==============================================================================

print("\nInitializing Red Pitaya...")

# Initialize the Red Pitaya interface
rp.rp_Init()
print("Red Pitaya initialized")


# ==============================================================================
# LED CONTROL - Blink LED using selected method
# ==============================================================================

print("\nStarting LED blink...")
print("Choose one of two methods below (comment out the other)\n")


# METHOD 1: Direct register manipulation
# Set LED state by writing to LED register (8 LEDs, bit 0 = LED0)
try:
    print("Method 1: Using direct register control")
    while True:
        time.sleep(blink_period / 2.0)
        rp.rp_LEDSetState(0b00000001)       # Turn on LED0 (bit 0 = 1)
        time.sleep(blink_period / 2.0)
        rp.rp_LEDSetState(0b00000000)       # Turn off LED0 (all bits = 0)
        
except KeyboardInterrupt:
    print("\n\nKeyboard interrupt detected (Ctrl+C)")


# METHOD 2: Using convenience macros
# Use pre-defined macros for LED control (recommended for clarity)
# Uncomment this block and comment the METHOD 1 block above to use
"""
try:
    print("Method 2: Using convenience macros")
    while True:
        time.sleep(blink_period / 2.0)
        rp.rp_DpinSetState(rp.RP_LED0, rp.RP_HIGH)      # Turn on LED0
        time.sleep(blink_period / 2.0)
        rp.rp_DpinSetState(rp.RP_LED0, rp.RP_LOW)       # Turn off LED0
    
except KeyboardInterrupt:
    print("\n\nKeyboard interrupt detected (Ctrl+C)")
"""


# ==============================================================================
# CLEANUP - Release resources
# ==============================================================================

print("Cleaning up...")

# Ensure LED is off before exiting
rp.rp_LEDSetState(0b00000000)

# Release Red Pitaya resources
rp.rp_Release()

print("Resources released - program complete")
print("LED should now be off")
