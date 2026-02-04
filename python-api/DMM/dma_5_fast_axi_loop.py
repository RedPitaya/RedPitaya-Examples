#!/usr/bin/python3
"""
Red Pitaya Multi-Channel DMA Acquisition Example
=================================================

This example demonstrates high-speed data acquisition from multiple channels using DMA
(Direct Memory Access) on the Red Pitaya platform. The code is optimized for performance
with proper error handling and clean data processing.

Features:
- Multi-channel simultaneous acquisition (CH1 and CH2)
- DMA-based data transfer for high-speed operation
- External trigger support
- Continuous acquisition loop
- Efficient memory management and data processing

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)
- External trigger source connected to DIN0 (EXT_TRIG)

Software Requirements:
- Red Pitaya Python API (rp module)
- NumPy library

Usage:
    python FastAxiLoopAcq.py

Configuration:
    Modify the following parameters in the script:
    - DECIMATION: Decimation factor (1, 2, 4, 8, 16, or higher integers)
    - TRIGGER_LEVEL: Trigger level in volts
    - SAMPLES_PER_CHANNEL: Number of samples per channel
    - MAX_ITERATIONS: Number of acquisition loops

Note:
    The acquired_data variable is a placeholder for data that should be transmitted
    over Ethernet or processed further. Replace it with your actual data handling
    function (e.g., network transmission, file writing, or real-time processing).

Author: Red Pitaya
Date: January 2026
"""

import time
import numpy as np

try:
    import rp
except ImportError:
    print("Error: Red Pitaya API (rp) not found. Please ensure the code is executed on Red Pitaya hardware.")
    exit(1)

# Configuration
DEBUG = False  # Set to True for detailed debug output

# Channel configuration
CHANNEL_1 = rp.RP_CH_1
CHANNEL_2 = rp.RP_CH_2

#TODO : Add more channels if supported
channels = [CHANNEL_1, CHANNEL_2]  # Channels to acquire
num_channels = len(channels)

# Acquisition parameters
DECIMATION = 1                      # Decimation factor (1=125MHz, 2=62.5MHz, 4=31.25MHz, etc.)
TRIGGER_LEVEL = 0.2                 # Trigger level in volts
TRIGGER_DELAY = 0                   # Trigger delay in samples
SAMPLES_PER_CHANNEL = 5000          # Number of samples per channel (must be multiple of 8)
AXI_MIN_BLOCK_SIZE = 4096           # Minimum AXI block size (must be multiple of 4096)
MAX_ITERATIONS = 20                 # Number of acquisition loops

# Calculate AXI block size (rounded up to nearest multiple of AXI_MIN_BLOCK_SIZE)
axi_block_size = ((2 * SAMPLES_PER_CHANNEL + AXI_MIN_BLOCK_SIZE - 1) // AXI_MIN_BLOCK_SIZE) * AXI_MIN_BLOCK_SIZE
total_samples = SAMPLES_PER_CHANNEL * num_channels

# Pre-allocate data array for all channels
# This array holds the acquired data and can be replaced with network transmission or other processing
acquired_data = np.zeros((num_channels, SAMPLES_PER_CHANNEL), dtype=np.int16)

# Loop iteration counter
iteration_count = 0


def setup_red_pitaya():
    """
    Initialize and configure Red Pitaya for multi-channel acquisition.
    
    Returns:
        tuple: (dma_start_addr, dma_full_size) - DMA memory region information
        
    Raises:
        Exception: If initialization fails
    """
    try:
        rp.rp_Init()
        
        # Get DMA memory region information
        memory = rp.rp_AcqAxiGetMemoryRegion()
        dma_start_addr = memory[1]
        dma_full_size = memory[2]
        
        if DEBUG:
            print(f"DMA Memory Region: start=0x{dma_start_addr:X}, size={dma_full_size:,} bytes")
        
        return dma_start_addr, dma_full_size
    except Exception as e:
        print(f"Error initializing Red Pitaya: {e}")
        raise


def configure_acquisition(dma_start_addr):
    """
    Configure acquisition parameters for all channels.
    
    Args:
        dma_start_addr: Starting address of the DMA memory region
        
    Raises:
        Exception: If configuration fails
    """
    try:
        # Set decimation factor for acquisition
        rp.rp_AcqAxiSetDecimationFactor(DECIMATION)
        
        # Set trigger parameters (trigger on Channel 1)
        rp.rp_AcqSetTriggerLevel(rp.RP_T_CH_1, TRIGGER_LEVEL)

        if DEBUG:
            print(f"AXI block size: {axi_block_size:,} bytes")
            print(f"Decimation: {DECIMATION}, Trigger level: {TRIGGER_LEVEL}V")
        
        # Configure each channel with its own buffer region
        buffer_offset = dma_start_addr
        for i, channel in enumerate(channels):
            if DEBUG:
                print(f"CH{i+1}: buffer offset=0x{buffer_offset:X}, samples={SAMPLES_PER_CHANNEL}")

            rp.rp_AcqAxiSetTriggerDelay(channel, SAMPLES_PER_CHANNEL)
            rp.rp_AcqAxiSetBufferSamples(channel, buffer_offset, SAMPLES_PER_CHANNEL)
            rp.rp_AcqAxiEnable(channel, True)
            buffer_offset += axi_block_size
                
    except Exception as e:
        print(f"Error configuring acquisition: {e}")
        raise


def process_channel_data(memory_region, channel_idx):
    """
    Process data from a single channel memory region.
    
    Args:
        memory_region: Tuple containing (error_code, data_spans)
        channel_idx: Index of the channel being processed (0-based)
        
    Returns:
        numpy.ndarray: Processed channel data as int16 array
    """
    if memory_region[0] != 0:
        print(f"Error reading CH{channel_idx + 1} data: error code {memory_region[0]}")
        return np.zeros(SAMPLES_PER_CHANNEL, dtype=np.int16)
    
    # Combine all memory spans and convert to numpy array
    all_bytes = b''.join(span for span in memory_region[1])
    channel_data = np.frombuffer(all_bytes[:SAMPLES_PER_CHANNEL * 2], dtype=np.int16)
    
    # Pad with zeros if data is shorter than expected
    if len(channel_data) < SAMPLES_PER_CHANNEL:
        channel_data = np.pad(channel_data, (0, SAMPLES_PER_CHANNEL - len(channel_data)), 
                             constant_values=0)
    
    return channel_data


# Initialize Red Pitaya
dma_start_addr, dma_full_size = setup_red_pitaya()

# Configure acquisition
configure_acquisition(dma_start_addr)

# Main acquisition loop
print(f"Starting acquisition loop ({MAX_ITERATIONS} iterations)...")
print("Waiting for trigger on CHA positive edge...")
start_time = time.perf_counter()

try:
    while iteration_count < MAX_ITERATIONS:
        # Start acquisition and set trigger source
        rp.rp_AcqStart()
        rp.rp_AcqSetTriggerSrc(rp.RP_TRIG_SRC_CHA_PE)  # Trigger on CHA positive edge
        
        # Wait for trigger and buffer to fill
        # Note: This busy-wait loop is the primary bottleneck in acquisition speed
        while rp.rp_AcqAxiGetBufferFillState(rp.RP_CH_1)[1] == 0:
            pass
        
        # Stop acquisition after trigger is detected and buffer is filled
        rp.rp_AcqStop()

        # Get trigger positions for all channels
        trigger_positions = [rp.rp_AcqAxiGetWritePointerAtTrig(channel)[1] 
                           for channel in channels]
        if DEBUG:
            for i, pos in enumerate(trigger_positions):
                print(f"CH{i+1} trigger position: {pos}")

        # Read raw data from all channels
        memory_regions = [rp.rp_AcqAxiGetDataRawDirect(channel, trigger_positions[i], 
                                                       SAMPLES_PER_CHANNEL) 
                         for i, channel in enumerate(channels)]

        # Process and store data for all channels
        for i, memory_region in enumerate(memory_regions):
            acquired_data[i] = process_channel_data(memory_region, i)
        
        # TODO: Replace acquired_data with actual data transmission/processing
        # Example: send_via_ethernet(acquired_data) or save_to_file(acquired_data)
        
        iteration_count += 1
        
        # Progress update
        if iteration_count % 5 == 0 or iteration_count == MAX_ITERATIONS:
            elapsed_time = time.perf_counter() - start_time
            avg_time_per_iter = elapsed_time / iteration_count
            print(f"Progress: {iteration_count}/{MAX_ITERATIONS} iterations | "
                  f"Elapsed: {elapsed_time:.3f}s | Avg: {avg_time_per_iter:.4f}s/iter")

    # Display final summary
    total_time = time.perf_counter() - start_time
    print(f"\n{'='*60}")
    print(f"Acquisition completed successfully!")
    print(f"{'='*60}")
    print(f"Total iterations: {iteration_count}")
    print(f"Total time: {total_time:.3f} seconds")
    print(f"Average time per iteration: {total_time/iteration_count:.4f} seconds")
    print(f"\nData Summary (last acquisition):")
    for i in range(num_channels):
        data_range = f"[{acquired_data[i].min():,} to {acquired_data[i].max():,}]"
        print(f"  CH{i+1}: Range {data_range}")
        print(f"       First 10 samples: {acquired_data[i, :10]}")
        print(f"       Last 10 samples:  {acquired_data[i, -10:]}")

except KeyboardInterrupt:
    print("\n\nAcquisition interrupted by user")
except Exception as e:
    print(f"\nError during acquisition: {e}")
    import traceback
    traceback.print_exc()

finally:
    # Cleanup - disable all channels and release resources
    print("\nCleaning up...")
    try:
        for channel in channels:
            rp.rp_AcqAxiEnable(channel, False)
        rp.rp_Release()
        print("Cleanup completed successfully")
    except Exception as e:
        print(f"Error during cleanup: {e}")


