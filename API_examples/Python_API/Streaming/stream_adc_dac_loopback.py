#!/usr/bin/python3
"""
Red Pitaya ADC + DAC Streaming - Signal-Triggered Loopback

Runs ADC and DAC streaming simultaneously. The ADC callback monitors incoming
samples for a signal above a configurable threshold. When a signal is detected,
the raw samples are queued and the DAC true-streaming callback reads from that
queue to play them back on both output channels.

When the queue is empty (no signal detected), the DAC outputs silence (zeros).

Mode: True streaming loopback (ADC → queue → DAC)
ADC channels: 1 and 2
DAC channels: 1 and 2
DAC bit depth: 16-bit
"""

import streaming
import queue
import numpy as np


# ==============================================================================
# CONFIGURATION
# ==============================================================================

SIGNAL_THRESHOLD = 1000     # ADC sample amplitude that counts as a signal (0–32767)

# ADC configuration
adc_decimation  = 64        # Decimation factor; effective rate = 125 MS/s / decimation
adc_block_size  = 65536     # Network packet size in bytes
adc_memory_size = 1638400   # Reserved FPGA memory for ADC streaming in bytes

# DAC configuration
dac_rate        = 1953125   # DAC output rate in Hz (125 MS/s / 64 = 1.953 MS/s)
dac_memory_size = 1638400   # Reserved FPGA memory for DAC streaming in bytes


# ==============================================================================
# SHARED BUFFER — samples pass from ADC callback to DAC callback via this queue
# ==============================================================================

sample_queue: queue.Queue = queue.Queue()


# ==============================================================================
# ADC CALLBACK
# ==============================================================================

class ADCCallback(streaming.ADCCallback):
    """
    Receives ADC data packets and pushes samples to the shared queue whenever
    the signal amplitude exceeds SIGNAL_THRESHOLD.
    """

    def __init__(self):
        streaming.ADCCallback.__init__(self)
        self.total_samples = 0
        self.fpga_lost     = 0

    def receivePack(self, client, pack):
        self.total_samples += (pack.channel1.samples + pack.channel2.samples +
                               pack.channel3.samples + pack.channel4.samples)
        self.fpga_lost += max(pack.channel1.fpgaLost, pack.channel2.fpgaLost,
                              pack.channel3.fpgaLost, pack.channel4.fpgaLost)

        # Use channel 1 for threshold detection
        if pack.channel1.samples > 0:
            self._check_and_queue(pack.channel1)

    def _check_and_queue(self, channel):
        """Push channel data to the queue if any sample exceeds the threshold."""
        for sample in channel.raw:
            if abs(sample) > SIGNAL_THRESHOLD:
                sample_queue.put(np.array(channel.raw, dtype=np.int16))
                print(f"Signal detected — queued {channel.samples} samples")
                break

    # Connection / server-stop handlers
    def connected(self, client, host):
        print(f"ADC connected: {host}")

    def disconnected(self, client, host):
        print(f"ADC disconnected: {host}")

    def error(self, client, host, code):
        print(f"ADC error on {host}, code: {code}")

    def stopped(self, client, host, code):
        print(f"ADC server stopped: {host}")

    def stoppedNoActiveChannels(self, client, host):
        print(f"ADC server stopped: {host} - No active channels")

    def stoppedMemError(self, client, host):
        print(f"ADC server stopped: {host} - Memory error")

    def stoppedMemModify(self, client, host):
        print(f"ADC server stopped: {host} - Memory changed")

    def stoppedSDFull(self, client, host):
        print(f"ADC server stopped: {host} - SD card full")

    def stoppedSDDone(self, client, host):
        print(f"ADC server stopped: {host} - Data written to SD card")

    def configConnected(self, client, host):
        print(f"ADC control connected: {host}")

    def configError(self, client, host, code):
        print(f"ADC control error on {host}, code: {code}")

    def configErrorTimeout(self, client, host):
        print(f"ADC control timeout on {host}")


# ==============================================================================
# DAC CALLBACK
# ==============================================================================

class DACCallback(streaming.DACCallback):
    """
    Provides samples to the DAC true-streaming engine.

    When the shared queue contains data captured by the ADC, that data is played
    back. Otherwise, zeros (silence) are written to the output buffers.
    """

    def __init__(self):
        streaming.DACCallback.__init__(self)
        self.packets_sent = 0

    def streamData16Bit(self, client, ch1, ch2, size):
        """
        Called by the streaming engine each time it needs a new block of samples.

        Returns:
            False to continue streaming, True to stop on error.
        """
        try:
            if sample_queue.empty():
                # No signal detected — output silence
                silence = np.zeros(size, dtype=np.int16)
                if ch1 is not None:
                    ch1.cast('h')[:] = silence
                if ch2 is not None:
                    ch2.cast('h')[:] = silence
                return False

            data = sample_queue.get_nowait()
            samples_to_send = min(size, len(data))

            if ch1 is not None:
                view = ch1.cast('h')
                view[:samples_to_send] = data[:samples_to_send]
                if samples_to_send < size:
                    view[samples_to_send:] = 0

            if ch2 is not None:
                view = ch2.cast('h')
                view[:samples_to_send] = data[:samples_to_send]
                if samples_to_send < size:
                    view[samples_to_send:] = 0

            return False

        except Exception as e:
            print(f"streamData16Bit error: {e}")
            return True

    def sentPack(self, client, ch1_size, ch2_size):
        self.packets_sent += 1
        # Uncomment for detailed logging:
        # print(f"DAC sent — CH1: {ch1_size}, CH2: {ch2_size} samples")

    # Connection / server-stop handlers
    def connected(self, client, host):
        print(f"DAC connected: {host}")

    def disconnected(self, client, host):
        print(f"DAC disconnected: {host}")

    def error(self, client, host, code):
        print(f"DAC error on {host}, code: {code}")
        client.notifyStop()

    def stopped(self, client, host):
        print(f"DAC server stopped: {host}")
        client.notifyStop()

    def stoppedFileEnd(self, client, host):
        print(f"DAC server stopped: {host} - File end")
        client.notifyStop()

    def stoppedFileBroken(self, client, host):
        print(f"DAC server stopped: {host} - File corrupted")
        client.notifyStop()

    def stoppedEmpty(self, client, host):
        print(f"DAC server stopped: {host} - Empty")
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

    def configConnected(self, client, host):
        print(f"DAC control connected: {host}")

    def configError(self, client, host, code):
        print(f"DAC control error on {host}, code: {code}")
        client.notifyStop()

    def configErrorTimeout(self, client, host):
        print(f"DAC control timeout on {host}")
        client.notifyStop()


# ==============================================================================
# MAIN PROGRAM
# ==============================================================================

print("=" * 70)
print("Red Pitaya ADC + DAC Streaming — Signal-Triggered Loopback")
print("=" * 70)
print(f"Signal threshold:  {SIGNAL_THRESHOLD}")
print(f"ADC decimation:    {adc_decimation}  (rate: {125e6/adc_decimation/1e6:.3f} MS/s)")
print(f"DAC output rate:   {dac_rate/1e6:.3f} MS/s")
print("=" * 70)

# Step 1: Create clients and callbacks
# A single ConfigStreamClient is shared by both ADC and DAC clients
confObj     = streaming.ConfigStreamClient()
adc_client  = streaming.ADCStreamClient(confObj)
dac_client  = streaming.DACStreamClient(confObj)

adc_callback = ADCCallback()
dac_callback = DACCallback()

adc_client.setReceiveDataCallback(adc_callback)
dac_client.setCallback(dac_callback)
confObj.setVerbose(True)
adc_client.setVerbose(False)
dac_client.setVerbose(True)

# Step 2: Connect (single connect call covers both ADC and DAC)
print("\nConnecting to Red Pitaya...")
if not confObj.connect():
    print("ERROR: Failed to connect")
    print("Make sure Red Pitaya streaming app is running and the stream_app FPGA is loaded.")
    exit(1)

# Step 3: Configure ADC
print("Configuring ADC...")
print(f"Current ADC decimation: {confObj.getConfig('adc_decimation')}")

confObj.sendConfig('adc_pass_mode',    'NET')
confObj.sendConfig('adc_decimation',   f'{adc_decimation}')
confObj.sendConfig('block_size',       f'{adc_block_size}')
confObj.sendConfig('adc_size',         f'{adc_memory_size}')
confObj.sendConfig('channel_state_1',  'ON')
confObj.sendConfig('channel_state_2',  'ON')

# Step 4: Configure DAC
print("Configuring DAC...")
print(f"Current DAC rate: {confObj.getConfig('dac_rate')}")

confObj.sendConfig('dac_pass_mode', 'DAC_NET')
confObj.sendConfig('dac_rate',      f'{dac_rate}')
confObj.sendConfig('dac_size',      f'{dac_memory_size}')

# Step 5: Start ADC streaming
print("\nStarting ADC streaming...")
if not adc_client.startStreaming():
    print("ERROR: Failed to start ADC streaming")
    exit(1)

# Step 6: Start DAC true streaming (16-bit, both channels)
print("Starting DAC true streaming (16-bit)...")
host = confObj.getHosts()[0]
if not dac_client.startStreamingFromMemorySink(host, True, True, streaming.DAC_16BIT):
    print("ERROR: Failed to start DAC streaming")
    adc_client.notifyStop()
    exit(1)

print("\nLoopback running — press Ctrl+C to stop.")

# Step 7: Wait for completion or user interrupt
try:
    adc_client.wait()
except KeyboardInterrupt:
    print("\nInterrupted by user.")
    adc_client.notifyStop()

dac_client.notifyStop()
dac_client.wait()

# Step 8: Display statistics
print("\n" + "=" * 70)
print("LOOPBACK COMPLETE")
print("=" * 70)
print(f"ADC total samples received: {adc_callback.total_samples:,}")
print(f"ADC samples lost (FPGA):    {adc_callback.fpga_lost:,}")
print(f"DAC packets sent:           {dac_callback.packets_sent:,}")
print("=" * 70)
