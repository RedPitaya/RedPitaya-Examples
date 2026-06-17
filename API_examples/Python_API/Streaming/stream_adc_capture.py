#!/usr/bin/python3
"""
Red Pitaya ADC Streaming - Single Board Capture

Captures ADC data from a single Red Pitaya board. Data from both channels
is collected simultaneously into pre-allocated numpy arrays and basic
statistics are printed once the capture is complete.

Mode: Network streaming (NET)
Channels: 2
"""

import streaming
import numpy as np


# ==============================================================================
# CALLBACK CLASS - Handles incoming data packets from the streaming server
# ==============================================================================

class Callback(streaming.ADCCallback):
    """
    Custom callback handler for processing streaming ADC data.
    
    This class receives data packets from the Red Pitaya streaming server and stores them
    in pre-allocated numpy arrays for efficient memory usage.
    """
    
    def __init__(self, max_samples_per_channel=25_000_000):
        """
        Initialize the callback with pre-allocated data buffers.
        
        Args:
            max_samples_per_channel: Maximum number of samples to collect per channel
        """
        streaming.ADCCallback.__init__(self)
        
        # Sample counters
        self.counter = 0              # Total samples received
        self.fpgaLost = 0             # Number of samples lost by FPGA
        self.stop_requested = False   # Flag to prevent duplicate stop requests
        
        # Pre-allocate numpy arrays for data storage (int16 format, 2 bytes per sample)
        self.max_samples = max_samples_per_channel
        self.ch1_data = np.empty(max_samples_per_channel, dtype=np.int16)
        self.ch2_data = np.empty(max_samples_per_channel, dtype=np.int16)
        self.ch1_idx = 0  # Current write position for channel 1
        self.ch2_idx = 0  # Current write position for channel 2
        
        print(f"Pre-allocated {max_samples_per_channel * 2 * 2 / (1024*1024):.1f} MB for data buffers")

    def receivePack(self, client, n):
        """
        Called automatically when a data packet arrives from the streaming server.
        
        Args:
            client: The streaming client instance
            n: Data packet containing samples from all channels
        """
        # Ignore packets that arrive after stop is requested (in-flight packets)
        if self.stop_requested:
            return
        
        # Update statistics
        self.counter += n.channel1.samples + n.channel2.samples
        self.fpgaLost += max([n.channel1.fpgaLost, n.channel2.fpgaLost, 
                              n.channel3.fpgaLost, n.channel4.fpgaLost])
        
        # Process Channel 1 data
        if n.channel1.samples > 0 and self.ch1_idx < self.max_samples:
            # Convert SWIG vector to numpy array efficiently
            packet_data = np.array(n.channel1.raw, dtype=np.int16)
            samples_to_copy = min(len(packet_data), self.max_samples - self.ch1_idx)
            self.ch1_data[self.ch1_idx:self.ch1_idx + samples_to_copy] = packet_data[:samples_to_copy]
            self.ch1_idx += samples_to_copy
        
        # Process Channel 2 data
        if n.channel2.samples > 0 and self.ch2_idx < self.max_samples:
            # Convert SWIG vector to numpy array efficiently
            packet_data = np.array(n.channel2.raw, dtype=np.int16)
            samples_to_copy = min(len(packet_data), self.max_samples - self.ch2_idx)
            self.ch2_data[self.ch2_idx:self.ch2_idx + samples_to_copy] = packet_data[:samples_to_copy]
            self.ch2_idx += samples_to_copy
        
        # Stop streaming when buffers are full
        if self.ch1_idx >= self.max_samples or self.ch2_idx >= self.max_samples:
            if not self.stop_requested:
                self.stop_requested = True
                print(f"Buffer full - stopping stream (CH1: {self.ch1_idx}, CH2: {self.ch2_idx} samples)")
                client.notifyStop()
    
    def get_data(self):
        """
        Returns the collected data arrays, trimmed to actual size.
        
        Returns:
            tuple: (channel1_data, channel2_data) as numpy arrays
        """
        return self.ch1_data[:self.ch1_idx], self.ch2_data[:self.ch2_idx]
    
    # Connection event handlers
    def connected(self, client, host):
        print(f"Connected to streaming server: {host}")

    def disconnected(self, client, host):
        print(f"Disconnected from server: {host}")

    def error(self, client, host, code):
        print(f"Client error on {host}, code: {code}")
    
    # Server stop event handlers
    def stopped(self, client, host, code):
        print(f"Server stopped: {host}")

    def stoppedNoActiveChannels(self, client, host):
        print(f"Server stopped: {host} - No active channels")

    def stoppedMemError(self, client, host):
        print(f"Server stopped: {host} - Memory error")

    def stoppedMemModify(self, client, host):
        print(f"Server stopped: {host} - Memory changed")

    def stoppedSDFull(self, client, host):
        print(f"Server stopped: {host} - SD card full")

    def stoppedSDDone(self, client, host):
        print(f"Server stopped: {host} - Data written to SD card")
    
    # Control connection handlers
    def configConnected(self, client, host):
        print(f"Control client connected: {host}")

    def configError(self, client, host, code):
        print(f"Control client error on {host}, code: {code}")

    def configErrorTimeout(self, client, host):
        print(f"Control client timeout on {host}")


# ==============================================================================
# CONFIG CHANNEL CALLBACK - Handles configuration events
# ==============================================================================

class ConfigCallback(streaming.ConfigCallback):
    """Handles configuration channel events from ConfigStreamClient."""

    def configConnected(self, client, host):
        print(f"Config client connected: {host}")

    def configError(self, client, host, code):
        print(f"Config client error on {host}, code: {code}")

    def configErrorTimeout(self, client, host):
        print(f"Config client timeout on {host}")


# ==============================================================================
# CONFIGURATION - Set your acquisition parameters here
# ==============================================================================

# ADC sampling configuration
decimation = 256                    # Decimation factor (1, 2, 4, 8, 16, 17, 18, ..., 65536)
sample_rate = 125e6 / decimation    # Red Pitaya ADC base rate is 125 MS/s
capture_duration = 1                # Duration to capture in seconds

# Network streaming configuration
block_size = 131072                 # Network packet size in bytes (range: 2048 to 2097152)
adc_size = 4 * 1024 * 1024          # Reserved memory for ADC streaming on Red Pitaya (4 MB)

# Channel configuration
ch1_state = 'ON'                    # Channel 1: 'ON' or 'OFF'
ch2_state = 'ON'                    # Channel 2: 'ON' or 'OFF'

# Calculate required buffer size
max_samples_per_channel = int(sample_rate * capture_duration)

# Ensure buffer is large enough for at least one network packet
samples_per_block = block_size // 2  # int16 = 2 bytes per sample
if max_samples_per_channel < samples_per_block:
    print(f"Warning: Calculated max_samples ({max_samples_per_channel}) is less than one buffer ({samples_per_block})")
    max_samples_per_channel = samples_per_block
    print(f"Adjusted max_samples to minimum buffer size: {max_samples_per_channel}")

print("=" * 70)
print("Red Pitaya ADC Streaming Configuration")
print("=" * 70)
print(f"Sample rate:     {sample_rate/1e6:.2f} MS/s (decimation: {decimation})")
print(f"Capture time:    {capture_duration} seconds")
print(f"Samples/channel: {max_samples_per_channel:,}")
print(f"Memory usage:    {max_samples_per_channel * 2 * 2 / (1024*1024):.1f} MB total")
print("=" * 70)


# ==============================================================================
# MAIN PROGRAM - Connect, configure, and start streaming
# ==============================================================================

# Step 1: Create streaming client and callback handler
confObj = streaming.ConfigStreamClient()
client = streaming.ADCStreamClient(confObj)
confCallback = ConfigCallback()
confObj.addCallback(confCallback)
callback = Callback(max_samples_per_channel=max_samples_per_channel)
client.setReceiveDataCallback(callback)
confObj.setVerbose(True)
client.setVerbose(False)

# Step 2: Connect to Red Pitaya streaming server
print("\nConnecting to Red Pitaya...")
if not confObj.connect():
    print("ERROR: Failed to connect to streaming server")
    print("Make sure Red Pitaya streaming app is running and the stream_app FPGA is loaded.")
    exit(1)

# Step 3: Configure streaming parameters
print("Configuring streaming parameters...")
current_decimation = confObj.getConfig('adc_decimation')
print(f"Current decimation: {current_decimation}")

confObj.sendConfig('adc_pass_mode', 'NET')              # Set network mode (NET or FILE for SD card)
confObj.sendConfig('adc_decimation', f'{decimation}')   # Set decimation factor
confObj.sendConfig('block_size', f'{block_size}')       # Set network packet size
confObj.sendConfig('adc_size', f'{adc_size}')           # Set FPGA buffer size
confObj.sendConfig('channel_state_1', f'{ch1_state}')   # Enable/disable channel 1
confObj.sendConfig('channel_state_2', f'{ch2_state}')   # Enable/disable channel 2

# Step 4: Start streaming
print("\nStarting data acquisition...")
if not client.startStreaming():
    print("ERROR: Failed to start streaming")
    exit(1)

print("Streaming started - collecting data...")

# Step 5: Wait for streaming to complete
client.wait()

# Step 6: Retrieve and display results
print("\n" + "=" * 70)
print("ACQUISITION COMPLETE")
print("=" * 70)
print(f"Total samples received: {callback.counter:,}")
print(f"Samples lost by FPGA:   {callback.fpgaLost:,}")

# Get the collected data
ch1_samples, ch2_samples = callback.get_data()

print(f"\nChannel 1: {len(ch1_samples):,} samples collected")
print(f"  Min: {ch1_samples.min():6d}  Max: {ch1_samples.max():6d}  Mean: {ch1_samples.mean():6.2f}")
print(f"  First 10 samples: {ch1_samples[:10]}")

print(f"\nChannel 2: {len(ch2_samples):,} samples collected")
print(f"  Min: {ch2_samples.min():6d}  Max: {ch2_samples.max():6d}  Mean: {ch2_samples.mean():6.2f}")
print(f"  First 10 samples: {ch2_samples[:10]}")

print("\n" + "=" * 70)
print("Data is now available in 'ch1_samples' and 'ch2_samples' numpy arrays")
print("You can now process, plot, or save the data as needed")
print("=" * 70)


