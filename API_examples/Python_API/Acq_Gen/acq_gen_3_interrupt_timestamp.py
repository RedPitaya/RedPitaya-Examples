#!/usr/bin/python3
"""
Red Pitaya Interrupt-Based Trigger Timestamp Measurement Example
================================================================

This example demonstrates accurate trigger timestamp measurement using
interrupt-based acquisition on Red Pitaya. Two threads run concurrently:
a generator thread that produces periodic burst signals, and an acquisition
thread that measures the time between consecutive triggers using hardware
timestamps.

This is useful for precise timing measurements, jitter analysis, and
applications requiring accurate time-of-arrival measurements.

Features:
- Multi-threaded design: separate generator and acquisition threads
- Interrupt-based trigger detection for precise timing
- Hardware timestamp readout for each trigger event
- Configurable trigger level and decimation
- Graceful shutdown on Ctrl+C
- Reports time delta between consecutive triggers

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)
- Connect OUT1 to IN1 for loopback testing

Software Requirements:
- Red Pitaya Python API (rp module)
- rp_overlay module (for FPGA overlay)
- OS 2.00 or higher

Usage:
    python acq_gen_3_interrupt_timestamp.py

    Connect OUT1 to IN1 with a cable or jumper.
    The program will print the time between consecutive triggers.
    Press Ctrl+C to stop.

Configuration:
    Modify parameters in the CONFIGURATION section:
    - gen_freq: Generator signal frequency in Hz
    - gen_ampl: Generator signal amplitude in volts
    - dec: Decimation factor for acquisition
    - trig_lvl: Trigger threshold voltage
    - gen_period_s: Time between generator bursts in seconds
    - trig_timeout_ms: Timeout for trigger interrupt in milliseconds

Author: Red Pitaya
Date: May 2026
"""

import time
import signal
import threading
import sys
from rp_overlay import overlay
import rp


# ==============================================================================
# CONFIGURATION - Set your generation, acquisition, and timing parameters
# ==============================================================================

# Generation parameters
gen_channel = rp.RP_CH_1        # Generator output channel

# Waveform type
# Available waveforms:
#   RP_WAVEFORM_SINE, RP_WAVEFORM_SQUARE, RP_WAVEFORM_TRIANGLE,
#   RP_WAVEFORM_RAMP_UP, RP_WAVEFORM_RAMP_DOWN, RP_WAVEFORM_DC,
#   RP_WAVEFORM_PWM, RP_WAVEFORM_ARBITRARY, RP_WAVEFORM_DC_NEG,
#   RP_WAVEFORM_SWEEP
gen_waveform = rp.RP_WAVEFORM_SINE

gen_freq = 1000.0               # Generator frequency in Hz (1 kHz)
gen_ampl = 1.0                  # Generator amplitude in volts
gen_burst_cycles = 1            # Number of cycles per burst
gen_period_s = 1.0              # Time between generator triggers in seconds

# Acquisition parameters
# Available decimations: 1, 2, 4, 8, 16, 17, 18, ..., 65536
#   Decimation 1    = 125 MS/s
#   Decimation 1024 = ~122 kS/s
#   Sample rate     = 125 MS/s / decimation
dec = rp.RP_DEC_1024            # Decimation factor

# Trigger parameters
# Available trigger channels (for trigger level):
#   RP_T_CH_1, RP_T_CH_2, RP_T_CH_EXT
trig_channel = rp.RP_T_CH_1    # Trigger level channel

trig_lvl = 0.15                 # Trigger threshold in volts
trig_dly = 0                    # Trigger delay in samples

# Available acquisition trigger sources:
#   RP_TRIG_SRC_DISABLED, RP_TRIG_SRC_NOW, RP_TRIG_SRC_CHA_PE,
#   RP_TRIG_SRC_CHA_NE, RP_TRIG_SRC_CHB_PE, RP_TRIG_SRC_CHB_NE,
#   RP_TRIG_SRC_EXT_PE, RP_TRIG_SRC_EXT_NE, RP_TRIG_SRC_AWG_PE,
#   RP_TRIG_SRC_AWG_NE
acq_trig_sour = rp.RP_TRIG_SRC_CHA_PE

trig_timeout_ms = 4000          # Timeout for trigger interrupt in milliseconds

print("=" * 70)
print("Red Pitaya Interrupt-Based Trigger Timestamp Measurement")
print("=" * 70)
print(f"Generator channel:   {gen_channel}")
print(f"Waveform:            {gen_waveform}")
print(f"Frequency:           {gen_freq} Hz")
print(f"Amplitude:           {gen_ampl} V")
print(f"Burst cycles:        {gen_burst_cycles}")
print(f"Generator period:    {gen_period_s} s")
print()
print(f"Decimation:          {dec}")
print(f"Trigger source:      {acq_trig_sour}")
print(f"Trigger channel:     {trig_channel}")
print(f"Trigger level:       {trig_lvl} V")
print(f"Trigger timeout:     {trig_timeout_ms} ms")
print("NOTE: Connect OUT1 to IN1 for loopback testing")
print("Press Ctrl+C to stop the program")
print("=" * 70)


# ==============================================================================
# GLOBAL STATE - Stop event for thread coordination
# ==============================================================================

stop_event = threading.Event()


def signal_handler(sig, frame):
    """Handle Ctrl+C to gracefully stop all threads."""
    print("\nCtrl+C pressed. Stopping...")
    stop_event.set()


# ==============================================================================
# GENERATOR THREAD - Periodic burst signal generation
# ==============================================================================

def generator_thread():
    """Generator thread - generates periodic trigger signals."""
    print("\nGenerator thread started")

    # Reset and configure generator
    rp.rp_GenReset()
    rp.rp_GenWaveform(gen_channel, gen_waveform)
    rp.rp_GenFreq(gen_channel, gen_freq)
    rp.rp_GenAmp(gen_channel, gen_ampl)
    rp.rp_GenMode(gen_channel, rp.RP_GEN_MODE_BURST)
    rp.rp_GenBurstCount(gen_channel, gen_burst_cycles)
    rp.rp_GenOutEnable(gen_channel)
    print(f"Generator configured: {gen_waveform}, {gen_freq} Hz, {gen_ampl} V, {gen_burst_cycles} cycle burst")

    while not stop_event.is_set():
        rp.rp_GenTriggerOnly(gen_channel)
        print("Generator: signal triggered")
        time.sleep(gen_period_s)

    print("Generator thread stopped")


# ==============================================================================
# ACQUISITION THREAD - Interrupt-based timestamp measurement
# ==============================================================================

def acquisition_thread():
    """Acquisition thread - measures time between triggers using timestamps."""
    print("\nAcquisition thread started")

    # Reset and configure acquisition
    rp.rp_AcqReset()
    rp.rp_AcqSetDecimation(dec)
    rp.rp_AcqSetTriggerDelay(trig_dly)
    rp.rp_AcqSetTriggerLevel(trig_channel, trig_lvl)
    rp.rp_AcqSetInitTimestamp(0)
    print(f"Acquisition configured: decimation={dec}, trigger level={trig_lvl} V")

    prev_timestamp = 0

    while not stop_event.is_set():
        # Start acquisition and set trigger source
        rp.rp_AcqStart()
        rp.rp_AcqSetTriggerSrc(acq_trig_sour)

        # Wait for trigger interrupt
        result = rp.rp_AcqIntTriggerRead(trig_timeout_ms)

        if stop_event.is_set():
            break

        if result == rp.RP_OK:
            # Read hardware timestamp for the trigger event
            ret, cur_timestamp = rp.rp_AcqGetTimestamp(rp.RP_CH_1)

            if ret == rp.RP_OK:
                if prev_timestamp != 0:
                    delta_time = (cur_timestamp - prev_timestamp) / 1e9
                    print(f"Time between triggers: {delta_time:.6f} s")
                else:
                    print("Acquisition: first trigger detected")

                prev_timestamp = cur_timestamp
            else:
                print(f"Error getting timestamp: {rp.rp_GetError(ret)}", file=sys.stderr)
                break

        elif result == rp.RP_ETIM:
            print("Acquisition: trigger timeout", file=sys.stderr)
        else:
            print(f"Acquisition error: {rp.rp_GetError(result)}", file=sys.stderr)
            break

        time.sleep(0.1)

    rp.rp_AcqStop()
    print("Acquisition thread stopped")


# ==============================================================================
# MAIN - Initialize, run threads, and clean up
# ==============================================================================

def main():
    # Set up Ctrl+C handler
    signal.signal(signal.SIGINT, signal_handler)

    # Initialize FPGA overlay and Red Pitaya API
    print("\nInitializing FPGA overlay and Red Pitaya...")
    fpga = overlay()

    if rp.rp_Init() != rp.RP_OK:
        print("API initialization failed!", file=sys.stderr)
        return 1
    print("Red Pitaya initialized")

    print("\nStarting trigger timing measurement...")
    print("Press Ctrl+C to stop\n")

    # Start generator and acquisition threads
    gen = threading.Thread(target=generator_thread)
    acq = threading.Thread(target=acquisition_thread)
    gen.start()
    acq.start()

    # Wait for threads to complete
    gen.join()
    acq.join()

    # ==============================================================================
    # CLEANUP - Release resources
    # ==============================================================================

    print("\nCleaning up...")
    rp.rp_Release()
    print("Resources released - program complete")

    return 0


if __name__ == "__main__":
    sys.exit(main())
