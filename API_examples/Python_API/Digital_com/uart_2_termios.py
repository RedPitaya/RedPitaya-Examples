#!/usr/bin/python3
"""
Red Pitaya UART Low-Level Hardware API Example
===============================================

This example demonstrates low-level UART communication on Red Pitaya using direct
termios system calls. Unlike the higher-level rp_hw API, this approach provides
direct control over the UART hardware interface using Linux termios library,
similar to C code that uses system calls.

The example performs:
- UART device initialization with custom termios settings
- Write operation to UART TX
- Non-blocking read operation from UART RX with retry logic
- Loopback testing capability

Features:
- Direct termios-based UART control
- Configurable baud rate and serial parameters
- Non-blocking read with EAGAIN handling
- Canonical mode with line-based input
- Custom timeout and retry logic
- Raw output mode

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)

Setup for Loopback Test:
    Connect the following pins on the E2 connector:
    - TX (ttyPS1) to RX with a jumper wire for loopback testing
    
    Or connect to external UART device:
    - Red Pitaya TX -> External device RX
    - Red Pitaya RX -> External device TX
    - GND -> GND

Technical Details:
- UART Device: /dev/ttyPS1
- Default Baud Rate: 9600 bps
- Word Size: 8 bits
- Parity: None
- Stop Bits: 1
- Mode: Canonical (line-based input)
- Output: Raw mode

Supported Baud Rates:
    1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200, 230400,
    460800, 500000, 576000, 921600, 1000000, 1152000, 1500000,
    2000000, 2500000, 3000000, 3500000, 4000000

Software Requirements:
- Python 3 with termios module (standard library on Linux)
- Root or dialout group permissions

Usage:
    python uart_2_termios.py
    
    The program will:
    1. Initialize UART interface
    2. Write test message to UART TX
    3. Read data from UART RX (non-blocking with retry)
    4. Display received data
    5. Clean up resources

Note:
    This example uses low-level system calls and requires proper hardware
    connections. The read operation will retry until data is available.

Author: Red Pitaya
Date: May 2026
"""

import os
import termios
import fcntl
import time
import errno


# ==============================================================================
# UART CONFIGURATION
# ==============================================================================

# UART Device Configuration
UART_DEVICE = "/dev/ttyPS1"        # UART device path
BAUD_RATE = termios.B9600          # Baud rate (use termios.Bxxxx constants)
WORD_SIZE = termios.CS8            # Word size (CS5, CS6, CS7, CS8)
STOP_BITS = 1                      # Stop bits (1 or 2)
PARITY = None                      # Parity (None, Even, Odd)

# Test Data
TEST_MESSAGE = "HELLO WORLD!"      # Message to send via UART
READ_BUFFER_SIZE = 256             # Read buffer size
MAX_READ_RETRIES = 100             # Maximum read retry attempts
RETRY_DELAY = 0.1                  # Delay between retries (seconds)

# Baud rate mapping for display
BAUD_RATE_NAMES = {
    termios.B1200: 1200,
    termios.B2400: 2400,
    termios.B4800: 4800,
    termios.B9600: 9600,
    termios.B19200: 19200,
    termios.B38400: 38400,
    termios.B57600: 57600,
    termios.B115200: 115200,
    termios.B230400: 230400,
}

print("=" * 70)
print("Red Pitaya UART Low-Level Hardware API Configuration")
print("=" * 70)
print(f"UART Device:         {UART_DEVICE}")
print(f"Baud Rate:           {BAUD_RATE_NAMES.get(BAUD_RATE, 'Custom')} bps")
print("Word Size:           8 bits")
print("Parity:              None")
print(f"Stop Bits:           {STOP_BITS}")
print(f"Test Message:        \"{TEST_MESSAGE}\"")
print(f"Max Read Retries:    {MAX_READ_RETRIES}")
print("=" * 70)


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def uart_init():
    """
    Initialize UART interface with termios settings.
    
    Returns:
        int: File descriptor on success, -1 on error
    """
    try:
        # Open UART device
        uart_fd = os.open(UART_DEVICE, os.O_RDWR | os.O_NOCTTY | os.O_NDELAY)
        
        # Get current termios settings
        settings = termios.tcgetattr(uart_fd)
        
        # Set baud rate (input and output)
        settings[4] = BAUD_RATE   # ispeed
        settings[5] = BAUD_RATE   # ospeed
        
        # Configure control flags (c_cflag)
        settings[2] &= ~termios.PARENB  # No parity
        settings[2] &= ~termios.CSTOPB  # 1 stop bit
        settings[2] &= ~termios.CSIZE   # Clear size bits
        settings[2] |= WORD_SIZE | termios.CLOCAL  # 8 bits, ignore modem lines
        
        # Configure local flags (c_lflag)
        settings[3] = termios.ICANON    # Canonical mode (line-based input)
        
        # Configure output flags (c_oflag)
        settings[1] &= ~termios.OPOST   # Raw output
        
        # Flush and apply settings
        termios.tcflush(uart_fd, termios.TCIFLUSH)
        termios.tcsetattr(uart_fd, termios.TCSANOW, settings)
        
        return uart_fd
        
    except Exception as e:
        print(f"    ERROR: Failed to initialize UART - {e}")
        return -1


def uart_write(uart_fd, data):
    """
    Write data to UART TX.
    
    Args:
        uart_fd: File descriptor for UART device
        data: String to write
        
    Returns:
        int: 0 on success, -1 on error
    """
    try:
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        # Add newline character
        tx_buffer = data + b'\n'
        
        # Write to UART
        bytes_written = os.write(uart_fd, tx_buffer)
        
        if bytes_written < len(tx_buffer):
            print(f"    WARNING: Partial write - {bytes_written}/{len(tx_buffer)} bytes")
        
        return 0
        
    except Exception as e:
        print(f"    ERROR: UART TX failed - {e}")
        return -1


def uart_read(uart_fd, size):
    """
    Read data from UART RX with non-blocking retry logic.
    
    Args:
        uart_fd: File descriptor for UART device
        size: Maximum number of bytes to read
        
    Returns:
        bytes: Received data, or None on error
    """
    try:
        # Set non-blocking mode
        flags = fcntl.fcntl(uart_fd, fcntl.F_GETFL)
        fcntl.fcntl(uart_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
        
        retry_count = 0
        
        while retry_count < MAX_READ_RETRIES:
            try:
                # Try to read data
                rx_buffer = os.read(uart_fd, size)
                
                if len(rx_buffer) == 0:
                    # No data available yet
                    retry_count += 1
                    time.sleep(RETRY_DELAY)
                    continue
                else:
                    # Data received
                    return rx_buffer
                    
            except OSError as e:
                if e.errno == errno.EAGAIN or e.errno == errno.EWOULDBLOCK:
                    # No data yet available, retry
                    retry_count += 1
                    time.sleep(RETRY_DELAY)
                    continue
                else:
                    # Other error
                    print(f"    ERROR: Read error - {e}")
                    return None
        
        # Max retries reached
        print(f"    WARNING: No data received after {MAX_READ_RETRIES} retries")
        return b''
        
    except Exception as e:
        print(f"    ERROR: UART RX failed - {e}")
        return None


def uart_release(uart_fd):
    """
    Release UART resources and close device.
    
    Args:
        uart_fd: File descriptor for UART device
        
    Returns:
        int: 0 on success, -1 on error
    """
    try:
        termios.tcflush(uart_fd, termios.TCIFLUSH)
        os.close(uart_fd)
        return 0
    except Exception as e:
        print(f"    ERROR: Failed to release UART - {e}")
        return -1


# ==============================================================================
# MAIN PROGRAM
# ==============================================================================

def main():
    """Main program for low-level UART communication test."""
    
    uart_fd = -1
    
    try:
        # ===== STEP 1: Initialize UART =====
        print("\n[1] Initializing UART interface...")
        uart_fd = uart_init()
        if uart_fd < 0:
            print("    ERROR: UART initialization failed")
            return 1
        print(f"    UART device opened (fd: {uart_fd})")
        print(f"    Baud rate: {BAUD_RATE_NAMES.get(BAUD_RATE, 'Custom')} bps")
        
        # ===== STEP 2: Write Test Data =====
        print("\n[2] Writing test message to UART TX...")
        print(f"    Message: \"{TEST_MESSAGE}\"")
        if uart_write(uart_fd, TEST_MESSAGE) < 0:
            print("    ERROR: Write operation failed")
            return 1
        print(f"    {len(TEST_MESSAGE) + 1} bytes written (including newline)")
        
        # ===== STEP 3: Read Data from UART =====
        print("\n[3] Reading data from UART RX...")
        print(f"    Buffer size: {READ_BUFFER_SIZE} bytes")
        print(f"    Non-blocking mode with retry (max {MAX_READ_RETRIES} attempts)")
        
        rx_data = uart_read(uart_fd, READ_BUFFER_SIZE)
        
        if rx_data is None:
            print("    ERROR: Read operation failed")
            return 1
        
        if len(rx_data) == 0:
            print("    WARNING: No data received")
            print("    Check loopback connection (TX to RX)")
            return 1
        
        # ===== STEP 4: Display and Verify Data =====
        print("\n[4] Processing received data...")
        
        # Remove trailing newline/whitespace
        rx_string = rx_data.decode('utf-8', errors='ignore').strip()
        
        print(f"    Bytes received: {len(rx_data)}")
        print(f"    Received data: \"{rx_string}\"")
        
        # Verify data
        if rx_string == TEST_MESSAGE:
            print("    Data verification: MATCH")
            match = True
        else:
            print("    Data verification: MISMATCH")
            print(f"    Expected: \"{TEST_MESSAGE}\"")
            print(f"    Received: \"{rx_string}\"")
            match = False
        
        # ===== COMPLETION =====
        print("\n" + "=" * 70)
        if match:
            print("UART low-level test completed successfully")
        else:
            print("UART low-level test completed - Data verification failed")
        print("=" * 70)
        
        return 0 if match else 1
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    finally:
        # ===== CLEANUP =====
        if uart_fd >= 0:
            print("\n[Cleanup] Releasing UART resources...")
            uart_release(uart_fd)
            print("    UART device closed")


if __name__ == "__main__":
    exit(main())
