#!/usr/bin/python3
"""
Red Pitaya Interactive Analog Output Setting Example
=====================================================

This example demonstrates interactive control of Red Pitaya's slow analog outputs
(AO0-AO3) with user input. Users can dynamically set output voltages through a
command-line interface with real-time feedback and validation.

Features:
- Interactive voltage setting for all 4 analog outputs
- Real-time input validation and error handling
- Individual or batch voltage updates
- Voltage range checking and clamping (0-1.8V)
- Continuous operation until user exits
- User-friendly menu interface

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)
- Optional: Multimeter or oscilloscope to verify output voltages
- Optional: External circuits connected to AO0-AO3 pins

Software Requirements:
- Red Pitaya Python API (rp module)

Usage:
    python ana_3_interactive_set_analog_outs.py
    
    Enter voltages when prompted:
    - Single value: Sets all 4 outputs to the same voltage
    - Four values (space-separated): Sets each output individually
    
    Examples:
        1.5             -> Sets all outputs to 1.5V
        0.5 1.0 1.5 1.8 -> Sets AO0=0.5V, AO1=1.0V, AO2=1.5V, AO3=1.8V
    
    Press Ctrl+C to exit.

Important Note:
    Slow analog outputs can generate voltages from 0V to 1.8V only.
    Values outside this range will be automatically clamped.
    Output impedance: ~100Ω (100Ω series resistor with 8.2nF parallel capacitor acting as a low-pass filter).
    Not 50Ω — do not use with 50Ω transmission lines or RF loads.
    Maximum current: a few mA (keep load impedance above ~500Ω to stay below ~3mA)

Author: Red Pitaya
Date: May 2026
"""

import time
import rp


# ==============================================================================
# CONFIGURATION - Set your analog output parameters here
# ==============================================================================

# Analog output parameters
num_analog_outputs = 4          # Number of analog outputs (AO0-AO3)
analog_out = [rp.RP_AOUT0, rp.RP_AOUT1, rp.RP_AOUT2, rp.RP_AOUT3]

# Voltage limits
min_voltage = 0.0               # Minimum output voltage
max_voltage = 1.8               # Maximum output voltage
default_voltage = 1.0           # Default voltage for invalid inputs

# Timing
update_delay = 0.2              # Delay between updates in seconds

print("=" * 70)
print("Red Pitaya Interactive Analog Output Configuration")
print("=" * 70)
print(f"Analog outputs:      AO0 through AO{num_analog_outputs-1}")
print(f"Voltage range:       {min_voltage}V to {max_voltage}V")
print(f"Default voltage:     {default_voltage}V (for invalid/out-of-range values)")
print("Output impedance:    ~100Ω (100Ω series + 8.2nF shunt low-pass filter)")
print("Max current:         a few mA — keep load > ~500Ω")
print()
print("Input formats:")
print("  Single value:      1.5          (sets all outputs to 1.5V)")
print("  Four values:       0.5 1.0 1.5 1.8  (sets each output individually)")
print()
print("Press Ctrl+C to exit")
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
# HELPER FUNCTIONS - Input validation and voltage setting
# ==============================================================================

def parse_and_validate_voltages(input_str):
    """
    Parse user input and validate voltage values.
    
    Args:
        input_str: User input string containing one or four voltage values
        
    Returns:
        tuple: (success, voltage_list) where success is bool and voltage_list contains 4 values
    """
    try:
        # Split input and convert to floats
        values = input_str.strip().split()

        if len(values) == 0:
            print("ERROR: No values entered")
            return False, None

        # Convert to floats
        parsed_voltages = [float(v) for v in values]

        # Handle single value (apply to all outputs)
        if len(parsed_voltages) == 1:
            parsed_voltages = parsed_voltages * num_analog_outputs
            print(f"Setting all {num_analog_outputs} outputs to {parsed_voltages[0]:.3f}V")

        # Handle four values (one per output)
        elif len(parsed_voltages) == num_analog_outputs:
            print(f"Setting individual voltages for {num_analog_outputs} outputs")

        # Invalid number of values
        else:
            print(f"ERROR: Expected 1 or {num_analog_outputs} values, got {len(parsed_voltages)}")
            print(f"       Using default voltage {default_voltage}V for all outputs")
            parsed_voltages = [default_voltage] * num_analog_outputs

        # Validate and clamp voltages to valid range
        clamped_voltages = []
        for idx, v in enumerate(parsed_voltages):
            if not min_voltage <= v <= max_voltage:
                print(f"WARNING: AO[{idx}] voltage {v:.3f}V is out of range ({min_voltage}-{max_voltage}V)")
                v = max(min_voltage, min(max_voltage, v))
                print(f"         Clamped to {v:.3f}V")
            clamped_voltages.append(v)

        return True, clamped_voltages

    except ValueError as e:
        print("ERROR: Invalid input - please enter numeric values only")
        return False, None


def set_output_voltages(output_voltages):
    """
    Set the output voltages on all analog outputs.
    
    Args:
        output_voltages: List of 4 voltage values to set
    """
    print("-" * 70)
    for i in range(num_analog_outputs):
        # Set the output voltage using generic analog pin function
        rp.rp_ApinSetValue(analog_out[i], output_voltages[i])
        print(f"Set voltage on AO[{i}] to {output_voltages[i]:.3f} V")
    print("-" * 70)


# ==============================================================================
# INTERACTIVE CONTROL LOOP - Get user input and set voltages
# ==============================================================================

print("\nStarting interactive analog output control...")
print("Enter voltage values when prompted\n")

# Choose one of two methods below (comment out the other)

# METHOD 1: Using generic analog pin function (rp_ApinSetValue)
try:
    while True:
        # Get user input
        print()
        user_input = input("Enter voltage(s) for AO0-AO3 [single or 4 space-separated values]: ")

        # Parse and validate input
        success, validated_voltages = parse_and_validate_voltages(user_input)

        if success and validated_voltages:
            # Set the output voltages
            set_output_voltages(validated_voltages)
            print("✓ Voltages set successfully")
        else:
            print("✗ Failed to set voltages - please try again")

        # Small delay between updates
        time.sleep(update_delay)

except KeyboardInterrupt:
    print("\n\nKeyboard interrupt detected (Ctrl+C)")


# METHOD 2: Using dedicated analog output function (rp_AOpinSetValue)
# Uncomment this block and comment the METHOD 1 block above to use
"""
try:
    while True:
        # Get user input
        print()
        user_input = input("Enter voltage(s) for AO0-AO3 [single or 4 space-separated values]: ")

        # Parse and validate input
        success, validated_voltages = parse_and_validate_voltages(user_input)

        if success and validated_voltages:
            # Set the output voltages using dedicated AO function
            print("-" * 70)
            for i in range(num_analog_outputs):
                rp.rp_AOpinSetValue(i, validated_voltages[i])
                print(f"Set voltage on AO[{i}] to {validated_voltages[i]:.3f} V")
            print("-" * 70)
            print("✓ Voltages set successfully")
        else:
            print("✗ Failed to set voltages - please try again")

        # Small delay between updates
        time.sleep(update_delay)

except KeyboardInterrupt:
    print("\n\nKeyboard interrupt detected (Ctrl+C)")
"""


# ==============================================================================
# CLEANUP - Release resources and reset outputs
# ==============================================================================

print("\nCleaning up...")

# Optional: Reset outputs to 0V before exiting
# Uncomment the next two lines to reset outputs on exit
# print("Resetting all outputs to 0V...")
# rp.rp_ApinReset()

# Release Red Pitaya resources
rp.rp_Release()

print("Resources released - program complete")
print("\nNote: Analog outputs will maintain their last set voltages")
print("      Restart the board or use rp_ApinReset() to set outputs to 0V")
