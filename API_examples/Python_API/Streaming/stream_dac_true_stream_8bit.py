#!/usr/bin/python3
"""
Red Pitaya DAC Streaming - True Streaming Mode, 8-bit

The board continuously requests new sample blocks from the host by calling
streamData8Bit() in the callback. This allows infinite, on-the-fly waveform
generation without pre-allocating large buffers.

Use this mode when:
  - The waveform must be generated or modified in real time
  - The signal is infinite or longer than FPGA RAM
  - 8-bit amplitude resolution is sufficient

Mode: True streaming (host-driven, callback sink)
Channels: 2
Bit depth: 8-bit signed (int8, range -127 to +127)
"""

import streaming
import numpy as np


# ==============================================================================
# CALLBACK CLASS - Handles streaming events and provides real-time data
# ==============================================================================

class Callback(streaming.DACCallback):
    """
    Custom callback handler for DAC streaming with real-time data generation.

    The key method here is streamData8Bit(), which is called repeatedly by
    the streaming engine whenever it needs more 8-bit samples to send to the DAC.
    All other methods handle connection and server state events.
    """

    counter = 0  # Count of data packets sent

    def streamData8Bit(self, client, ch1, ch2, size):
        """
        Called by the streaming engine each time it needs a new block of samples.

        This method must fill ch1 and ch2 with 'size' 8-bit signed samples.
        Return False to continue streaming, or True to stop.

        Args:
            client: The streaming client instance
            ch1:    memoryview buffer for channel 1 (int8), or None if not active
            ch2:    memoryview buffer for channel 2 (int8), or None if not active
            size:   Number of samples to generate (buffer length)

        Returns:
            bool: False to continue streaming, True to stop
        """
        try:
            # Generate one full sine cycle across the requested block size
            t = np.linspace(0, 2 * np.pi, size, endpoint=False, dtype=np.float32)
            samples = (np.sin(t) * 127).astype(np.int8)

            # Copy data into the memoryview buffers provided by the streaming engine
            if ch1 is not None:
                ch1.cast('b')[:] = samples
            if ch2 is not None:
                ch2.cast('b')[:] = samples

            print(f"streamData size {size}")

            return False  # Return False to continue streaming

        except Exception as e:
            print(f"streamData8Bit error: {e}")
            return True  # Return True to stop streaming on error

    def sentPack(self, client, ch1_size, ch2_size):
        """
        Called when a data packet has been sent to the DAC.

        Args:
            client: The streaming client instance
            ch1_size: Number of samples sent to channel 1
            ch2_size: Number of samples sent to channel 2
        """
        self.counter += 1
        # Uncomment for detailed packet logging:
        # print(f"Data sent - CH1: {ch1_size} samples, CH2: {ch2_size} samples")

    # Connection event handlers
    def connected(self, client, host):
        print(f"DAC client connected: {host}")

    def disconnected(self, client, host):
        print(f"DAC client disconnected: {host}")

    def error(self, client, host, code):
        print(f"DAC client error on {host}, code: {code}")
        client.notifyStop()

    # Server stop event handlers
    def stopped(self, client, host):
        print(f"DAC server stopped: {host}")
        client.notifyStop()

    def stoppedFileEnd(self, client, host):
        print(f"DAC server stopped: {host} - File playback finished")
        client.notifyStop()

    def stoppedFileBroken(self, client, host):
        print(f"DAC server stopped: {host} - File is corrupted")
        client.notifyStop()

    def stoppedEmpty(self, client, host):
        print(f"DAC server stopped: {host} - File is empty")
        client.notifyStop()

    def stoppedMemError(self, client, host):
        print(f"DAC server stopped: {host} - Memory error")
        client.notifyStop()

    def stoppedMemModify(self, client, host):
        print(f"DAC server stopped: {host} - Memory changed")
        client.notifyStop()

    def stoppedMissingFile(self, client, host):
        print(f"DAC server stopped: {host} - File not found")
        client.notifyStop()


# ==============================================================================
# CONFIG CHANNEL CALLBACK - Handles configuration events
# ==============================================================================

class ConfigCallback(streaming.ConfigCallback):
    """Handles configuration channel events from ConfigStreamClient."""

    def sigInt(self):
        client.notifyStop()


# ==============================================================================
# CONFIGURATION - Set your DAC streaming parameters here
# ==============================================================================

# DAC output configuration
dac_rate = int(15.625e6)          # DAC sampling rate in Hz (max 125 MS/s)
block_size = 4*1048576          # Network packet size in bytes
dac_memory_size = 64*1048576    # Reserved memory for DAC streaming in bytes
adc_memory_size = 0        # Reserved memory for ADC streaming (not used here but set to default)

# Channel enable flags (passed to startStreamingFromMemorySink)
enable_ch1 = True               # Enable channel 1 output
enable_ch2 = False               # Enable channel 2 output

print("=" * 70)
print("Red Pitaya DAC Streaming Configuration - Memory Sink (8-bit)")
print("=" * 70)
print(f"DAC rate:        {dac_rate/1e6:.4f} MS/s")
print("Bit depth:       8-bit signed (int8, range -127 to +127)")
print("Mode:            Real-time callback sink (on-the-fly generation)")
print(f"Channels:        {'CH1' if enable_ch1 else ''} {'CH2' if enable_ch2 else ''}".strip())
print("=" * 70)


# ==============================================================================
# MAIN PROGRAM - Connect, configure, and start streaming
# ==============================================================================

# Step 1: Create streaming client and callback handler
confObj = streaming.ConfigStreamClient()
client = streaming.DACStreamClient(confObj)
confCallback = ConfigCallback()
confObj.addCallback(confCallback)
callback = Callback()
client.setCallback(callback)
confObj.setVerbose(True)
client.setVerbose(True)

# Step 2: Connect to Red Pitaya streaming server
print("\nConnecting to Red Pitaya...")
if not confObj.connect():
    print("ERROR: Failed to connect to DAC streaming server")
    print("Make sure Red Pitaya streaming app is running and the stream_app FPGA is loaded.")
    exit(1)

# Step 3: Configure DAC streaming parameters
print("Configuring DAC streaming parameters...")
current_rate = confObj.getConfig('dac_rate')
print(f"Current DAC rate: {current_rate} Hz")

confObj.sendConfig('dac_pass_mode', 'DAC_NET')         # Set network mode
confObj.sendConfig('dac_rate', f'{dac_rate}')          # Set DAC sampling rate
confObj.sendConfig('block_size', f'{block_size}')      # Set network packet size
confObj.sendConfig('dac_size', f'{dac_memory_size}')   # Set FPGA buffer size

# Step 4: Start streaming in memory sink mode (8-bit)
# The streaming engine will call streamData8Bit() repeatedly for new data blocks.
# Parameters: host, enable_ch1, enable_ch2, bit_depth
print("\nStarting DAC streaming in 8-bit memory sink mode...")
host = confObj.getHosts()[0]
if not client.startStreamingFromMemorySink(host, enable_ch1, enable_ch2, streaming.DAC_8BIT):
    print("ERROR: Failed to start DAC streaming from memory sink")
    exit(1)

print("Streaming started - generating and outputting 8-bit waveform in real time...")
print("Press Ctrl+C to stop.")

# Step 5: Wait for streaming to complete (or Ctrl+C to interrupt)
try:
    client.wait()
except KeyboardInterrupt:
    print("\nStreaming interrupted by user.")
    client.notifyStop()

# Step 6: Display results
print("\n" + "=" * 70)
print("STREAMING COMPLETE")
print("=" * 70)
print(f"Total data packets sent: {callback.counter}")
print("=" * 70)
