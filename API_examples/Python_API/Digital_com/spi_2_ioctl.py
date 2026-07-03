#!/usr/bin/python3
"""
Red Pitaya SPI Low-Level Hardware API Example
==============================================

This example demonstrates low-level SPI communication on Red Pitaya using direct
ioctl system calls. Unlike the higher-level rp_hw API, this approach provides
direct control over the SPI hardware interface, similar to C code that uses
Linux SPI device drivers.

The example performs:
- SPI device initialization with custom parameters
- Simple write operation to SPI bus
- Multi-transfer read operation with SPI_IOC_MESSAGE
- Flash ID read command (0x9F) for testing
- Loopback data verification

Features:
- Direct ioctl-based SPI control
- Configurable SPI mode and speed
- Multiple transfer operations in single ioctl call
- Flash command example (RDID - Read ID)
- Write and read operations
- Low-level hardware access

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)

Setup for Loopback Test:
    Connect the following pins on the E2 connector:
    - MOSI to MISO with a jumper wire for loopback testing
    
    Or connect to external SPI Flash/device:
    - MOSI -> Device MOSI
    - MISO -> Device MISO
    - SCLK -> Device SCLK
    - CS   -> Device CS

Technical Details:
- SPI Device: /dev/spidev1.0
- Default Speed: 1 MHz (1000000 Hz)
- Uses ioctl system calls for low-level control
- Supports SPI mode configuration (CPHA, CPOL, etc.)
- Multi-transfer capability using SPI_IOC_MESSAGE

SPI Mode Flags (can be combined with |):
- SPI_LOOP: Loopback mode
- SPI_CPHA: Clock phase
- SPI_CPOL: Clock polarity
- SPI_LSB_FIRST: LSB transmitted first
- SPI_CS_HIGH: Chip select active high
- SPI_3WIRE: 3-wire mode (bidirectional)
- SPI_NO_CS: No chip select
- SPI_READY: Slave ready signal

Software Requirements:
- Python 3 with fcntl module (standard library)
- Root or SPI group permissions

Usage:
    python spi_2_ioctl.py
    
    The program will:
    1. Initialize SPI interface
    2. Write test data to SPI bus
    3. Read flash ID (0x9F command)
    4. Display received data
    5. Clean up resources

Note:
    This example uses low-level system calls and requires proper hardware
    connections. Incorrect configuration may cause communication failures.

Author: Red Pitaya
Date: May 2026
"""

import os
import fcntl
import struct
import ctypes


# ==============================================================================
# SPI CONSTANTS AND CONFIGURATION
# ==============================================================================

# _IOC helper — implements the Linux _IOC() macro (linux/ioctl.h)
_IOC_NRSHIFT   = 0
_IOC_TYPESHIFT = 8
_IOC_SIZESHIFT = 16
_IOC_DIRSHIFT  = 30
_IOC_WRITE = 1
_IOC_READ  = 2

def _IOC(dir_, type_, nr, size):
    return (dir_ << _IOC_DIRSHIFT) | (type_ << _IOC_TYPESHIFT) | (nr << _IOC_NRSHIFT) | (size << _IOC_SIZESHIFT)


# SPI ioctl commands (from linux/spi/spidev.h)
SPI_IOC_MAGIC = 107  # 'k'

# SPI mode flags
SPI_CPHA = 0x01      # Clock phase
SPI_CPOL = 0x02      # Clock polarity
SPI_MODE_0 = 0       # (0,0)
SPI_MODE_1 = SPI_CPHA
SPI_MODE_2 = SPI_CPOL
SPI_MODE_3 = SPI_CPHA | SPI_CPOL
SPI_CS_HIGH = 0x04   # Chip select active high
SPI_LSB_FIRST = 0x08 # LSB first
SPI_3WIRE = 0x10     # 3-wire mode
SPI_LOOP = 0x20      # Loopback mode
SPI_NO_CS = 0x40     # No chip select
SPI_READY = 0x80     # Slave pulls low to pause

# ioctl command codes
SPI_IOC_WR_MODE = _IOC(_IOC_WRITE, SPI_IOC_MAGIC, 1, 1)
SPI_IOC_RD_MODE = _IOC(_IOC_READ, SPI_IOC_MAGIC, 1, 1)
SPI_IOC_WR_MAX_SPEED_HZ = _IOC(_IOC_WRITE, SPI_IOC_MAGIC, 4, 4)
SPI_IOC_RD_MAX_SPEED_HZ = _IOC(_IOC_READ, SPI_IOC_MAGIC, 4, 4)

# Configuration
SPI_DEVICE = "/dev/spidev2.0"  # SPI device path
SPI_MODE = 0                    # SPI mode (0-3)
SPI_SPEED = 1000000             # SPI clock speed in Hz (1 MHz)
TEST_MESSAGE = "REDPITAYA SPI TEST"

print("=" * 70)
print("Red Pitaya SPI Low-Level Hardware API Configuration")
print("=" * 70)
print(f"SPI Device:          {SPI_DEVICE}")
print(f"SPI Mode:            {SPI_MODE}")
print(f"SPI Speed:           {SPI_SPEED / 1000000:.1f} MHz")
print(f"Test Message:        \"{TEST_MESSAGE}\"")
print("=" * 70)


# ==============================================================================
# SPI TRANSFER STRUCTURE
# ==============================================================================

class spi_ioc_transfer(ctypes.Structure):
    """SPI transfer structure for ioctl operations."""
    _fields_ = [
        ("tx_buf", ctypes.c_uint64),
        ("rx_buf", ctypes.c_uint64),
        ("len", ctypes.c_uint32),
        ("speed_hz", ctypes.c_uint32),
        ("delay_usecs", ctypes.c_uint16),
        ("bits_per_word", ctypes.c_uint8),
        ("cs_change", ctypes.c_uint8),
        ("tx_nbits", ctypes.c_uint8),
        ("rx_nbits", ctypes.c_uint8),
        ("pad", ctypes.c_uint16),
    ]


def SPI_IOC_MESSAGE(n):
    """Generate ioctl command for n SPI transfers."""
    return _IOC(_IOC_WRITE, SPI_IOC_MAGIC, 0, n * ctypes.sizeof(spi_ioc_transfer))


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def init_spi():
    """
    Initialize SPI interface with specified mode and speed.
    
    Returns:
        int: File descriptor on success, -1 on error
    """
    try:
        # Open SPI device
        fd = os.open(SPI_DEVICE, os.O_RDWR | os.O_NOCTTY)
        
        # Set SPI mode
        mode_bytes = struct.pack('B', SPI_MODE)
        fcntl.ioctl(fd, SPI_IOC_WR_MODE, mode_bytes)
        
        # Set SPI speed
        speed_bytes = struct.pack('I', SPI_SPEED)
        fcntl.ioctl(fd, SPI_IOC_WR_MAX_SPEED_HZ, speed_bytes)
        
        return fd
        
    except Exception as e:
        print(f"    ERROR: Failed to initialize SPI - {e}")
        return -1


def write_spi(fd, data):
    """
    Write data to SPI bus using simple write operation.
    
    Args:
        fd: File descriptor for SPI device
        data: String or bytes to write
        
    Returns:
        int: 0 on success, -1 on error
    """
    try:
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        bytes_written = os.write(fd, data)
        
        if bytes_written != len(data):
            print(f"    WARNING: Partial write - {bytes_written}/{len(data)} bytes")
        
        return 0
        
    except Exception as e:
        print(f"    ERROR: Failed to write to SPI - {e}")
        return -1


def read_flash_id(fd):
    """
    Read flash ID and perform loopback test using multi-transfer ioctl.
    
    Sends RDID command (0x9F) and sample loopback data in a single
    multi-transfer operation.
    
    Args:
        fd: File descriptor for SPI device
        
    Returns:
        int: 0 on success, -1 on error
    """
    try:
        # Prepare buffers as mutable ctypes char arrays so addressof() works
        buf0 = ctypes.create_string_buffer(bytes([0x9F]), 1)   # RDID command
        buf1 = ctypes.create_string_buffer(bytes([0x01, 0x23, 0x45]), 3)  # Sample loopback data

        # Create transfer structures
        xfer0 = spi_ioc_transfer()
        xfer0.tx_buf = ctypes.addressof(buf0)
        xfer0.rx_buf = ctypes.addressof(buf0)
        xfer0.len = ctypes.sizeof(buf0)

        xfer1 = spi_ioc_transfer()
        xfer1.tx_buf = ctypes.addressof(buf1)
        xfer1.rx_buf = ctypes.addressof(buf1)
        xfer1.len = ctypes.sizeof(buf1)

        # Create array of transfers
        xfer_array = (spi_ioc_transfer * 2)(xfer0, xfer1)

        # Perform multi-transfer ioctl
        fcntl.ioctl(fd, SPI_IOC_MESSAGE(2), xfer_array)

        return bytearray(buf1.raw)
        
    except Exception as e:
        print(f"    ERROR: Failed to read from SPI - {e}")
        return None


# ==============================================================================
# MAIN PROGRAM
# ==============================================================================

def main():
    """Main program for low-level SPI communication test."""
    
    spi_fd = -1
    
    try:
        # ===== STEP 1: Initialize SPI =====
        print("\n[1] Initializing SPI interface...")
        spi_fd = init_spi()
        if spi_fd < 0:
            print("    ERROR: SPI initialization failed")
            return 1
        print(f"    SPI device opened (fd: {spi_fd})")
        print(f"    Mode: {SPI_MODE}, Speed: {SPI_SPEED / 1000000:.1f} MHz")
        
        # ===== STEP 2: Write Test Data =====
        print("\n[2] Writing test message to SPI bus...")
        print(f"    Message: \"{TEST_MESSAGE}\"")
        if write_spi(spi_fd, TEST_MESSAGE) < 0:
            print("    ERROR: Write operation failed")
            return 1
        print(f"    {len(TEST_MESSAGE)} bytes written successfully")
        
        # ===== STEP 3: Read Flash ID and Loopback Data =====
        print("\n[3] Performing multi-transfer read operation...")
        print("    Transfer 0: RDID command (0x9F)")
        print("    Transfer 1: Loopback data (0x01, 0x23, 0x45)")
        
        result = read_flash_id(spi_fd)
        if result is None:
            print("    ERROR: Read operation failed")
            return 1
        
        print("\n    Received loopback data:")
        for i, byte in enumerate(result):
            print(f"        Buffer[{i}]: 0x{byte:02X} ({byte})")
        
        # ===== STEP 4: Verify Loopback =====
        print("\n[4] Verifying loopback data...")
        expected = [0x01, 0x23, 0x45]
        match = all(result[i] == expected[i] for i in range(len(expected)))
        
        if match:
            print("    Data verification: MATCH")
            print("    Loopback test successful")
        else:
            print("    Data verification: MISMATCH")
            print(f"    Expected: {[f'0x{b:02X}' for b in expected]}")
            print(f"    Received: {[f'0x{b:02X}' for b in result]}")
        
        # ===== COMPLETION =====
        print("\n" + "=" * 70)
        if match:
            print("SPI low-level test completed successfully")
        else:
            print("SPI low-level test completed - Loopback verification failed")
        print("=" * 70)
        
        return 0 if match else 1
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    finally:
        # ===== CLEANUP =====
        if spi_fd >= 0:
            print("\n[Cleanup] Releasing SPI resources...")
            os.close(spi_fd)
            print("    SPI device closed")


if __name__ == "__main__":
    exit(main())
