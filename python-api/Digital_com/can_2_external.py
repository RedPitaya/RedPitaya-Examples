#!/usr/bin/python3
"""
Red Pitaya Dual CAN Bus Communication Example
==============================================

This example demonstrates bidirectional CAN (Controller Area Network) bus 
communication between two CAN interfaces on Red Pitaya. The example shows how 
to configure and use both CAN0 and CAN1 simultaneously for inter-interface 
communication or connection to external CAN devices.

The example sends frames between CAN0 and CAN1 in both directions, demonstrating:
- Dual CAN interface initialization and configuration
- Synchronized bitrate configuration across interfaces
- Bidirectional frame transmission (CAN0 ↔ CAN1)
- Frame reception with detailed information
- Standard and extended frame support
- Timeout-based reception control
- CAN frame metadata extraction (ID, length, status)

Features:
- Dual CAN interface operation (CAN0 and CAN1)
- Configurable bitrate (1 bps to 10 Mbps) synchronized across both interfaces
- Multiple controller modes support
- Standard (11-bit) and extended (29-bit) CAN frame IDs
- Variable data length (up to 8 bytes per frame)
- RX timeout control for reliable reception
- Numpy array-based data buffers
- Detailed frame information display (CAN ID, data length, status)
- Bidirectional communication testing

Hardware Requirements:
- Red Pitaya board with dual CAN support (STEMlab 125-14 or similar)
- For external CAN: CAN transceivers connected to both CAN interfaces
- For direct connection: Wire CAN0 to CAN1 externally

CAN Interface Mapping:
    CAN0: DIO7_P (CAN0_H), DIO7_N (CAN0_L)
    CAN1: DIO6_P (CAN1_H), DIO6_N (CAN1_L)

Hardware Setup Options:
    
    Option 1 - Direct Interface Connection (Internal Test):
        Connect CAN0 to CAN1 directly:
        - Wire DIO7_P to DIO6_P (CAN_H to CAN_H)
        - Wire DIO7_N to DIO6_N (CAN_L to CAN_L)
        - Add 120Ω termination resistor at each end
        - Common ground
    
    Option 2 - External CAN Device:
        Connect each interface to separate external CAN transceivers:
        - CAN0: MCP2551 or similar transceiver on DIO7
        - CAN1: MCP2551 or similar transceiver on DIO6
        - Connect to external CAN bus network
        - Ensure proper 120Ω termination at bus ends
        - Common ground across all devices

Wiring for Direct Connection:
    Red Pitaya CAN0 to CAN1:
        DIO7_P (CAN0_H) ----[120Ω]---- DIO6_P (CAN1_H)
        DIO7_N (CAN0_L) ----[120Ω]---- DIO6_N (CAN1_L)
        GND ----------------- GND

Technical Details:
- CAN Interfaces: CAN0 (DIO7) and CAN1 (DIO6)
- Default Bitrate: 200 kbps (configurable 1 bps - 10 Mbps)
- Frame Types: Standard (11-bit ID) and Extended (29-bit ID)
- Data Length: Variable, up to 8 bytes per frame
- RX Timeout: 2000 ms (configurable, 0 = disabled)
- TX Timeout: Immediate (0 = no timeout)

Controller Modes:
- Normal Mode: Standard CAN communication with ACK
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
    python can_2_external.py
    
    The program will:
    1. Initialize FPGA and both CAN interfaces
    2. Configure CAN0 and CAN1 with identical bitrates
    3. Send frames from CAN0 to CAN1 (two frames with different IDs)
    4. Display received frame details
    5. Send frames from CAN1 to CAN0 (reverse direction)
    6. Display received frame details
    7. Close both interfaces

CAN Frame Information:
    rp_CanReadNP returns tuple: (status, can_id, data_length)
    - status: 0 = success, non-zero = error/timeout
    - can_id: CAN identifier of received frame
    - data_length: Number of data bytes in frame

Note:
    This example uses normal mode (loopback disabled) which requires proper 
    physical connection between CAN0 and CAN1 or external CAN devices.
    For testing without hardware, use loopback mode in can_1_loopback.py example.

Author: Red Pitaya
Date: January 2026
"""

import numpy as np
import rp
import rp_hw_can


# ==============================================================================
# CONFIGURATION - Set your dual CAN parameters here
# ==============================================================================

# CAN Interface Selection (both interfaces used)
can_interface_0 = rp_hw_can.RP_CAN_0        # CAN0: DIO7_P, DIO7_N
can_interface_1 = rp_hw_can.RP_CAN_1        # CAN1: DIO6_P, DIO6_N

# CAN Communication Parameters (synchronized across both interfaces)
can_bitrate = 200000                        # Bitrate in bps (1 - 10000000)
can_mode = rp_hw_can.RP_CAN_MODE_LOOPBACK   # Controller mode (set to normal for external)
use_loopback = False                        # Disable loopback for inter-interface communication

# CAN Frame Configuration
can_id_standard = 123                       # Standard frame CAN ID (11-bit)
can_id_extended = 321                       # Extended frame CAN ID (29-bit)

# Timeout Configuration (milliseconds, 0 = disabled)
can_rx_timeout = 2000                       # RX timeout (2 seconds)
can_tx_timeout = 0                          # TX timeout (immediate)

# Test Data Configuration
data_length_short = 3                       # Short frame: 3 bytes
data_length_full = 8                        # Full frame: 8 bytes
test_data = np.arange(8, dtype=np.uint8)    # Test pattern: [0,1,2,3,4,5,6,7]

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
print("Red Pitaya Dual CAN Bus Communication Configuration")
print("=" * 70)
print(f"CAN0 Interface:      {interface_names[can_interface_0]}")
print(f"CAN1 Interface:      {interface_names[can_interface_1]}")
print(f"Bitrate:             {can_bitrate / 1000:.1f} kbps")
print(f"Controller Mode:     {mode_names.get(can_mode, 'Unknown')}")
print(f"Loopback Enabled:    {use_loopback}")
print(f"Standard CAN ID:     {can_id_standard} (0x{can_id_standard:03X})")
print(f"Extended CAN ID:     {can_id_extended} (0x{can_id_extended:03X})")
print(f"RX Timeout:          {can_rx_timeout} ms")
print(f"TX Timeout:          {can_tx_timeout} ms {'(immediate)' if can_tx_timeout == 0 else ''}")
print(f"Test Data:           {list(test_data)}")
print(f"Short Frame Length:  {data_length_short} bytes")
print(f"Full Frame Length:   {data_length_full} bytes")
print("=" * 70)


# ==============================================================================
# MAIN PROGRAM
# ==============================================================================

def main():
    """Main program to perform dual CAN bus communication test."""
    
    try:
        # ===== STEP 1: Initialize Red Pitaya =====
        print("\n[1] Initializing Red Pitaya...")
        rp.rp_Init()
        print("    Red Pitaya initialized")
        
        # ===== STEP 2: Initialize CAN in FPGA =====
        print("\n[2] Initializing CAN in FPGA...")
        rp_hw_can.rp_CanSetFPGAEnable(True)
        print("    CAN FPGA interface enabled")
        print("    CAN data routing: Controllers -> GPIO pins")
        
        # ===== STEP 3: Configure CAN0 Interface =====
        print(f"\n[3] Configuring {interface_names[can_interface_0]}...")
        
        # Stop CAN0 for configuration
        rp_hw_can.rp_CanStop(can_interface_0)
        print("    CAN0 interface stopped for configuration")
        
        # Set CAN0 bitrate
        rp_hw_can.rp_CanSetBitrate(can_interface_0, can_bitrate)
        print(f"    Bitrate set: {can_bitrate / 1000:.1f} kbps")
        
        # Set CAN0 controller mode
        rp_hw_can.rp_CanSetControllerMode(can_interface_0, can_mode, use_loopback)
        print(f"    Controller mode: {mode_names.get(can_mode, 'Unknown')}")
        print(f"    Loopback: {'Enabled' if use_loopback else 'Disabled'}")
        
        # ===== STEP 4: Configure CAN1 Interface =====
        print(f"\n[4] Configuring {interface_names[can_interface_1]}...")
        
        # Stop CAN1 for configuration
        rp_hw_can.rp_CanStop(can_interface_1)
        print("    CAN1 interface stopped for configuration")
        
        # Set CAN1 bitrate (same as CAN0)
        rp_hw_can.rp_CanSetBitrate(can_interface_1, can_bitrate)
        print(f"    Bitrate set: {can_bitrate / 1000:.1f} kbps")
        
        # Set CAN1 controller mode (same as CAN0)
        rp_hw_can.rp_CanSetControllerMode(can_interface_1, can_mode, use_loopback)
        print(f"    Controller mode: {mode_names.get(can_mode, 'Unknown')}")
        print(f"    Loopback: {'Enabled' if use_loopback else 'Disabled'}")
        
        # ===== STEP 5: Start Both CAN Interfaces =====
        print("\n[5] Starting CAN interfaces...")
        
        # Start and open CAN0
        rp_hw_can.rp_CanStart(can_interface_0)
        rp_hw_can.rp_CanOpen(can_interface_0)
        print("    CAN0 started and socket opened")
        
        # Start and open CAN1
        rp_hw_can.rp_CanStart(can_interface_1)
        rp_hw_can.rp_CanOpen(can_interface_1)
        print("    CAN1 started and socket opened")
        print("    Both CAN interfaces ready for communication")
        
        # ===== STEP 6: Transmission CAN0 -> CAN1 =====
        print("\n[6] Transmitting frames: CAN0 -> CAN1...")
        print(f"    Test data: {list(test_data)}")
        
        # Send first frame (standard ID, 3 bytes)
        print(f"\n    Frame 1: Standard ID={can_id_standard} (0x{can_id_standard:03X}), {data_length_short} bytes")
        tx_result = rp_hw_can.rp_CanSendNP(
            can_interface_0,
            can_id_standard,
            False,  # Standard frame
            False,  # Not RTR
            can_tx_timeout,
            test_data[0:data_length_short]
        )
        print(f"    TX Result: {tx_result}")
        
        # Send second frame (extended ID, 8 bytes)
        print(f"\n    Frame 2: Extended ID={can_id_extended} (0x{can_id_extended:08X}), {data_length_full} bytes")
        tx_result = rp_hw_can.rp_CanSendNP(
            can_interface_0,
            can_id_extended,
            True,   # Extended frame
            False,  # Not RTR
            can_tx_timeout,
            test_data
        )
        print(f"    TX Result: {tx_result}")
        
        # ===== STEP 7: Reception at CAN1 =====
        print("\n[7] Receiving frames at CAN1...")
        
        # Receive first frame
        rx_buffer = np.zeros(8, dtype=np.uint8)
        can_info = rp_hw_can.rp_CanReadNP(can_interface_1, can_rx_timeout, rx_buffer)
        status, rx_can_id, rx_data_len = can_info
        
        print(f"\n    Frame 1 received:")
        print(f"        Status:      {status} ({'OK' if status == 0 else 'ERROR'})")
        print(f"        CAN ID:      {rx_can_id} (0x{rx_can_id:X})")
        print(f"        Data Length: {rx_data_len} bytes")
        print(f"        Data:        {list(rx_buffer[:rx_data_len])}")
        
        # Receive second frame
        rx_buffer = np.zeros(8, dtype=np.uint8)
        can_info = rp_hw_can.rp_CanReadNP(can_interface_1, can_rx_timeout, rx_buffer)
        status, rx_can_id, rx_data_len = can_info
        
        print(f"\n    Frame 2 received:")
        print(f"        Status:      {status} ({'OK' if status == 0 else 'ERROR'})")
        print(f"        CAN ID:      {rx_can_id} (0x{rx_can_id:X})")
        print(f"        Data Length: {rx_data_len} bytes")
        print(f"        Data:        {list(rx_buffer[:rx_data_len])}")
        
        # ===== STEP 8: Transmission CAN1 -> CAN0 =====
        print("\n[8] Transmitting frames: CAN1 -> CAN0...")
        print(f"    Test data: {list(test_data)}")
        
        # Send first frame (standard ID, 3 bytes)
        print(f"\n    Frame 1: Standard ID={can_id_standard} (0x{can_id_standard:03X}), {data_length_short} bytes")
        tx_result = rp_hw_can.rp_CanSendNP(
            can_interface_1,
            can_id_standard,
            False,  # Standard frame
            False,  # Not RTR
            can_tx_timeout,
            test_data[0:data_length_short]
        )
        print(f"    TX Result: {tx_result}")
        
        # Send second frame (extended ID, 8 bytes)
        print(f"\n    Frame 2: Extended ID={can_id_extended} (0x{can_id_extended:08X}), {data_length_full} bytes")
        tx_result = rp_hw_can.rp_CanSendNP(
            can_interface_1,
            can_id_extended,
            True,   # Extended frame
            False,  # Not RTR
            can_tx_timeout,
            test_data
        )
        print(f"    TX Result: {tx_result}")
        
        # ===== STEP 9: Reception at CAN0 =====
        print("\n[9] Receiving frames at CAN0...")
        
        # Receive first frame
        rx_buffer = np.zeros(8, dtype=np.uint8)
        can_info = rp_hw_can.rp_CanReadNP(can_interface_0, can_rx_timeout, rx_buffer)
        status, rx_can_id, rx_data_len = can_info
        
        print(f"\n    Frame 1 received:")
        print(f"        Status:      {status} ({'OK' if status == 0 else 'ERROR'})")
        print(f"        CAN ID:      {rx_can_id} (0x{rx_can_id:X})")
        print(f"        Data Length: {rx_data_len} bytes")
        print(f"        Data:        {list(rx_buffer[:rx_data_len])}")
        
        # Receive second frame
        rx_buffer = np.zeros(8, dtype=np.uint8)
        can_info = rp_hw_can.rp_CanReadNP(can_interface_0, can_rx_timeout, rx_buffer)
        status, rx_can_id, rx_data_len = can_info
        
        print(f"\n    Frame 2 received:")
        print(f"        Status:      {status} ({'OK' if status == 0 else 'ERROR'})")
        print(f"        CAN ID:      {rx_can_id} (0x{rx_can_id:X})")
        print(f"        Data Length: {rx_data_len} bytes")
        print(f"        Data:        {list(rx_buffer[:rx_data_len])}")
        
        # ===== STEP 10: Close CAN Interfaces =====
        print("\n[10] Closing CAN interfaces...")
        rp_hw_can.rp_CanClose(can_interface_0)
        print("    CAN0 socket closed")
        rp_hw_can.rp_CanClose(can_interface_1)
        print("    CAN1 socket closed")
        
        # ===== COMPLETION =====
        print("\n" + "=" * 70)
        print("Dual CAN bus communication test completed successfully")
        print("=" * 70)
        
        return 0
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        
        # Attempt cleanup
        try:
            rp_hw_can.rp_CanClose(can_interface_0)
            rp_hw_can.rp_CanClose(can_interface_1)
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

print("End Program")
rp.rp_Release()
