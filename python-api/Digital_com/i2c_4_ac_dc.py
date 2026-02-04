#!/usr/bin/python3
"""
Red Pitaya AC/DC Mode Control via I2C Example
==============================================

This example demonstrates how to control the AC/DC coupling mode of analog input
channels on Red Pitaya boards equipped with the AC/DC mode expansion module. The
example uses I2C communication via SMBus protocol to control a digital I/O expander
that switches relay circuits for AC/DC coupling.

The AC/DC mode switching allows you to:
- DC Mode: Direct coupling, measures full signal including DC offset
- AC Mode: Capacitive coupling, blocks DC component and measures AC variations

Features:
- I2C communication with GPIO expander (address 0x21)
- SMBus word read/write operations
- AC/DC mode control for channels 1 and 2
- Status readback verification
- Force mode for reliable I2C communication

Hardware Requirements:
- Red Pitaya board with AC/DC mode expansion
- Internal I2C-controlled GPIO expander at address 0x21
- No external connections required (internal hardware)

Technical Details:
- I2C Bus: /dev/i2c-0
- Device Address: 0x21 (GPIO expander)
- Control Register: 0x02
- Protocol: SMBus word (16-bit) operations
- AC Mode Value: 0x00AA (channels 1 & 2)
- DC Mode Value: 0x0055 (channels 1 & 2)

Control Sequence:
1. Write initial value with lower nibble set (0x0055 or 0x00AA)
2. Clear lower nibble (AND with ~0x000F) to latch the value
3. Repeat for each mode change

Software Requirements:
- Red Pitaya hardware library (rp_hw module)
- Red Pitaya board with AC/DC expansion capability

Usage:
    python i2c_4_ac_dc.py
    
    The program will:
    1. Switch channels 1 & 2 to DC mode (3 seconds)
    2. Switch channels 1 & 2 to AC mode
    3. Read back the current AC/DC state

Note:
    This example only works on Red Pitaya boards with AC/DC mode expansion.
    Standard boards without this feature will show I2C communication errors.

Author: Red Pitaya
Date: January 2026
"""

import time
import rp_hw


# ==============================================================================
# CONFIGURATION - Set your I2C and AC/DC control parameters here
# ==============================================================================

# I2C Configuration
i2c_device = "/dev/i2c-0"       # I2C bus device
gpio_expander_address = 0x21    # GPIO expander I2C address
control_register = 0x02         # Control register address
force_mode = True               # Enable force mode for direct access

# AC/DC Mode Control Values
DC_MODE_VALUE = 0x0055          # Value to set DC mode (channels 1 & 2)
AC_MODE_VALUE = 0x00AA          # Value to set AC mode (channels 1 & 2)
LATCH_MASK = ~0x000F            # Mask to clear lower nibble for latching

# Timing Configuration
latch_delay = 1.0               # Delay after writing value (seconds)
dc_mode_duration = 3.0          # How long to stay in DC mode (seconds)

print("=" * 70)
print("Red Pitaya AC/DC Mode Control Configuration")
print("=" * 70)
print(f"I2C Device:          {i2c_device}")
print(f"GPIO Expander Addr:  0x{gpio_expander_address:02X}")
print(f"Control Register:    0x{control_register:02X}")
print(f"DC Mode Value:       0x{DC_MODE_VALUE:04X}")
print(f"AC Mode Value:       0x{AC_MODE_VALUE:04X}")
print(f"Latch Delay:         {latch_delay} seconds")
print(f"DC Mode Duration:    {dc_mode_duration} seconds")
print("=" * 70)


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def set_ac_dc_mode(value, mode_name):
    """
    Set AC/DC mode by writing value and then latching it.
    
    Args:
        value: Mode value to write (DC_MODE_VALUE or AC_MODE_VALUE)
        mode_name: Description of the mode for display
        
    Returns:
        int: 0 on success, -1 on error
    """
    print(f"\n    Setting {mode_name}...")
    
    # Step 1: Write initial value
    res = rp_hw.rp_I2C_SMBUS_WriteWord(control_register, value)
    if res != 0:
        print(f"    ERROR: Failed to write initial value (error code: {res})")
        return -1
    print(f"    Wrote 0x{value:04X} (result: {res})")
    
    time.sleep(latch_delay)
    
    # Step 2: Clear lower nibble to latch the value
    latched_value = value & LATCH_MASK
    res = rp_hw.rp_I2C_SMBUS_WriteWord(control_register, latched_value)
    if res != 0:
        print(f"    ERROR: Failed to latch value (error code: {res})")
        return -1
    print(f"    Latched with 0x{latched_value:04X} (result: {res})")
    
    return 0


# ==============================================================================
# MAIN PROGRAM
# ==============================================================================

def main():
    """Main program to control AC/DC mode on Red Pitaya analog inputs."""
    
    try:
        # ===== STEP 1: Initialize I2C Device =====
        print("\n[1] Initializing I2C device...")
        res = rp_hw.rp_I2C_InitDevice(i2c_device, gpio_expander_address)
        if res != 0:
            print(f"    ERROR: Failed to initialize I2C device (error code: {res})")
            print("    Note: This example requires AC/DC expansion hardware")
            return 1
        print("    I2C device initialized successfully")
        
        # ===== STEP 2: Configure Force Mode =====
        print("\n[2] Configuring I2C force mode...")
        res = rp_hw.rp_I2C_setForceMode(force_mode)
        if res != 0:
            print(f"    ERROR: Failed to set force mode (error code: {res})")
            return 1
        print(f"    Force mode: {'Enabled' if force_mode else 'Disabled'}")
        
        # ===== STEP 3: Turn ON DC Mode (Channels 1 & 2) =====
        print(f"\n[3] Turning ON DC mode for channels 1 & 2...")
        if set_ac_dc_mode(DC_MODE_VALUE, "DC mode") != 0:
            return 1
        print(f"    DC mode active - holding for {dc_mode_duration} seconds...")
        time.sleep(dc_mode_duration)
        
        # ===== STEP 4: Turn ON AC Mode (Channels 1 & 2) =====
        print(f"\n[4] Turning ON AC mode for channels 1 & 2...")
        if set_ac_dc_mode(AC_MODE_VALUE, "AC mode") != 0:
            return 1
        print("    AC mode active")
        
        # ===== STEP 5: Read Back Current State =====
        print("\n[5] Reading back current AC/DC state...")
        read_value_tuple = rp_hw.rp_I2C_SMBUS_ReadWord(control_register)
        
        # Handle return value (could be tuple or single value depending on API)
        if isinstance(read_value_tuple, tuple):
            res, read_value = read_value_tuple
        else:
            res = read_value_tuple
            read_value = 0
        
        if res != 0:
            print(f"    ERROR: Failed to read value (error code: {res})")
            return 1
        
        print(f"    Read value: 0x{read_value:04X} (result: {res})")
        
        # Interpret the value
        if (read_value & ~LATCH_MASK) == (AC_MODE_VALUE & ~LATCH_MASK):
            print("    Current mode: AC (capacitive coupling)")
        elif (read_value & ~LATCH_MASK) == (DC_MODE_VALUE & ~LATCH_MASK):
            print("    Current mode: DC (direct coupling)")
        else:
            print(f"    Current mode: Unknown (0x{read_value:04X})")
        
        # ===== COMPLETION =====
        print("\n" + "=" * 70)
        print("AC/DC mode control test completed successfully")
        print("=" * 70)
        
        return 0
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
