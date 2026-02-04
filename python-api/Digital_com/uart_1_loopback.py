#!/usr/bin/python3
"""
Red Pitaya UART Loopback Test Example
======================================

This example demonstrates UART (Universal Asynchronous Receiver-Transmitter)
communication on Red Pitaya using loopback mode. In loopback configuration,
the TX (transmit) pin is connected to RX (receive) pin, allowing transmitted
data to be received back for testing and verification.

The example sends a test message via UART and reads it back in two parts,
demonstrating:
- UART initialization and configuration
- Configurable serial parameters (speed, word size, parity, stop bits)
- Timeout-based read operations
- Multi-part data reception
- Data verification

Features:
- UART initialization and configuration
- Configurable baud rate (1200 to 4 Mbps)
- Word size selection (6, 7, or 8 bits)
- Parity mode (None, Even, Odd, Mark, Space)
- Stop bits configuration (1 or 2 bits)
- Timeout control for read operations
- Buffer management for TX and RX

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)

Setup for Loopback Test:
    Connect the following pins on the E2 connector:
    - TX (Pin X) to RX (Pin Y) with a jumper wire
    
    Alternatively, connect to external UART device:
    - Red Pitaya TX -> External device RX
    - Red Pitaya RX -> External device TX
    - GND -> GND

Technical Details:
- Default Speed: 115200 baud
- Supported Speeds: 1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200,
                    230400, 576000, 921000, 1000000, 1152000, 1500000,
                    2000000, 2500000, 3000000, 3500000, 4000000
- Word Size: 6, 7, or 8 bits
- Parity: None, Even, Odd, Mark, Space
- Stop Bits: 1 or 2
- Timeout: 0-255 (in units of 1/10 second)

Software Requirements:
- Red Pitaya hardware library (rp_hw module)

Usage:
    python uart_1_loopback.py
    
    The program will:
    1. Configure UART interface
    2. Send test message
    3. Read back data in two parts (5 bytes, then remainder)
    4. Display received data and verify

Note:
    Ensure proper loopback connection before running.
    Incorrect wiring will result in no data received.

Author: Red Pitaya
Date: January 2026
"""

import rp_hw


# ==============================================================================
# CONFIGURATION - Set your UART parameters here
# ==============================================================================

# UART Communication Parameters
uart_speed = 115200                     # Baud rate in bps
uart_timeout = 10                       # Read timeout in 1/10 sec (10 = 1 sec)
uart_word_size = rp_hw.RP_UART_CS8      # Word size (CS6, CS7, CS8)
uart_parity = rp_hw.RP_UART_MARK        # Parity (NONE, EVEN, ODD, MARK, SPACE)
uart_stop_bits = rp_hw.RP_UART_STOP2    # Stop bits (STOP1, STOP2)

# Test Data
test_message = "TEST string"            # Message to send via UART
read_chunk_1_size = 5                   # Size of first read chunk (bytes)

# Get parameter names for display
word_size_names = {
    rp_hw.RP_UART_CS6: "6 bits",
    rp_hw.RP_UART_CS7: "7 bits",
    rp_hw.RP_UART_CS8: "8 bits"
}

parity_names = {
    rp_hw.RP_UART_NONE: "None",
    rp_hw.RP_UART_EVEN: "Even",
    rp_hw.RP_UART_ODD: "Odd",
    rp_hw.RP_UART_MARK: "Mark",
    rp_hw.RP_UART_SPACE: "Space"
}

stop_bits_names = {
    rp_hw.RP_UART_STOP1: "1 bit",
    rp_hw.RP_UART_STOP2: "2 bits"
}

print("=" * 70)
print("Red Pitaya UART Loopback Test Configuration")
print("=" * 70)
print(f"Baud Rate:           {uart_speed} bps")
print(f"Timeout:             {uart_timeout / 10:.1f} seconds")
print(f"Word Size:           {word_size_names.get(uart_word_size, 'Unknown')}")
print(f"Parity:              {parity_names.get(uart_parity, 'Unknown')}")
print(f"Stop Bits:           {stop_bits_names.get(uart_stop_bits, 'Unknown')}")
print(f"Test Message:        \"{test_message}\"")
print(f"Message Length:      {len(test_message)} bytes")
print(f"Read Strategy:       First {read_chunk_1_size} bytes, then remainder")
print("=" * 70)


# ==============================================================================
# MAIN PROGRAM
# ==============================================================================

def main():
    """Main program to perform UART loopback test."""
    
    try:
        # Prepare test data
        data_int = [ord(char) for char in test_message]
        data_size = len(data_int)
        
        # ===== STEP 1: Initialize UART =====
        print("\n[1] Initializing UART interface...")
        rp_hw.rp_UartInit()
        print("    UART interface initialized")
        
        # ===== STEP 2: Configure UART Parameters =====
        print("\n[2] Configuring UART parameters...")
        
        rp_hw.rp_UartSetTimeout(uart_timeout)
        print(f"    Timeout: {uart_timeout / 10:.1f} seconds")
        
        rp_hw.rp_UartSetSpeed(uart_speed)
        print(f"    Baud rate: {uart_speed} bps")
        
        rp_hw.rp_UartSetBits(uart_word_size)
        print(f"    Word size: {word_size_names.get(uart_word_size, 'Unknown')}")
        
        rp_hw.rp_UartSetStopBits(uart_stop_bits)
        print(f"    Stop bits: {stop_bits_names.get(uart_stop_bits, 'Unknown')}")
        
        rp_hw.rp_UartSetParityMode(uart_parity)
        print(f"    Parity: {parity_names.get(uart_parity, 'Unknown')}")
        
        # ===== STEP 3: Apply Settings =====
        print("\n[3] Applying UART settings...")
        rp_hw.rp_UartSetSettings()
        print("    Settings applied successfully")
        
        # ===== STEP 4: Prepare TX Buffer =====
        print("\n[4] Preparing transmit buffer...")
        tx_buff = rp_hw.Buffer(data_size)
        for i in range(data_size):
            tx_buff[i] = data_int[i]
        print(f"    TX Buffer: {data_size} bytes - \"{test_message}\"")
        
        # ===== STEP 5: Prepare RX Buffer =====
        print("\n[5] Preparing receive buffer...")
        rx_buff = rp_hw.Buffer(data_size)
        print(f"    RX Buffer: {data_size} bytes allocated")
        
        # ===== STEP 6: Write Data to UART =====
        print("\n[6] Transmitting data via UART...")
        rp_hw.rp_UartWrite(tx_buff, data_size)
        print(f"    {data_size} bytes transmitted")
        
        # ===== STEP 7: Read First Chunk =====
        print(f"\n[7] Reading first {read_chunk_1_size} bytes...")
        res_1 = rp_hw.rp_UartRead(rx_buff, read_chunk_1_size)
        result_code_1 = res_1[0]
        bytes_read_1 = res_1[1]
        
        print(f"    Result code: {result_code_1}")
        print(f"    Bytes read: {bytes_read_1}")
        
        if bytes_read_1 > 0:
            data_chunk_1 = ''.join([chr(rx_buff[i]) for i in range(bytes_read_1)])
            print(f"    Data: \"{data_chunk_1}\"")
        else:
            data_chunk_1 = ""
            print("    WARNING: No data received")
        
        # ===== STEP 8: Read Remaining Data =====
        remaining_bytes = data_size - read_chunk_1_size
        print(f"\n[8] Reading remaining {remaining_bytes} bytes...")
        res_2 = rp_hw.rp_UartRead(rx_buff, remaining_bytes)
        result_code_2 = res_2[0]
        bytes_read_2 = res_2[1]
        
        print(f"    Result code: {result_code_2}")
        print(f"    Bytes read: {bytes_read_2}")
        
        if bytes_read_2 > 0:
            data_chunk_2 = ''.join([chr(rx_buff[i]) for i in range(bytes_read_2)])
            print(f"    Data: \"{data_chunk_2}\"")
        else:
            data_chunk_2 = ""
            print("    WARNING: No data received")
        
        # ===== STEP 9: Verify Data =====
        print("\n[9] Verifying loopback data...")
        received_data = data_chunk_1 + data_chunk_2
        total_bytes_read = bytes_read_1 + bytes_read_2
        
        print(f"    Total bytes received: {total_bytes_read}/{data_size}")
        print(f"    Received data: \"{received_data}\"")
        
        if received_data == test_message:
            print("    Data verification: MATCH")
            match = True
        else:
            print("    Data verification: MISMATCH")
            print(f"    Expected: \"{test_message}\"")
            print(f"    Received: \"{received_data}\"")
            match = False
        
        # ===== STEP 10: Cleanup =====
        print("\n[10] Cleaning up resources...")
        rp_hw.rp_UartRelease()
        print("    UART resources released")
        
        # ===== COMPLETION =====
        print("\n" + "=" * 70)
        if match:
            print("UART loopback test completed successfully - All data verified")
        else:
            print("UART loopback test completed - Data verification failed")
            print("Check loopback connection (TX to RX)")
        print("=" * 70)
        
        return 0 if match else 1
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        
        # Attempt cleanup
        try:
            rp_hw.rp_UartRelease()
        except:
            pass
        
        return 1


if __name__ == "__main__":
    exit(main())
