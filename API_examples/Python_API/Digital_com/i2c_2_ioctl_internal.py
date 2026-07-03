#!/usr/bin/python3
"""
Red Pitaya Internal I2C EEPROM Read using Low-Level ioctl
==========================================================

This example demonstrates how to read raw data from the internal EEPROM on
Red Pitaya using direct Linux I2C ioctl system calls, without relying on the
rp_hw API.

Contrast with i2c_1_internal.py, which performs the same operation through
the high-level rp_hw API. This example gives you direct control over the I2C
bus and is useful for porting to other languages or environments where the
rp_hw library is not available.

Features:
- Direct I2C device access using ioctl system calls
- Configurable read offset and size
- Formatted hexadecimal + ASCII output

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)
- Internal EEPROM (8KB capacity)

Technical Details:
- I2C Bus: /dev/i2c-0
- EEPROM Address: 0x50
- Total Size: 8192 bytes (64 Kbit)

Note:
    The internal EEPROM is hardware write-protected on all Red Pitaya boards
    (WP pin is tied high). This example is therefore read-only. For write/read
    demonstrations, see i2c_3_external.py which uses an external EEPROM.

Software Requirements:
- Python 3 with fcntl module (standard library on Linux)
- Root or I2C group permissions

Usage:
    python i2c_2_ioctl_internal.py

Author: Red Pitaya
Date: May 2026
"""

import os
import time
import fcntl
import struct


# ==============================================================================
# I2C CONSTANTS AND CONFIGURATION
# ==============================================================================

# I2C ioctl commands
I2C_SLAVE_FORCE = 0x0706    # Force slave address (even if device is in use)
I2C_SLAVE       = 0x0703    # Set slave address

# EEPROM Configuration
EEPROM_ADDR  = 0x50         # Internal EEPROM I2C address
EEPROMSIZE   = 8192         # Total EEPROM size (64 Kbit = 8 KB)

# Read Configuration
READ_OFFSET = 0x0000        # Start address for read operation
READ_SIZE   = 64            # Number of bytes to read

# I2C device path
I2C_DEVICE = "/dev/i2c-0"


print("=" * 70)
print("Red Pitaya Internal I2C EEPROM Low-Level Read")
print("=" * 70)
print(f"I2C Device:     {I2C_DEVICE}")
print(f"EEPROM Address: 0x{EEPROM_ADDR:02X}")
print(f"Read Offset:    0x{READ_OFFSET:04X}")
print(f"Read Size:      {READ_SIZE} bytes")
print("=" * 70)


# ==============================================================================
# I2C FUNCTIONS
# ==============================================================================

def iic_read(fd, offset, size):
    """
    Read data from the EEPROM at the given offset.

    Args:
        fd:     File descriptor for I2C device
        offset: EEPROM memory address to read from
        size:   Number of bytes to read

    Returns:
        bytes: Read data, or None on error
    """
    try:
        # Write the 2-byte address to set the internal read pointer
        addr_buf = struct.pack('>H', offset)
        os.write(fd, addr_buf)

        # Small delay to let the EEPROM process the address
        time.sleep(0.001)

        # Read the requested number of bytes
        data = os.read(fd, size)
        return data

    except Exception as e:
        print(f"    ERROR: Read failed - {e}")
        return None


# ==============================================================================
# MAIN PROGRAM
# ==============================================================================

def main():
    """Read raw bytes from the internal EEPROM and display them."""

    fd = None

    try:
        # ===== STEP 1: Open I2C Device =====
        print("\n[1] Opening I2C device...")
        fd = os.open(I2C_DEVICE, os.O_RDWR)
        print(f"    Opened: {I2C_DEVICE}")

        # ===== STEP 2: Set EEPROM Slave Address =====
        print("\n[2] Setting EEPROM slave address...")
        fcntl.ioctl(fd, I2C_SLAVE_FORCE, EEPROM_ADDR)
        print(f"    Slave address: 0x{EEPROM_ADDR:02X}")

        # ===== STEP 3: Read Data =====
        print(f"\n[3] Reading {READ_SIZE} bytes from offset 0x{READ_OFFSET:04X}...")
        data = iic_read(fd, READ_OFFSET, READ_SIZE)
        if data is None:
            print("    ERROR: Read operation failed")
            return 1
        print(f"    Read {len(data)} bytes successfully")

        # ===== STEP 4: Display Data =====
        print(f"\n[4] EEPROM contents at offset 0x{READ_OFFSET:04X}:")
        print("-" * 70)
        for i in range(0, len(data), 16):
            row = data[i:i + 16]
            hex_str   = ' '.join(f'{b:02X}' for b in row)
            ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in row)
            print(f"  0x{READ_OFFSET + i:04X}:  {hex_str:<47}  {ascii_str}")
        print("-" * 70)

        print("\n✓ EEPROM read completed successfully")
        return 0

    except PermissionError:
        print("\n✗ ERROR: Permission denied — run as root or add user to the i2c group:")
        print("   sudo usermod -a -G i2c $USER")
        return 1

    except FileNotFoundError:
        print(f"\n✗ ERROR: I2C device {I2C_DEVICE} not found")
        return 1

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        return 1

    finally:
        if fd is not None:
            os.close(fd)
            print("\n[Cleanup] I2C device closed")


if __name__ == "__main__":
    exit(main())
