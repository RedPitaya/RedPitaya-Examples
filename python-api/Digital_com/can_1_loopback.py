#!/usr/bin/python3
"""
Red Pitaya CAN Bus Loopback Test Example
=========================================

This example demonstrates CAN (Controller Area Network) bus communication on
Red Pitaya using loopback mode. In loopback mode, transmitted messages are
immediately received back by the same interface, allowing testing and verification
without requiring external CAN devices.

The example sends a test frame via CAN and reads it back, demonstrating:
- CAN interface initialization and configuration
- Bitrate configuration (up to 10 Mbps)
- Controller mode selection (loopback, listen-only, etc.)
- Frame transmission with configurable parameters
- Frame reception with timeout control
- Extended frame and RTR support

Features:
- CAN interface initialization in FPGA
- Configurable bitrate (1 bps to 10 Mbps)
- Multiple controller modes (loopback, listen-only, one-shot, etc.)
- Standard and extended CAN frame support
- Remote Transmission Request (RTR) support
- TX/RX timeout control
- Numpy array-based data buffers
- Data verification

Hardware Requirements:
- Red Pitaya board with CAN support (STEMlab 125-14 or similar)
- For loopback: No external connections required
- For external CAN: CAN transceiver connected to DIO pins

CAN Interface Mapping:
    - RP_CAN_0: DIO7_P (CAN_H), DIO7_N (CAN_L)
    - RP_CAN_1: DIO6_P (CAN_H), DIO6_N (CAN_L)

Setup for Loopback Test:
    No external hardware required - loopback mode is internal
    
Setup for External CAN Device:
    Connect CAN transceiver to appropriate DIO pins:
    - CAN_H to external CAN_H
    - CAN_L to external CAN_L
    - Common ground
    - 120Ω termination resistors at each end of the bus

Technical Details:
- CAN Interface: CAN0 (DIO7) or CAN1 (DIO6)
- Default Bitrate: 200 kbps (configurable 1 bps - 10 Mbps)
- Frame Types: Standard (11-bit ID) or Extended (29-bit ID)
- Data Length: Up to 8 bytes per frame
- Timeout: Configurable TX/RX timeout (0 = disabled)

Controller Modes:
- RP_CAN_MODE_LOOPBACK: Internal loopback for testing
- RP_CAN_MODE_LISTENONLY: Listen only, no ACK
- RP_CAN_MODE_3_SAMPLES: Sample point three times
- RP_CAN_MODE_ONE_SHOT: Single transmission attempt
- RP_CAN_MODE_BERR_REPORTING: Report bus errors

Software Requirements:
- Red Pitaya API library (rp module)
- Red Pitaya CAN library (rp_hw_can module)
- NumPy library

Usage:
    python can_1_loopback.py
    
    The program will:
    1. Initialize FPGA and CAN interface
    2. Configure CAN parameters
    3. Send test frame
    4. Read back the frame
    5. Verify data and display results

Note:
    Loopback mode is for testing only. For actual CAN communication,
    use RP_CAN_MODE_LISTENONLY or normal mode with external devices.

Author: Red Pitaya
Date: January 2026
"""

import numpy as np
import rp
import rp_hw_can


# ==============================================================================
# CONFIGURATION - Set your CAN parameters here
# ==============================================================================

# CAN Interface Selection
can_interface = rp_hw_can.RP_CAN_0          # RP_CAN_0 (DIO7) or RP_CAN_1 (DIO6)

# CAN Communication Parameters
can_bitrate = 200000                        # Bitrate in bps (1 - 10000000)
can_mode = rp_hw_can.RP_CAN_MODE_LOOPBACK   # Controller mode

# CAN Frame Configuration
can_id = 123                                # CAN identifier (11-bit or 29-bit)
can_extended_frame = False                  # Extended frame (29-bit ID)
can_rtr = False                             # Remote Transmission Request

# Timeout Configuration (milliseconds, 0 = disabled)
can_tx_timeout = 0                          # TX timeout
can_rx_timeout = 0                          # RX timeout

# Test Data
data_length = 8                             # Number of bytes to send (max 8)
test_data = np.arange(data_length, dtype=np.uint8)  # Test pattern: [0,1,2,3,4,5,6,7]

# Interface name mapping
interface_names = {
    rp_hw_can.RP_CAN_0: "CAN0 (DIO7_P/DIO7_N)",
    rp_hw_can.RP_CAN_1: "CAN1 (DIO6_P/DIO6_N)"
}

# Mode name mapping
mode_names = {
    rp_hw_can.RP_CAN_MODE_LOOPBACK: "Loopback",
    rp_hw_can.RP_CAN_MODE_LISTENONLY: "Listen Only",
    rp_hw_can.RP_CAN_MODE_3_SAMPLES: "3 Samples",
    rp_hw_can.RP_CAN_MODE_ONE_SHOT: "One Shot",
    rp_hw_can.RP_CAN_MODE_BERR_REPORTING: "Bus Error Reporting"
}

print("=" * 70)
print("Red Pitaya CAN Bus Loopback Test Configuration")
print("=" * 70)
print(f"CAN Interface:       {interface_names.get(can_interface, 'Unknown')}")
print(f"Bitrate:             {can_bitrate / 1000:.1f} kbps")
print(f"Controller Mode:     {mode_names.get(can_mode, 'Unknown')}")
print(f"CAN ID:              {can_id} (0x{can_id:03X})")
print(f"Extended Frame:      {can_extended_frame}")
print(f"RTR Frame:           {can_rtr}")
print(f"TX Timeout:          {can_tx_timeout} ms {'(disabled)' if can_tx_timeout == 0 else ''}")
print(f"RX Timeout:          {can_rx_timeout} ms {'(disabled)' if can_rx_timeout == 0 else ''}")
print(f"Data Length:         {data_length} bytes")
print(f"Test Data:           {list(test_data)}")
print("=" * 70)


# ==============================================================================
# MAIN PROGRAM
# ==============================================================================

def main():
    """Main program to perform CAN loopback test."""
    
    try:
        # Prepare RX buffer
        rx_buffer = np.zeros(data_length, dtype=np.uint8)
        
        # ===== STEP 1: Initialize Red Pitaya =====
        print("\n[1] Initializing Red Pitaya...")
        rp.rp_Init()
        print("    Red Pitaya initialized")
        
        # ===== STEP 2: Initialize CAN in FPGA =====
        print("\n[2] Initializing CAN in FPGA...")
        rp_hw_can.rp_CanSetFPGAEnable(True)
        print("    CAN FPGA interface enabled")
        print("    CAN data routing: Controller -> GPIO pins")
        
        # ===== STEP 3: Configure CAN Interface =====
        print(f"\n[3] Configuring {interface_names.get(can_interface, 'CAN interface')}...")
        
        # Stop CAN for configuration
        rp_hw_can.rp_CanStop(can_interface)
        print("    CAN interface stopped for configuration")
        
        # Set bitrate
        rp_hw_can.rp_CanSetBitrate(can_interface, can_bitrate)
        print(f"    Bitrate set: {can_bitrate / 1000:.1f} kbps")
        
        # Set controller mode
        rp_hw_can.rp_CanSetControllerMode(can_interface, can_mode, True)
        print(f"    Controller mode: {mode_names.get(can_mode, 'Unknown')}")
        
        # ===== STEP 4: Start CAN Interface =====
        print("\n[4] Starting CAN interface...")
        rp_hw_can.rp_CanStart(can_interface)
        print("    CAN interface started (line UP)")
        
        # Open CAN socket
        rp_hw_can.rp_CanOpen(can_interface)
        print("    CAN socket opened")
        print("    CAN interface ready for communication")
        
        # ===== STEP 5: Send CAN Frame =====
        print("\n[5] Transmitting CAN frame...")
        print(f"    CAN ID: {can_id} (0x{can_id:03X})")
        print(f"    Data: {list(test_data)}")
        print(f"    Length: {data_length} bytes")
        
        tx_result = rp_hw_can.rp_CanSendNP(
            can_interface,
            can_id,
            can_extended_frame,
            can_rtr,
            can_tx_timeout,
            test_data
        )
        print(f"    TX Result: {tx_result}")
        
        if tx_result != 0:
            print("    WARNING: Transmission may have failed")
        else:
            print("    Frame transmitted successfully")
        
        # ===== STEP 6: Receive CAN Frame =====
        print("\n[6] Receiving CAN frame...")
        print(f"    Waiting for data (timeout: {can_rx_timeout} ms)...")
        
        rx_result = rp_hw_can.rp_CanReadNP(
            can_interface,
            can_rx_timeout,
            rx_buffer
        )
        print(f"    RX Result: {rx_result}")
        
        if rx_result != 0:
            print("    WARNING: Reception may have failed or timed out")
        else:
            print("    Frame received successfully")
        
        print(f"    Received data: {list(rx_buffer)}")
        
        # ===== STEP 7: Verify Data =====
        print("\n[7] Verifying loopback data...")
        
        if np.array_equal(test_data, rx_buffer):
            print("    Data verification: MATCH")
            print("    Loopback test successful")
            match = True
        else:
            print("    Data verification: MISMATCH")
            print(f"    Expected: {list(test_data)}")
            print(f"    Received: {list(rx_buffer)}")
            match = False
        
        # ===== STEP 8: Close CAN Interface =====
        print("\n[8] Closing CAN interface...")
        rp_hw_can.rp_CanClose(can_interface)
        print("    CAN socket closed")
        
        # ===== COMPLETION =====
        print("\n" + "=" * 70)
        if match:
            print("CAN loopback test completed successfully - All data verified")
        else:
            print("CAN loopback test completed - Data verification failed")
        print("=" * 70)
        
        return 0 if match else 1
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        
        # Attempt cleanup
        try:
            rp_hw_can.rp_CanClose(can_interface)
        except:
            pass
        
        return 1
        
    finally:
        # ===== CLEANUP =====
        print("\n[Cleanup] Releasing Red Pitaya resources...")
        try:
            rp.rp_Release()
            print("    Resources released")
        except:
            pass


if __name__ == "__main__":
    exit(main())
