#!/usr/bin/python3
"""
Red Pitaya External I2C EEPROM Write/Read Example
==================================================

This example demonstrates communication with an external 24LC64 EEPROM memory
using the I2C protocol via Red Pitaya's hardware API. The code writes a test
string to the EEPROM, reads it back, and verifies the operation. It also
demonstrates reading from different memory locations to show EEPROM addressing.

Features:
- External I2C EEPROM communication (24LC64)
- Force mode operation for reliable I2C access
- Buffer-based write operations
- Address pointer manipulation
- Multiple read operations from different offsets
- Data verification with ASCII conversion

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)
- External 24LC64 EEPROM (8KB capacity)
- I2C connections: SDA, SCL, GND, and VCC

Connection Diagram:
    Red Pitaya                    24LC64 EEPROM
    ============                  ==============
    I2C0 SDA      <------------>  SDA (Pin 5)
    I2C0 SCL      <------------>  SCL (Pin 6)
    GND           <------------>  GND (Pin 4)
    3.3V          <------------>  VCC (Pin 8)
    
    Address Pins (typical for 0b1010110 = 0x56):
    A0 (Pin 1)    -> GND
    A1 (Pin 2)    -> GND
    A2 (Pin 3)    -> VCC

Technical Details:
- I2C Bus: /dev/i2c-0
- EEPROM Address: 0x56 (0b1010110)
- EEPROM Size: 8192 bytes (64 Kbit)
- Page Size: 32 bytes
- Write delay: 5ms for internal completion
- Read delay: 1ms between operations

Software Requirements:
- Red Pitaya hardware library (rp_hw module)

Usage:
    python i2c_3_ioctl_external.py
    
    The program will:
    1. Write test string to EEPROM at address 0x0000
    2. Read back the data and verify
    3. Read from offset after written data

Note:
    Ensure the external EEPROM is properly connected and powered.
    Incorrect I2C address will result in communication failure.
    Check A0, A1, A2 pins to determine correct I2C address.

Author: Red Pitaya
Date: January 2026
"""

import time
import rp_hw


# ==============================================================================
# CONFIGURATION - Set your I2C and EEPROM parameters here
# ==============================================================================

# I2C Configuration
i2c_device = "/dev/i2c-0"       # I2C bus device
eeprom_address = 0b1010110      # 24LC64 I2C address (0x56)
force_mode = True               # Enable force mode for direct access

# EEPROM Specifications
EEPROM_SIZE = 8192              # Total EEPROM size (64 Kbit = 8 KB)
PAGE_SIZE = 32                  # EEPROM page size in bytes

# Test Data Configuration
test_message = "TEST string"    # Message to write to EEPROM
write_offset = 0x0000           # Starting address for write operation
write_delay = 0.005             # Delay after write (5ms)
read_delay = 0.001              # Delay before read (1ms)

print("=" * 70)
print("Red Pitaya External I2C EEPROM Write/Read Configuration")
print("=" * 70)
print(f"I2C Device:          {i2c_device}")
print(f"EEPROM Address:      0x{eeprom_address:02X} (0b{eeprom_address:07b})")
print(f"EEPROM Size:         {EEPROM_SIZE} bytes")
print(f"Page Size:           {PAGE_SIZE} bytes")
print(f"Test Message:        \"{test_message}\"")
print(f"Write Offset:        0x{write_offset:04X}")
print(f"Write Delay:         {write_delay * 1000} ms")
print(f"Read Delay:          {read_delay * 1000} ms")
print("=" * 70)


# ==============================================================================
# MAIN PROGRAM
# ==============================================================================

def main():
    """Main program to write and read external EEPROM data."""
    
    try:
        # Prepare test data
        data_int = [ord(char) for char in test_message]
        data_size = len(data_int)
        
        # ===== STEP 1: Initialize I2C Device =====
        print("\n[1] Initializing I2C device...")
        res = rp_hw.rp_I2C_InitDevice(i2c_device, eeprom_address)
        if res != 0:
            print(f"    ERROR: Failed to initialize I2C device (error code: {res})")
            return 1
        print("    I2C device initialized successfully")
        
        # ===== STEP 2: Configure Force Mode =====
        print("\n[2] Configuring I2C force mode...")
        rp_hw.rp_I2C_setForceMode(force_mode)
        print(f"    Force mode: {'Enabled' if force_mode else 'Disabled'}")
        
        # ===== STEP 3: Verify Device Address =====
        print("\n[3] Verifying device address...")
        res = rp_hw.rp_I2C_getDevAddress()
        device_addr = res[1] if isinstance(res, tuple) else res
        print(f"    Device address: 0x{device_addr:02X}")
        
        # ===== STEP 4: Prepare Write Buffer =====
        print("\n[4] Preparing write buffer...")
        rx_buff = rp_hw.Buffer(PAGE_SIZE + 2)
        
        # Set memory address (2 bytes, big-endian)
        rx_buff[0] = write_offset >> 8      # High byte
        rx_buff[1] = write_offset & 0xFF    # Low byte
        
        # Copy data to buffer
        for i in range(data_size):
            rx_buff[i + 2] = data_int[i]
        
        print(f"    Buffer prepared: {data_size} bytes + 2 address bytes")
        print(f"    Data: {[chr(data_int[i]) for i in range(data_size)]}")
        
        # ===== STEP 5: Write Data to EEPROM =====
        print(f"\n[5] Writing data to EEPROM at address 0x{write_offset:04X}...")
        res = rp_hw.rp_I2C_IOCTL_WriteBuffer(rx_buff, data_size + 2)
        if res != 0:
            print(f"    ERROR: Write failed (error code: {res})")
            return 1
        print(f"    Data written successfully (result: {res})")
        
        # Wait for EEPROM internal write cycle
        time.sleep(write_delay)
        
        # ===== STEP 6: Set Read Pointer to Start =====
        print(f"\n[6] Setting read pointer to address 0x{write_offset:04X}...")
        rx_buff[0] = write_offset >> 8      # High byte
        rx_buff[1] = write_offset & 0xFF    # Low byte
        
        res = rp_hw.rp_I2C_IOCTL_WriteBuffer(rx_buff, 2)
        print(f"    Read pointer set (result: {res})")
        
        time.sleep(read_delay)
        
        # ===== STEP 7: Read Data from Start Address =====
        print(f"\n[7] Reading {data_size} bytes from EEPROM...")
        res = rp_hw.rp_I2C_IOCTL_ReadBuffer(rx_buff, data_size + 2)
        if res != 0:
            print(f"    ERROR: Read failed (error code: {res})")
            return 1
        
        # Extract and display read data
        data_read = ''.join([chr(rx_buff[i]) for i in range(data_size)])
        print(f"    Read successful (result: {res})")
        print(f"    Read data: \"{data_read}\"")
        
        # Verify data
        if data_read == test_message:
            print("    Data verification: MATCH")
        else:
            print("    WARNING: Data verification: MISMATCH")
            print(f"    Expected: \"{test_message}\"")
            print(f"    Got:      \"{data_read}\"")
        
        # ===== STEP 8: Set Read Pointer After Written Data =====
        offset_after = data_size
        print(f"\n[8] Setting read pointer to address 0x{offset_after:04X}...")
        rx_buff[0] = offset_after >> 8      # High byte
        rx_buff[1] = offset_after & 0xFF    # Low byte
        
        res = rp_hw.rp_I2C_IOCTL_WriteBuffer(rx_buff, 2)
        print(f"    Read pointer set (result: {res})")
        
        # ===== STEP 9: Read Data After Written Data =====
        print(f"\n[9] Reading {data_size} bytes from offset 0x{offset_after:04X}...")
        res = rp_hw.rp_I2C_IOCTL_ReadBuffer(rx_buff, data_size + 2)
        if res != 0:
            print(f"    ERROR: Read failed (error code: {res})")
            return 1
        
        # Extract and display read data
        data_read_after = ''.join([chr(rx_buff[i]) for i in range(data_size)])
        print(f"    Read successful (result: {res})")
        print(f"    Read data: \"{data_read_after}\"")
        print(f"    (This shows data at different EEPROM location)")
        
        # ===== COMPLETION =====
        print("\n" + "=" * 70)
        print("External EEPROM test completed successfully")
        print("=" * 70)
        
        return 0
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
