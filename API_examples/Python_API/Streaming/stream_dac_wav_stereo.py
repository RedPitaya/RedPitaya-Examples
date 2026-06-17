#!/usr/bin/python3
"""
Red Pitaya DAC Streaming - WAV File, Stereo

Streams a stereo (two-channel) WAV file to both Red Pitaya DAC outputs.
Generates an 8-bit sine wave for both channels, saves it as a stereo WAV
file, and plays it continuously in an infinite loop.

Mode: WAV file playback
Channels: 2 (stereo)
Bit depth: 8-bit
Playback: infinite loop
"""

import streaming
import numpy as np
import wave


# ==============================================================================
# CALLBACK CLASS - Handles streaming events and monitors data transmission
# ==============================================================================

class Callback(streaming.DACCallback):
    """
    Custom callback handler for DAC streaming events.
    
    This class monitors the streaming process and handles various server states
    including errors, completion, and connection events.
    """
    
    def __init__(self):
        """Initialize the callback handler."""
        streaming.DACCallback.__init__(self)
        self.counter = 0  # Count of data packets sent
    
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
    
    # Control connection handlers
    def configConnected(self, client, host):
        print(f"Control client connected: {host}")

    def configError(self, client, host, code):
        print(f"Control client error on {host}, code: {code}")
        client.notifyStop()

    def configErrorTimeout(self, client, host):
        print(f"Control client timeout on {host}")
        client.notifyStop()


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
# WAV FILE HELPER
# ==============================================================================

def create_stereo_wav(filename, left_channel, right_channel, sample_rate):
    """Write a stereo 8-bit WAV file using Python's built-in wave module."""
    with wave.open(filename, 'w') as f:
        f.setnchannels(2)       # stereo
        f.setsampwidth(1)       # 1 byte per sample (8-bit)
        f.setframerate(sample_rate)
        # Interleave left and right channels
        stereo_data = np.empty((left_channel.size + right_channel.size,), dtype=np.uint8)
        stereo_data[0::2] = left_channel
        stereo_data[1::2] = right_channel
        f.writeframes(stereo_data.tobytes())


# ==============================================================================
# CONFIGURATION - Set your DAC streaming parameters here
# ==============================================================================

# DAC output configuration
dac_rate = 125000000            # DAC sampling rate in Hz (max 125 MS/s)
block_size = 262144             # Network packet size in bytes (larger for stereo)
dac_memory_size = 5242880       # Reserved memory for DAC streaming in bytes

# Waveform generation parameters
waveform_frequency = 1          # Frequency of generated sine wave in Hz
waveform_samples = 1024 * 256   # Number of samples in generated waveform (per channel)
wav_filename = "sin.wav"        # Output WAV file name

# Playback configuration
repeat_infinite = True          # Set to True for continuous playback
repeat_count = 1                # Number of times to repeat (ignored if infinite is True)

print("=" * 70)
print("Red Pitaya DAC Streaming Configuration - Stereo Mode")
print("=" * 70)
print(f"DAC rate:        {dac_rate/1e6:.2f} MS/s")
print(f"Waveform:        {waveform_frequency} Hz sine wave (stereo)")
print(f"Waveform size:   {waveform_samples} samples per channel")
print(f"Repeat mode:     {'Infinite (continuous loop)' if repeat_infinite else f'{repeat_count} times'}")
print(f"Output file:     {wav_filename}")
print("=" * 70)


# ==============================================================================
# WAVEFORM GENERATION - Create stereo signal to stream
# ==============================================================================

print("\nGenerating stereo waveform...")

# Create time array
t = np.linspace(0., 1., waveform_samples)

# Generate sine wave with maximum amplitude for 8-bit unsigned format
amplitude = np.iinfo(np.int8).max
data = (amplitude * np.sin(2. * np.pi * waveform_frequency * t)).astype(np.int8)

# Create stereo WAV file (8-bit PCM, interleaved channels)
create_stereo_wav(wav_filename, data, data, waveform_samples)
print(f"Stereo waveform saved to '{wav_filename}'")
print(f"File format: {waveform_samples} samples x 2 channels (8-bit)")


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
    print("Make sure Red Pitaya streaming app is running")
    exit(1)

# Step 3: Configure DAC streaming parameters
print("Configuring DAC streaming parameters...")
current_rate = confObj.getConfig('dac_rate')
print(f"Current DAC rate: {current_rate} Hz")

confObj.sendConfig('dac_pass_mode', 'DAC_NET')         # Set network mode
confObj.sendConfig('dac_rate', f'{dac_rate}')          # Set DAC sampling rate
confObj.sendConfig('block_size', f'{block_size}')      # Set network packet size
confObj.sendConfig('dac_size', f'{dac_memory_size}')   # Set FPGA buffer size

# Step 4: Configure playback mode
client.setRepeatInf(repeat_infinite)                   # Enable/disable infinite repeat
if not repeat_infinite:
    client.setRepeatCount(repeat_count)                # Set number of repetitions

# Step 5: Start streaming the stereo WAV file
print(f"\nStarting DAC streaming from '{wav_filename}'...")
host = confObj.getHosts()[0]
if not client.startStreamingWAV(host, f"./{wav_filename}"):
    print("ERROR: Failed to start DAC streaming")
    exit(1)

if repeat_infinite:
    print("Streaming started - outputting stereo waveform to both DACs (infinite loop)...")
    print("Press Ctrl+C to stop streaming")
else:
    print(f"Streaming started - will play {repeat_count} time(s)...")

# Step 6: Wait for streaming to complete (or Ctrl+C if infinite)
try:
    client.wait()
except KeyboardInterrupt:
    print("\n\nStreaming interrupted by user")

# Step 7: Display results
print("\n" + "=" * 70)
print("STREAMING COMPLETE")
print("=" * 70)
print(f"Total data packets sent: {callback.counter}")
print("=" * 70)