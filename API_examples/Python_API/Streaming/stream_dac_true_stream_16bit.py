#!/usr/bin/python3
"""
Red Pitaya DAC Streaming - True Streaming Mode, 16-bit

The board continuously requests new sample blocks from the host by calling
streamData16Bit() in the callback. This allows infinite, on-the-fly waveform
generation without pre-allocating large buffers.

Use this mode when:
  - The waveform must be generated or modified in real time
  - The signal is infinite or longer than FPGA RAM
  - Full 16-bit amplitude resolution is required

Compared to stream_dac_true_stream_8bit.py, this example uses int16 samples
(range -32767 to +32767) for higher dynamic range.

Mode: True streaming (host-driven, callback sink)
Channels: 2
Bit depth: 16-bit signed (int16, range -32767 to +32767)
"""

import streaming
import numpy as np


# ==============================================================================
# CALLBACK CLASS - Handles streaming events and provides real-time data
# ==============================================================================

class Callback(streaming.DACCallback):
    """
    Custom callback handler for DAC streaming with real-time data generation.

    The key method here is streamData16Bit(), which is called repeatedly by
    the streaming engine whenever it needs more 16-bit samples to send to the DAC.
    All other methods handle connection and server state events.
    """

    counter = 0  # Count of data packets sent

    def streamData16Bit(self, client, ch1, ch2, size):
        """
        Called by the streaming engine each time it needs a new block of samples.

        This method must fill ch1 and ch2 with 'size' 16-bit signed samples.
        Return False to continue streaming, or True to stop.

        Args:
            client: The streaming client instance
            ch1:    memoryview buffer for channel 1 (int16), or None if not active
            ch2:    memoryview buffer for channel 2 (int16), or None if not active
            size:   Number of samples to generate (buffer length)

        Returns:
            bool: False to continue streaming, True to stop
        """
        try:
            # Generate one full sine cycle across the requested block size
            t = np.linspace(0, 2 * np.pi, size, endpoint=False, dtype=np.float32)
            samples = (np.sin(t) * 32767).astype(np.int16)

            # Copy data into the memoryview buffers provided by the streaming engine
            # Use cast('h') for int16 (signed short) format
            if ch1 is not None:
                ch1.cast('h')[:] = samples
            if ch2 is not None:
                ch2.cast('h')[:] = samples

            print(f"streamData size {size}")

            return False  # Return False to continue streaming

        except Exception as e:
            print(f"streamData16Bit error: {e}")
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
dac_rate = 15625000             # DAC sampling rate in Hz
block_size = int(0.5*1048576)   # Network packet size in bytes (0.5 MB)
dac_memory_size = 128*1048576   # Reserved memory for DAC streaming in bytes (128 MB)

# Channel enable flags (passed to startStreamingFromMemorySink)
enable_ch1 = True               # Enable channel 1 output
enable_ch2 = True               # Enable channel 2 output

print("=" * 70)
print("Red Pitaya DAC Streaming Configuration - Memory Sink (16-bit)")
print("=" * 70)
print(f"DAC rate:        {dac_rate/1e6:.5f} MS/s")
print(f"Bit depth:       16-bit signed (int16, range -32767 to +32767)")
print(f"Mode:            Real-time callback sink (on-the-fly generation)")
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

# Step 4: Start streaming in memory sink mode (16-bit)
# The streaming engine will call streamData16Bit() repeatedly for new data blocks.
# Parameters: host, enable_ch1, enable_ch2, bit_depth
print("\nStarting DAC streaming in 16-bit memory sink mode...")
host = confObj.getHosts()[0]
if not client.startStreamingFromMemorySink(host, enable_ch1, enable_ch2, streaming.DAC_16BIT):
    print("ERROR: Failed to start DAC streaming from memory sink")
    exit(1)

print("Streaming started - generating and outputting 16-bit waveform in real time...")
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
