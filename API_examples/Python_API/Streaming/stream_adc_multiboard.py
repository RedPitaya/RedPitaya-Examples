#!/usr/bin/python3
"""
Red Pitaya ADC Streaming - Multi-Board Synchronized Capture

Captures ADC data from multiple Red Pitaya boards simultaneously in a
master/slave configuration. Each board collects data from two channels
into separate per-host numpy arrays.

Mode: Network streaming (NET)
Channels: 2 per board
Topology: 1 master + N slaves
"""

import streaming
import numpy as np


# ==============================================================================
# CALLBACK CLASS - Handles incoming data packets from multiple streaming servers
# ==============================================================================

class Callback(streaming.ADCCallback):
    """
    Custom callback handler for processing streaming ADC data from multiple boards.
    
    This class receives data packets from multiple Red Pitaya streaming servers and stores them
    in pre-allocated numpy arrays per host for efficient memory usage.
    """
    
    def __init__(self, hosts, max_samples_per_channel=25_000_000):
        """
        Initialize the callback with pre-allocated data buffers for each host.
        
        Args:
            hosts: List of host addresses to monitor
            max_samples_per_channel: Maximum number of samples to collect per channel per host
        """
        streaming.ADCCallback.__init__(self)
        
        # Sample counters per host
        self.counter = {}           # Total samples received per host
        self.fpgaLost = {}          # Number of samples lost by FPGA per host
        self.stop_requested = {}    # Flag to prevent duplicate stop requests per host
        
        # Pre-allocate numpy arrays for data storage (int16 format, 2 bytes per sample)
        self.max_samples = max_samples_per_channel
        self.ch1_data = {}   # Channel 1 data per host
        self.ch2_data = {}   # Channel 2 data per host
        self.ch1_idx = {}    # Current write position for channel 1 per host
        self.ch2_idx = {}    # Current write position for channel 2 per host
        
        # Initialize storage for each host
        for host in hosts:
            self.counter[host] = 0
            self.fpgaLost[host] = 0
            self.stop_requested[host] = False
            self.ch1_data[host] = np.empty(max_samples_per_channel, dtype=np.int16)
            self.ch2_data[host] = np.empty(max_samples_per_channel, dtype=np.int16)
            self.ch1_idx[host] = 0
            self.ch2_idx[host] = 0
        
        memory_per_board = max_samples_per_channel * 2 * 2 / (1024*1024)
        total_memory = memory_per_board * len(hosts)
        print(f"Pre-allocated {memory_per_board:.1f} MB per board (x{len(hosts)} boards = {total_memory:.1f} MB total)")

    def receivePack(self, client, pack):
        """
        Called automatically when a data packet arrives from the streaming server.
        
        Args:
            client: The streaming client instance
            pack: Data packet containing samples from all channels and host information
        """
        host = pack.host
        
        # Ignore packets that arrive after stop is requested (in-flight packets)
        if self.stop_requested.get(host, False):
            return
        
        # Update statistics
        self.counter[host] += pack.channel1.samples + pack.channel2.samples
        self.fpgaLost[host] += max([pack.channel1.fpgaLost, pack.channel2.fpgaLost, 
                                    pack.channel3.fpgaLost, pack.channel4.fpgaLost])
        
        # Process Channel 1 data
        if pack.channel1.samples > 0 and self.ch1_idx[host] < self.max_samples:
            # Convert SWIG vector to numpy array efficiently
            packet_data = np.array(pack.channel1.raw, dtype=np.int16)
            samples_to_copy = min(len(packet_data), self.max_samples - self.ch1_idx[host])
            self.ch1_data[host][self.ch1_idx[host]:self.ch1_idx[host] + samples_to_copy] = packet_data[:samples_to_copy]
            self.ch1_idx[host] += samples_to_copy
        
        # Process Channel 2 data
        if pack.channel2.samples > 0 and self.ch2_idx[host] < self.max_samples:
            # Convert SWIG vector to numpy array efficiently
            packet_data = np.array(pack.channel2.raw, dtype=np.int16)
            samples_to_copy = min(len(packet_data), self.max_samples - self.ch2_idx[host])
            self.ch2_data[host][self.ch2_idx[host]:self.ch2_idx[host] + samples_to_copy] = packet_data[:samples_to_copy]
            self.ch2_idx[host] += samples_to_copy
        
        # Stop streaming when buffers are full for this host
        if self.ch1_idx[host] >= self.max_samples or self.ch2_idx[host] >= self.max_samples:
            if not self.stop_requested[host]:
                self.stop_requested[host] = True
                print(f"Buffer full for {host} - stopping stream (CH1: {self.ch1_idx[host]}, CH2: {self.ch2_idx[host]} samples)")
                client.notifyStop(host)
    
    def get_data(self, host):
        """
        Returns the collected data arrays for a specific host, trimmed to actual size.
        
        Args:
            host: The host address to retrieve data for
            
        Returns:
            tuple: (channel1_data, channel2_data) as numpy arrays
        """
        return self.ch1_data[host][:self.ch1_idx[host]], self.ch2_data[host][:self.ch2_idx[host]]
    
    def print_channel_stats(self, host, channel_name, data):
        """
        Print statistics for a specific channel and host.
        
        Args:
            host: The host address
            channel_name: Name of the channel (e.g., "Channel 1")
            data: Numpy array of channel data
        """
        if len(data) == 0:
            print(f"  {host} - {channel_name}: No data collected")
            return
        
        print(f"  {host} - {channel_name}: {len(data):,} samples")
        print(f"    Min: {data.min():6d}  Max: {data.max():6d}  Mean: {data.mean():6.2f}")
        print(f"    First 10 samples: {data[:10]}")
    
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

# Multi-board configuration
hosts = ['200.0.0.7', '200.0.0.8']  # Master and slave IP addresses

# ADC sampling configuration
decimation = 64                     # Decimation factor (1, 2, 4, 8, 16, 17, 18, ..., 65536)
sample_rate = 125e6 / decimation    # Red Pitaya ADC base rate is 125 MS/s
capture_duration = 1                # Duration to capture in seconds

# Network streaming configuration
block_size = 16384                  # Network packet size in bytes (range: 2048 to 2097152)
adc_size = 1638400                  # Reserved memory for ADC streaming on Red Pitaya

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
print("Red Pitaya Multi-Board ADC Streaming Configuration")
print("=" * 70)
print(f"Number of boards: {len(hosts)} (Master + {len(hosts)-1} Slave)")
print(f"Master board:     {hosts[0]}")
for i in range(1, len(hosts)):
    print(f"Slave board {i}:    {hosts[i]}")
print(f"Sample rate:      {sample_rate/1e6:.2f} MS/s (decimation: {decimation})")
print(f"Capture time:     {capture_duration} seconds")
print(f"Samples/channel:  {max_samples_per_channel:,}")
print(f"Memory per board: {max_samples_per_channel * 2 * 2 / (1024*1024):.1f} MB")
print(f"Total memory:     {max_samples_per_channel * 2 * 2 * len(hosts) / (1024*1024):.1f} MB")
print("=" * 70)


# ==============================================================================
# MAIN PROGRAM - Multi-board synchronized streaming
# ==============================================================================

# Step 1: Create streaming client and callback handler
confObj = streaming.ConfigStreamClient()
client = streaming.ADCStreamClient(confObj)
confCallback = ConfigCallback()
confObj.addCallback(confCallback)
callback = Callback(hosts=hosts, max_samples_per_channel=max_samples_per_channel)
client.setReceiveDataCallback(callback)
confObj.setVerbose(True)
client.setVerbose(False)

# Step 2: Connect to all Red Pitaya boards
print(f"\nAttempting connection to hosts: {', '.join(hosts)}")
if not confObj.connect(hosts):
    print("ERROR: Connection failed to all specified hosts")
    print("Make sure all Red Pitaya boards are reachable and streaming app is running.")
    exit(1)

# Step 3: Configure master board
master_host = hosts[0]
print(f"\nConfiguring master board: {master_host}")

confObj.sendConfig(master_host, 'adc_pass_mode', 'NET')              # Set network mode
confObj.sendConfig(master_host, 'adc_decimation', f'{decimation}')   # Set decimation factor
confObj.sendConfig(master_host, 'block_size', f'{block_size}')       # Set network packet size
confObj.sendConfig(master_host, 'adc_size', f'{adc_size}')           # Set FPGA buffer size
confObj.sendConfig(master_host, 'channel_state_1', f'{ch1_state}')   # Enable/disable channel 1
confObj.sendConfig(master_host, 'channel_state_2', f'{ch2_state}')   # Enable/disable channel 2

# Step 4: Clone configuration from master to slave(s)
if len(hosts) > 1:
    print("Cloning configuration to slave board(s)...")
    full_config = confObj.getFileConfig(master_host)
    for i in range(1, len(hosts)):
        confObj.sendFileConfig(hosts[i], full_config)
        print(f"  Configuration sent to: {hosts[i]}")

# Step 5: Start synchronized streaming
print("\nStarting synchronized streaming...")
if not client.startStreaming():
    print("ERROR: Failed to start streaming session")
    exit(1)

print("Streaming started - collecting data from all boards...")

# Step 6: Wait for streaming to complete
client.wait()

# Step 7: Retrieve and display results
print("\n" + "=" * 70)
print("ACQUISITION COMPLETE")
print("=" * 70)

print("\nSample statistics per board:")
for host in hosts:
    print(f"  {host}: {callback.counter[host]:,} samples received")

print("\nSamples lost by FPGA per board:")
for host in hosts:
    print(f"  {host}: {callback.fpgaLost[host]:,} samples lost")

# Print detailed statistics for each board and channel
print("\nDetailed channel statistics:")
for host in hosts:
    ch1_samples, ch2_samples = callback.get_data(host)
    callback.print_channel_stats(host, "Channel 1", ch1_samples)
    callback.print_channel_stats(host, "Channel 2", ch2_samples)

print("\n" + "=" * 70)
print("Data is now available via callback.get_data(host)")
print(f"Example: ch1_samples, ch2_samples = callback.get_data('{hosts[0]}')")
print("You can now process, analyze, or save the data as needed")
print("=" * 70)
