#!/usr/bin/python3
"""
Red Pitaya DAC Streaming Example - Stereo Output

This example demonstrates how to stream stereo waveform data to Red Pitaya DACs.
It generates a sine wave for both channels, saves it as a stereo WAV file,
and streams it continuously to both DAC outputs in infinite loop mode.
"""

import streaming
import numpy as np
from scipy.io.wavfile import write


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
    
    def sendedPack(self, client, ch1_size, ch2_size):
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
# CONFIGURATION - Set your DAC streaming parameters here
# ==============================================================================

# DAC output configuration
dac_rate = 125000000            # DAC sampling rate in Hz (max 125 MS/s)
block_size = 262144             # Network packet size in bytes (larger for stereo)
dac_memory_size = 2621440       # Reserved memory for DAC streaming in bytes

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
data = amplitude * np.sin(2. * np.pi * waveform_frequency * t)

# Create stereo data by stacking the same waveform for both channels
# This creates a 2D array: [[ch1_sample1, ch2_sample1], [ch1_sample2, ch2_sample2], ...]
stereo = np.vstack((data.astype(np.uint8), data.astype(np.uint8)))
stereo = stereo.transpose()  # Transpose to interleave channels

# Save as stereo WAV file (8-bit PCM format)
write(wav_filename, waveform_samples, stereo)
print(f"Stereo waveform saved to '{wav_filename}'")
print(f"File format: {stereo.shape[0]} samples x {stereo.shape[1]} channels (8-bit)")


# ==============================================================================
# MAIN PROGRAM - Connect, configure, and start streaming
# ==============================================================================

# Step 1: Create streaming client and callback handler
obj = streaming.DACStreamClient()
callback = Callback()
obj.setCallbackFunction(callback.__disown__())  # __disown__() transfers ownership to client
obj.setVerbose(True)  # Enable detailed logging

# Step 2: Connect to Red Pitaya streaming server
print("\nConnecting to Red Pitaya...")
if not obj.connect():
    print("ERROR: Failed to connect to DAC streaming server")
    print("Make sure Red Pitaya streaming app is running")
    exit(1)

# Step 3: Configure DAC streaming parameters
print("Configuring DAC streaming parameters...")
current_rate = obj.getConfig('dac_rate')
print(f"Current DAC rate: {current_rate} Hz")

obj.sendConfig('dac_pass_mode', 'NET')              # Set network mode (NET or FILE)
obj.sendConfig('dac_rate', f'{dac_rate}')           # Set DAC sampling rate
obj.sendConfig('block_size', f'{block_size}')       # Set network packet size
obj.sendConfig('adc_size', f'{dac_memory_size}')    # Set FPGA buffer size

# Step 4: Configure playback mode
obj.setRepeatInf(repeat_infinite)                   # Enable/disable infinite repeat
if not repeat_infinite:
    obj.setRepeatCount(repeat_count)                # Set number of repetitions

# Step 5: Start streaming the stereo WAV file
print(f"\nStarting DAC streaming from '{wav_filename}'...")
if not obj.startStreamingWAV(f"./{wav_filename}"):
    print("ERROR: Failed to start DAC streaming")
    exit(1)

if repeat_infinite:
    print("Streaming started - outputting stereo waveform to both DACs (infinite loop)...")
    print("Press Ctrl+C to stop streaming")
else:
    print(f"Streaming started - will play {repeat_count} time(s)...")

# Step 6: Wait for streaming to complete (or Ctrl+C if infinite)
try:
    obj.wait()
except KeyboardInterrupt:
    print("\n\nStreaming interrupted by user")

# Step 7: Display results
print("\n" + "=" * 70)
print("STREAMING COMPLETE")
print("=" * 70)
print(f"Total data packets sent: {callback.counter}")
print("=" * 70)