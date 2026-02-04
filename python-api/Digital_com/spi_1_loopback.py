#!/usr/bin/python3
"""
Red Pitaya SPI Loopback Test Example
=====================================

This example demonstrates SPI communication on Red Pitaya using loopback mode.
In loopback configuration, the MOSI (Master Out Slave In) pin is connected to
MISO (Master In Slave Out) pin, allowing transmitted data to be received back
for testing and verification.

The example sends two messages via SPI and reads them back, demonstrating:
- Multi-message SPI transmission
- Buffer management for TX and RX operations
- SPI configuration parameters (mode, speed, word size, bit order)
- Chip select control between messages

Features:
- SPI initialization and configuration
- Multiple message queue support
- TX and RX buffer management
- Loopback data verification
- Configurable SPI parameters (mode, speed, word size, bit order)
- Chip select mode control

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)

Setup for Loopback Test:
    Connect the following pins on the E2 connector:
    - MOSI (Pin X) to MISO (Pin Y) with a jumper wire
    
    Alternatively, connect to external SPI device:
    - MOSI -> Slave MOSI
    - MISO -> Slave MISO
    - SCLK -> Slave SCLK
    - CS   -> Slave CS

Technical Details:
- SPI Device: /dev/spidev1.0
- Default Speed: 50 MHz (adjustable 1 Hz - 100 MHz)
- Word Size: 8 bits (7 or 8 bits supported)
- SPI Modes: LISL, LIST, HISL, HIST
- Bit Order: MSB or LSB first
- CS Mode: Normal or High (active high)

SPI Modes:
- RP_SPI_MODE_LISL: Low idle, sample on leading edge
- RP_SPI_MODE_LIST: Low idle, sample on trailing edge
- RP_SPI_MODE_HISL: High idle, sample on leading edge
- RP_SPI_MODE_HIST: High idle, sample on trailing edge

Software Requirements:
- Red Pitaya hardware library (rp_hw module)

Usage:
    python spi_1_loopback.py
    
    The program will:
    1. Configure SPI interface
    2. Send two test messages
    3. Read back the data
    4. Display transmitted and received data

Note:
    Ensure proper loopback connection before running.
    Incorrect wiring may result in no data received.

Author: Red Pitaya
Date: January 2026
"""

import rp_hw


# ==============================================================================
# CONFIGURATION - Set your SPI parameters here
# ==============================================================================

# SPI Device Configuration
spi_device = "/dev/spidev1.0"              # SPI device path

# SPI Parameters
spi_mode = rp_hw.RP_SPI_MODE_LIST          # SPI mode (LISL, LIST, HISL, HIST)
spi_cs_mode = rp_hw.RP_SPI_CS_NORMAL       # Chip select mode (NORMAL, HIGH)
spi_speed = 50000000                       # SPI clock speed in Hz (1 - 100000000)
spi_word_size = 8                          # Word size in bits (7 or 8)
spi_bit_order = rp_hw.RP_SPI_ORDER_BIT_MSB # Bit order (MSB or LSB first)

# Test Data
test_message_1 = "TEST string"             # First message to send
test_message_2 = "Red Pitaya 123"          # Second message to send
toggle_cs_msg1 = False                     # Toggle CS after message 1
toggle_cs_msg2 = True                      # Toggle CS after message 2

# Get mode name for display
mode_names = {
    rp_hw.RP_SPI_MODE_LIST: "LIST (Low idle, sample trailing)",
    rp_hw.RP_SPI_MODE_LISL: "LISL (Low idle, sample leading)",
    rp_hw.RP_SPI_MODE_HISL: "HISL (High idle, sample leading)",
    rp_hw.RP_SPI_MODE_HIST: "HIST (High idle, sample trailing)"
}

print("=" * 70)
print("Red Pitaya SPI Loopback Test Configuration")
print("=" * 70)
print(f"SPI Device:          {spi_device}")
print(f"SPI Mode:            {mode_names.get(spi_mode, 'Unknown')}")
print(f"CS Mode:             {'Normal (Active Low)' if spi_cs_mode == rp_hw.RP_SPI_CS_NORMAL else 'High (Active High)'}")
print(f"Speed:               {spi_speed / 1000000:.1f} MHz")
print(f"Word Size:           {spi_word_size} bits")
print(f"Bit Order:           {'MSB first' if spi_bit_order == rp_hw.RP_SPI_ORDER_BIT_MSB else 'LSB first'}")
print(f"Message 1:           \"{test_message_1}\"")
print(f"Message 2:           \"{test_message_2}\"")
print("=" * 70)


# ==============================================================================
# MAIN PROGRAM
# ==============================================================================

def main():
    """Main program to perform SPI loopback test."""
    
    try:
        # Prepare test data
        data_int_1 = [ord(char) for char in test_message_1]
        data_size_1 = len(data_int_1)
        data_int_2 = [ord(char) for char in test_message_2]
        data_size_2 = len(data_int_2)
        
        # ===== STEP 1: Initialize SPI =====
        print("\n[1] Initializing SPI interface...")
        rp_hw.rp_SPI_Init()
        print("    SPI interface initialized")
        
        # ===== STEP 2: Configure SPI Device =====
        print(f"\n[2] Configuring SPI device ({spi_device})...")
        rp_hw.rp_SPI_InitDevice(spi_device)
        print("    Device initialized")
        
        # ===== STEP 3: Set SPI Parameters =====
        print("\n[3] Setting SPI parameters...")
        rp_hw.rp_SPI_SetMode(spi_mode)
        print(f"    Mode set: {mode_names.get(spi_mode, 'Unknown')}")
        
        rp_hw.rp_SPI_SetCSMode(spi_cs_mode)
        print(f"    CS mode: {'Normal' if spi_cs_mode == rp_hw.RP_SPI_CS_NORMAL else 'High'}")
        
        rp_hw.rp_SPI_SetSpeed(spi_speed)
        print(f"    Speed: {spi_speed / 1000000:.1f} MHz")
        
        rp_hw.rp_SPI_SetWordLen(spi_word_size)
        print(f"    Word size: {spi_word_size} bits")
        
        rp_hw.rp_SPI_SetOrderBit(spi_bit_order)
        print(f"    Bit order: {'MSB first' if spi_bit_order == rp_hw.RP_SPI_ORDER_BIT_MSB else 'LSB first'}")
        
        # ===== STEP 4: Apply Settings =====
        print("\n[4] Applying SPI settings...")
        rp_hw.rp_SPI_SetSettings()
        print("    Settings applied successfully")
        
        # ===== STEP 5: Create Message Queue =====
        print("\n[5] Creating message queue...")
        msg_count = 2
        rp_hw.rp_SPI_CreateMessage(msg_count)
        print(f"    Message queue created ({msg_count} messages)")
        
        # ===== STEP 6: Prepare TX Buffers =====
        print("\n[6] Preparing transmit buffers...")
        
        # Prepare first message buffer
        tx_buff_1 = rp_hw.Buffer(data_size_1)
        for i in range(data_size_1):
            tx_buff_1[i] = data_int_1[i]
        print(f"    TX Buffer 1: {data_size_1} bytes - \"{test_message_1}\"")
        
        # Prepare second message buffer
        tx_buff_2 = rp_hw.Buffer(data_size_2)
        for i in range(data_size_2):
            tx_buff_2[i] = data_int_2[i]
        print(f"    TX Buffer 2: {data_size_2} bytes - \"{test_message_2}\"")
        
        # ===== STEP 7: Configure Messages =====
        print("\n[7] Configuring SPI messages...")
        
        # Configure message 0
        rp_hw.rp_SPI_SetBufferForMessage(0, tx_buff_1, True, data_size_1, toggle_cs_msg1)
        print(f"    Message 0: {data_size_1} bytes, Toggle CS: {toggle_cs_msg1}")
        
        # Configure message 1
        rp_hw.rp_SPI_SetBufferForMessage(1, tx_buff_2, True, data_size_2, toggle_cs_msg2)
        print(f"    Message 1: {data_size_2} bytes, Toggle CS: {toggle_cs_msg2}")
        
        # ===== STEP 8: Execute SPI Transfer =====
        print("\n[8] Executing SPI read/write operation...")
        rp_hw.rp_SPI_ReadWrite()
        print("    Transfer complete")
        
        # ===== STEP 9: Read RX Buffers =====
        print("\n[9] Reading received data...")
        
        # Read RX buffer 0
        res_0 = rp_hw.rp_SPI_GetRxBuffer(0)
        rx_buff_0 = rp_hw.Buffer_frompointer(res_0[1])
        data_rx_0 = ''.join([chr(rx_buff_0[i]) for i in range(res_0[2])])
        print(f"    RX Buffer 0: \"{data_rx_0}\"")
        
        # Read RX buffer 1
        res_1 = rp_hw.rp_SPI_GetRxBuffer(1)
        rx_buff_1 = rp_hw.Buffer_frompointer(res_1[1])
        data_rx_1 = ''.join([chr(rx_buff_1[i]) for i in range(res_1[2])])
        print(f"    RX Buffer 1: \"{data_rx_1}\"")
        
        # ===== STEP 10: Verify Data =====
        print("\n[10] Verifying loopback data...")
        
        match_1 = data_rx_0 == test_message_1
        match_2 = data_rx_1 == test_message_2
        
        print(f"    Message 1: {'MATCH' if match_1 else 'MISMATCH'}")
        if not match_1:
            print(f"        Expected: \"{test_message_1}\"")
            print(f"        Received: \"{data_rx_0}\"")
        
        print(f"    Message 2: {'MATCH' if match_2 else 'MISMATCH'}")
        if not match_2:
            print(f"        Expected: \"{test_message_2}\"")
            print(f"        Received: \"{data_rx_1}\"")
        
        # ===== STEP 11: Cleanup =====
        print("\n[11] Cleaning up resources...")
        rp_hw.rp_SPI_DestoryMessage()
        print("    Messages destroyed")
        
        rp_hw.rp_SPI_Release()
        print("    SPI resources released")
        
        # ===== COMPLETION =====
        print("\n" + "=" * 70)
        if match_1 and match_2:
            print("SPI loopback test completed successfully - All data verified")
        else:
            print("SPI loopback test completed - Data verification failed")
            print("Check loopback connection (MOSI to MISO)")
        print("=" * 70)
        
        return 0 if (match_1 and match_2) else 1
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        
        # Attempt cleanup
        try:
            rp_hw.rp_SPI_DestoryMessage()
            rp_hw.rp_SPI_Release()
        except:
            pass
        
        return 1


if __name__ == "__main__":
    exit(main())
