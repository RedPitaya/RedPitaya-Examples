#!/usr/bin/python3
"""
Red Pitaya Internal I2C EEPROM Read Example
============================================

This example demonstrates how to read raw data from the internal EEPROM
on Red Pitaya via the I2C bus using the rp_hw API.

The internal EEPROM stores factory calibration parameters. This example
reads the raw byte contents and displays them in hexadecimal. For
interpretation and conversion of calibration data, see the Calibration
examples.

Features:
- I2C device initialization and configuration
- Force mode operation for reliable I2C communication
- Buffer-based EEPROM read at a configurable address and size
- Formatted hexadecimal + ASCII output

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)
- Internal EEPROM at I2C address 0x50

Technical Details:
- I2C Bus: /dev/i2c-0
- EEPROM Address: 0x50
- Uses force mode for direct I2C access

Software Requirements:
- Red Pitaya hardware library (rp_hw module)

Usage:
    python i2c_1_internal.py

Note:
    The EEPROM contains critical factory calibration data — this example
    is read-only and does not modify any EEPROM contents.

Author: Red Pitaya
Date: May 2026
"""

import numpy as np
import time
import rp_hw


# ==============================================================================
# CONFIGURATION - Set your I2C parameters here
# ==============================================================================

i2c_device     = "/dev/i2c-0"   # I2C bus device
eeprom_address = 0x50           # Internal EEPROM I2C address
force_mode     = True           # Force mode for direct I2C access
read_offset    = 0x0000         # EEPROM address to start reading from
read_size      = 64             # Number of bytes to read
read_delay     = 0.1            # Delay between write-pointer and read (seconds)

print("=" * 70)
print("Red Pitaya Internal I2C EEPROM Read")
print("=" * 70)
print(f"I2C Device:     {i2c_device}")
print(f"EEPROM Address: 0x{eeprom_address:02X}")
print(f"Read Offset:    0x{read_offset:04X}")
print(f"Read Size:      {read_size} bytes")
print("=" * 70)


# ==============================================================================
# MAIN PROGRAM
# ==============================================================================

def main():
    """Read raw bytes from the internal EEPROM and display them."""

    try:
        # ===== STEP 1: Initialize I2C Device =====
        print("\n[1] Initializing I2C device...")
        res = rp_hw.rp_I2C_InitDevice(i2c_device, eeprom_address)
        if res != 0:
            print(f"    ERROR: Failed to initialize I2C device (error code: {res})")
            return 1
        print("    I2C device initialized successfully")

        # ===== STEP 2: Set Force Mode =====
        print("\n[2] Configuring I2C force mode...")
        rp_hw.rp_I2C_setForceMode(force_mode)
        print(f"    Force mode: {'Enabled' if force_mode else 'Disabled'}")

        # ===== STEP 3: Set Read Pointer =====
        print(f"\n[3] Setting read pointer to 0x{read_offset:04X}...")
        addr_buf = np.array([read_offset >> 8, read_offset & 0xFF], dtype=np.uint8)
        res = rp_hw.rp_I2C_IOCTL_WriteBuffer(addr_buf)
        if res != 0:
            print(f"    ERROR: Failed to set read pointer (error code: {res})")
            return 1
        print("    Read pointer set successfully")

        time.sleep(read_delay)

        # ===== STEP 4: Read Data =====
        print(f"\n[4] Reading {read_size} bytes from EEPROM...")
        rx_buf = np.zeros(read_size, dtype=np.uint8)
        res = rp_hw.rp_I2C_IOCTL_ReadBuffer(rx_buf)
        if res != 0:
            print(f"    ERROR: Read failed (error code: {res})")
            return 1
        print("    Read successful")

        # ===== STEP 5: Display Raw Data =====
        print(f"\n[5] EEPROM contents at offset 0x{read_offset:04X}:")
        print("-" * 70)
        for i in range(0, read_size, 16):
            row = rx_buf[i:i + 16]
            hex_str   = ' '.join(f'{b:02X}' for b in row)
            ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in row)
            print(f"  0x{read_offset + i:04X}:  {hex_str:<47}  {ascii_str}")
        print("-" * 70)

        print("\n✓ EEPROM read completed successfully")
        return 0

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
