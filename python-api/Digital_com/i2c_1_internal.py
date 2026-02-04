#!/usr/bin/python3
"""
Red Pitaya I2C EEPROM Access Example
=====================================

This example demonstrates how to access the internal EEPROM via I2C on Red Pitaya.
It reads calibration data stored in the EEPROM and displays it. The EEPROM contains
factory calibration parameters that are used to correct ADC and DAC measurements.

Features:
- I2C device initialization and configuration
- EEPROM read operations
- Data format detection and handling
- Calibration data conversion and display
- Force mode operation for reliable I2C communication

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)
- Internal EEPROM at I2C address 0x50

Technical Details:
- I2C Bus: /dev/i2c-0
- EEPROM Address: 0x50
- Supports multiple calibration data formats
- Uses force mode for direct I2C access

Software Requirements:
- Red Pitaya hardware libraries (rp_hw module)
- Red Pitaya calibration libraries (rp_hw_calib module)

Usage:
    python i2c_1_internal.py
    
    The program will read and display calibration data from the EEPROM.
    This includes ADC and DAC calibration parameters.

Note:
    This example accesses internal hardware. Ensure proper permissions
    for I2C device access. The EEPROM contains critical calibration data.

Author: Red Pitaya
Date: January 2026
"""

import time
import rp_hw
import rp_hw_calib


# ==============================================================================
# CONFIGURATION - Set your I2C parameters here
# ==============================================================================

# I2C device configuration
i2c_device = "/dev/i2c-0"       # I2C bus device
eeprom_address = 0x50           # EEPROM I2C address
force_mode = True               # Enable force mode for direct access
read_delay = 0.1                # Delay between operations (seconds)

print("=" * 70)
print("Red Pitaya I2C EEPROM Reader Configuration")
print("=" * 70)
print(f"I2C Device:          {i2c_device}")
print(f"EEPROM Address:      0x{eeprom_address:02X}")
print(f"Force Mode:          {force_mode}")
print(f"Read Delay:          {read_delay} seconds")
print("=" * 70)


# ==============================================================================
# MAIN PROGRAM
# ==============================================================================

def main():
    """Main program to read and display EEPROM calibration data."""
    
    try:
        # ===== STEP 1: Initialize I2C Device =====
        print("\n[1] Initializing I2C device...")
        res = rp_hw.rp_I2C_InitDevice(i2c_device, eeprom_address)
        print(f"    Init result: {res}")
        
        if res != 0:
            print("    ERROR: Failed to initialize I2C device")
            return 1

        # ===== STEP 2: Set Force Mode =====
        print("\n[2] Configuring I2C force mode...")
        res = rp_hw.rp_I2C_setForceMode(force_mode)
        print(f"    Force mode result: {res}")

        # ===== STEP 3: Set Read Position =====
        print("\n[3] Setting EEPROM read position to 0x0000...")
        wb = bytes([0, 0])  # Start address: 0x0000
        res = rp_hw.rp_I2C_IOCTL_WriteBuffer(wb, 2)
        print(f"    Write position result: {res}")
        
        time.sleep(read_delay)

        # ===== STEP 4: Read Data Format =====
        print("\n[4] Reading data format byte...")
        rb = bytearray(1)
        res = rp_hw.rp_I2C_IOCTL_ReadBuffer(rb, 1)
        print(f"    Read result: {res}")
        
        data_format = rb[0]
        print(f"    Data format: {data_format}")
        
        # ===== STEP 5: Reset Read Position =====
        print("\n[5] Resetting read position...")
        res = rp_hw.rp_I2C_IOCTL_WriteBuffer(wb, 2)
        print(f"    Write position result: {res}")
        
        time.sleep(read_delay)

        # ===== STEP 6: Read Calibration Data =====
        print("\n[6] Reading and converting calibration data...")
        calib = rp_hw_calib.rp_calib_params_t()

        if data_format == 5:
            print("    Using universal calibration format...")
            data = rp_hw_calib.rp_calib_params_universal_t()
            size = len(data)
            res = rp_hw.rp_I2C_IOCTL_ReadBuffer(data, size)
            print(f"    Read {size} bytes: result={res}")
            
            res = rp_hw_calib.rp_CalibConvertEEPROM(data, size, calib)
            print(f"    Conversion result: {res}")
        else:
            print("    Using legacy calibration format...")
            data = rp_hw_calib.rp_eepromWpData_t()
            size = len(data)
            res = rp_hw.rp_I2C_IOCTL_ReadBuffer(data, size)
            print(f"    Read {size} bytes: result={res}")
            
            res = rp_hw_calib.rp_CalibConvertEEPROM(data, size, calib)
            print(f"    Conversion result: {res}")

        # ===== STEP 7: Display Calibration Data =====
        print("\n[7] Calibration Parameters:")
        print("=" * 70)
        rp_hw_calib.rp_CalibPrint(calib)
        print("=" * 70)
        
        print("\n✓ EEPROM read completed successfully")
        return 0
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
