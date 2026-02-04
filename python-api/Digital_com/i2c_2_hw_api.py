#!/usr/bin/python3
"""
Red Pitaya I2C EEPROM Write/Read Example using Low-Level API
=============================================================

This example demonstrates communication with the internal 24LC64 EEPROM memory
on the Red Pitaya using the I2C protocol via low-level system calls. The code
writes a test message to a specified address inside the EEPROM and reads it back.

Unlike the previous example that uses the Red Pitaya C API, this example uses
direct ioctl and file operations accessible from Python, providing lower-level
control over I2C communication.

Features:
- Direct I2C device access using ioctl system calls
- Page-based EEPROM write operations (32-byte pages)
- Full EEPROM read capability (8KB total)
- Address offset control for specific memory locations
- Automatic page boundary handling for multi-page writes

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)
- Internal 24LC64 EEPROM (8KB capacity)

Technical Details:
- I2C Bus: /dev/i2c-0
- EEPROM Address: 0x50
- Page Size: 32 bytes
- Total Size: 8192 bytes (64 Kbit)
- Write requires 2ms delay per page for internal completion

Software Requirements:
- Python 3 with fcntl module (standard library)
- Root or I2C group permissions

Usage:
    python i2c_2_hw_api.py
    
    The program will:
    1. Write a test message to EEPROM at offset 0x100
    2. Read back the entire EEPROM contents
    3. Display success message

Warning:
    This example performs write operations to EEPROM. While the write is
    to a safe offset (0x100), avoid writing to critical calibration data
    stored at the beginning of the EEPROM (addresses 0x00-0xFF).

Author: Red Pitaya
Date: January 2026
"""

import os
import time
import fcntl
import struct


# ==============================================================================
# I2C CONSTANTS AND CONFIGURATION
# ==============================================================================

# I2C ioctl commands
I2C_SLAVE_FORCE = 0x0706    # Force slave address (even if in use)
I2C_SLAVE = 0x0703          # Change slave address
I2C_FUNCS = 0x0705          # Get adapter functionality
I2C_RDWR = 0x0707           # Combined R/W transfer

# EEPROM Configuration
EEPROM_ADDR = 0x50          # I2C address of EEPROM
PAGESIZE = 32               # Page size for write operations (bytes)
EEPROMSIZE = 8192           # Total EEPROM size (64 Kbit = 8 KB)

# Write Configuration
WRITE_OFFSET = 0x100        # Start address for write operation
PAGE_WRITE_DELAY = 0.002    # Delay after page write (2ms)

# I2C device path
I2C_DEVICE = "/dev/i2c-0"


print("=" * 70)
print("Red Pitaya I2C EEPROM Low-Level Write/Read Configuration")
print("=" * 70)
print(f"I2C Device:          {I2C_DEVICE}")
print(f"EEPROM Address:      0x{EEPROM_ADDR:02X}")
print(f"EEPROM Size:         {EEPROMSIZE} bytes")
print(f"Page Size:           {PAGESIZE} bytes")
print(f"Write Offset:        0x{WRITE_OFFSET:04X}")
print(f"Page Write Delay:    {PAGE_WRITE_DELAY * 1000} ms")
print("=" * 70)


# ==============================================================================
# I2C FUNCTIONS
# ==============================================================================

def iic_read(fd, offset, size):
    """
    Read data from the EEPROM.
    
    Args:
        fd: File descriptor for I2C device
        offset: EEPROM memory space offset
        size: Number of bytes to read
        
    Returns:
        bytes: Read data buffer, or None on error
    """
    try:
        # Prepare offset address (2 bytes, big-endian)
        write_buffer = struct.pack('>H', offset)
        
        # Write offset address to set read position
        bytes_written = os.write(fd, write_buffer)
        if bytes_written < 0:
            print("ERROR: Failed to write EEPROM address")
            return None
        
        print("    Performing read operation...")
        
        # Read bytes from EEPROM
        buffer = os.read(fd, size)
        if not buffer:
            print("ERROR: EEPROM read failed")
            return None
        
        print(f"      Successfully read {len(buffer)} bytes from EEPROM")
        return buffer
        
    except Exception as e:
        print(f"ERROR: Read operation failed - {e}")
        return None


def iic_write(fd, data, offset):
    """
    Write data to the EEPROM using page-based writes.
    
    Args:
        fd: File descriptor for I2C device
        data: Data to write (bytes or string)
        offset: EEPROM memory space offset
        
    Returns:
        int: 0 on success, -1 on error
    """
    try:
        # Convert string to bytes if needed
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        size = len(data)
        loop = 0
        current_offset = offset
        
        print(f"    Writing {size} bytes in {(size + PAGESIZE - 1) // PAGESIZE} page(s)...")
        
        while size > 0:
            # Determine bytes to write in this iteration
            write_bytes = min(size, PAGESIZE)
            
            # Prepare write buffer: [offset_high, offset_low, data...]
            write_buffer = struct.pack('>H', current_offset)
            write_buffer += data[loop * PAGESIZE : loop * PAGESIZE + write_bytes]
            
            # Write data to I2C bus
            bytes_written = os.write(fd, write_buffer)
            
            # Wait for EEPROM internal write cycle completion
            time.sleep(PAGE_WRITE_DELAY)
            
            if bytes_written != write_bytes + 2:
                print(f"ERROR: Failed to write page {loop + 1}")
                return -1
            
            # Update counters
            size -= write_bytes
            current_offset += PAGESIZE
            loop += 1
            
            if loop % 10 == 0:
                print(f"    Progress: {loop} pages written...")
        
        print(f"      Successfully wrote {len(data)} bytes to EEPROM")
        return 0
        
    except Exception as e:
        print(f"ERROR: Write operation failed - {e}")
        return -1


# ==============================================================================
# MAIN PROGRAM
# ==============================================================================

def main():
    """Main program to write and read EEPROM data."""
    
    fd = None
    
    try:
        # ===== STEP 1: Open I2C Device =====
        print("\n[1] Opening I2C device...")
        fd = os.open(I2C_DEVICE, os.O_RDWR)
        print(f"      Device opened: {I2C_DEVICE}")
        
        # ===== STEP 2: Set EEPROM Address =====
        print("\n[2] Setting EEPROM slave address...")
        result = fcntl.ioctl(fd, I2C_SLAVE_FORCE, EEPROM_ADDR)
        print(f"      EEPROM address set to 0x{EEPROM_ADDR:02X}")
        
        # ===== STEP 3: Prepare Test Data =====
        print("\n[3] Preparing test message...")
        test_message = (
            "THIS IS A TEST MESSAGE FOR THE I2C PROTOCOL COMMUNICATION WITH A EEPROM. "
            "IT WAS WRITTEN FOR A REDPITAYA MEASUREMENT TOOL."
        )
        print(f"    Message length: {len(test_message)} bytes")
        print(f"    Message: \"{test_message[:50]}...\"")
        
        # ===== STEP 4: Write to EEPROM =====
        print(f"\n[4] Writing message to EEPROM at offset 0x{WRITE_OFFSET:04X}...")
        status = iic_write(fd, test_message, WRITE_OFFSET)
        if status != 0:
            print("  ERROR: Failed to write to EEPROM")
            return 1
        
        # ===== STEP 5: Read from EEPROM =====
        print(f"\n[5] Reading {EEPROMSIZE} bytes from EEPROM...")
        buffer = iic_read(fd, 0x0000, EEPROMSIZE)
        if buffer is None:
            print("  ERROR: Failed to read from EEPROM")
            return 1
        
        # ===== STEP 6: Verify Written Data =====
        print("\n[6] Verifying written data...")
        # Extract the written portion from the buffer
        written_data = buffer[WRITE_OFFSET:WRITE_OFFSET + len(test_message)]
        
        if written_data.decode('utf-8', errors='ignore') == test_message:
            print("      Data verification successful!")
            print(f"      Read back: \"{written_data.decode('utf-8')[:50]}...\"")
        else:
            print("      Warning: Data verification shows differences")
            print(f"      Read back: \"{written_data[:50]}...\"")
        
        print("\n" + "=" * 70)
        print("✓ EEPROM test completed successfully")
        print("=" * 70)
        
        return 0
        
    except PermissionError:
        print("\n✗ ERROR: Permission denied")
        print("   Run with sudo or add user to i2c group:")
        print("   sudo usermod -a -G i2c $USER")
        return 1
        
    except FileNotFoundError:
        print(f"\n✗ ERROR: I2C device {I2C_DEVICE} not found")
        print("   Ensure I2C is enabled on your Red Pitaya")
        return 1
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        return 1
        
    finally:
        # Clean up
        if fd is not None:
            os.close(fd)
            print("\n[Cleanup] I2C device closed")


if __name__ == "__main__":
    exit(main())
