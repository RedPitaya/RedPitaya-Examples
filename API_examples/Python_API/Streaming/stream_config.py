#!/usr/bin/python3
"""
Red Pitaya Streaming - Configuration Client

Standalone example showing how to use the ConfigStreamClient to query and
change Red Pitaya streaming settings without starting an ADC or DAC stream.

Use this to:
  - Inspect current ADC/DAC settings on a live board
  - Push a new configuration before running a capture
  - Query active channels and memory block size
  - Save a configuration permanently to the board

All available callback events from the config channel are implemented so
that server-side confirmations and errors are visible in the console.
"""

import streaming


# ==============================================================================
# CALLBACK CLASS — receives responses and server events from the config channel
# ==============================================================================

class ConfigCallback(streaming.ConfigCallback):
    """
    Handles all callback events issued by the ConfigStreamClient.

    Each method corresponds to a server-side event or response. Implement
    only the ones you care about; the rest can be left as pass stubs.
    """

    # --- Connection events ---

    def configConnected(self, client, host: str):
        print(f"Config connected: {host}")

    def configError(self, client, host: str, code: int):
        print(f"Config error on {host}, code: {code}")

    def configErrorTimeout(self, client, host: str):
        print(f"Config timeout on {host}")

    def configErrorFileMissed(self, client, host: str):
        print(f"Config error on {host}: file not found")

    # --- Config response events ---

    def configMemoryBlockSize(self, client, host: str, block_size: int):
        print(f"Memory block size on {host}: {block_size} bytes")

    def configActiveChannels(self, client, host: str, channels: int):
        print(f"Active channels on {host}: {channels}")

    def configSuccessSend(self, client, host: str):
        print(f"Config sent successfully to {host}")

    def configFailSend(self, client, host: str):
        print(f"Config send failed on {host}")

    def configSuccessSave(self, client, host: str):
        print(f"Config saved successfully on {host}")

    def configFailSave(self, client, host: str):
        print(f"Config save failed on {host}")

    def configGetNewSettings(self, client, host: str):
        print(f"New settings received from {host}")

    # --- ADC server events ---

    def adcServerStopped(self, client, host: str):
        print(f"ADC server stopped: {host}")

    def adcServerStoppedNoActiveChannels(self, client, host: str):
        print(f"ADC server stopped: {host} - No active channels")

    def adcServerStoppedMemError(self, client, host: str):
        print(f"ADC server stopped: {host} - Memory error")

    def adcServerStoppedMemModify(self, client, host: str):
        print(f"ADC server stopped: {host} - Memory modified")

    def adcServerStoppedSDFull(self, client, host: str):
        print(f"ADC server stopped: {host} - SD card full")

    def adcServerStoppedSDDone(self, client, host: str):
        print(f"ADC server stopped: {host} - Data written to SD card")

    def adcServerStartedTCP(self, client, host: str):
        print(f"ADC server started (TCP): {host}")

    def adcServerStartedSD(self, client, host: str):
        print(f"ADC server started (SD card): {host}")

    def adcServerStartedFPGA(self, client, host: str):
        print(f"ADC server started (FPGA): {host}")

    # --- DAC server events ---

    def dacServerStartedTCP(self, client, host: str):
        print(f"DAC server started (TCP): {host}")

    def dacServerStartedSD(self, client, host: str):
        print(f"DAC server started (SD card): {host}")

    def dacServerStoppedMemError(self, client, host: str):
        print(f"DAC server stopped: {host} - Memory error")

    def dacServerStoppedMemModify(self, client, host: str):
        print(f"DAC server stopped: {host} - Memory modified")

    def dacServerStoppedConfigError(self, client, host: str):
        print(f"DAC server stopped: {host} - Configuration error")

    def dacServerStoppedFileMissed(self, client, host: str):
        print(f"DAC server stopped: {host} - File not found")

    def dacServerStoppedSDDone(self, client, host: str):
        print(f"DAC server stopped: {host} - SD card operation completed")

    def dacServerStoppedSDEmpty(self, client, host: str):
        print(f"DAC server stopped: {host} - SD card empty")

    def dacServerStoppedSDBroken(self, client, host: str):
        print(f"DAC server stopped: {host} - SD card broken")

    def dacServerStoppedSDMissing(self, client, host: str):
        print(f"DAC server stopped: {host} - SD card missing")


# ==============================================================================
# CONFIGURATION — set the parameters you want to push to the board
# ==============================================================================

# ADC settings
adc_decimation  = 64        # Decimation factor (effective rate = 125 MS/s / decimation)
block_size      = 16384     # Network packet size in bytes
adc_memory_size = 1638400   # Reserved FPGA memory for ADC streaming in bytes
ch1_state       = 'ON'      # Channel 1: 'ON' or 'OFF'
ch2_state       = 'ON'      # Channel 2: 'ON' or 'OFF'


# ==============================================================================
# MAIN PROGRAM
# ==============================================================================

print("=" * 70)
print("Red Pitaya Streaming — Configuration Client")
print("=" * 70)

# Step 1: Create client and register callback
client   = streaming.ConfigStreamClient()
callback = ConfigCallback()
client.addCallback(callback)
client.setVerbose(True)

# Step 2: Connect (auto-discover board on the network)
print("\nConnecting to Red Pitaya...")
if not client.connect():
    print("ERROR: Config client failed to connect")
    print("Make sure Red Pitaya streaming app is running and the stream_app FPGA is loaded.")
    exit(1)

# Step 3: Read current settings
print("\nReading current settings...")
current_decimation = client.getConfig('adc_decimation')
print(f"Current ADC decimation: {current_decimation}")

# Request memory block size and active channels from the first discovered host
first_host = client.getHosts()[0]
print(f"First discovered host: {first_host}")
client.requestMemoryBlockSize(first_host)
client.requestActiveChannels(first_host)

# Step 4: Push new configuration
print("\nPushing new configuration...")
client.sendConfig('adc_pass_mode',   'NET')
client.sendConfig('adc_decimation',  f'{adc_decimation}')
client.sendConfig('block_size',      f'{block_size}')
client.sendConfig('adc_size',        f'{adc_memory_size}')
client.sendConfig('channel_state_1', f'{ch1_state}')
client.sendConfig('channel_state_2', f'{ch2_state}')

print("\nConfiguration complete.")
print("=" * 70)
print(f"ADC mode:       NET (network streaming)")
print(f"Decimation:     {adc_decimation}  (rate: {125e6/adc_decimation/1e6:.3f} MS/s)")
print(f"Block size:     {block_size} bytes")
print(f"ADC memory:     {adc_memory_size} bytes")
print(f"Channel 1:      {ch1_state}")
print(f"Channel 2:      {ch2_state}")
print("=" * 70)
