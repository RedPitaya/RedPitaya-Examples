#!/usr/bin/python3
"""
Red Pitaya Multiboard Example - Daisy Chain Synchronization with Click Shield
==============================================================================

This example demonstrates synchronized acquisition and generation across multiple
Red Pitaya boards using the Click Shield daisy chain functionality. The Click Shield
enables precise clock and trigger synchronization between multiple boards, allowing
for multi-channel measurements and coordinated signal generation.

Features:
- Clock synchronization between boards via Click Shield
- Trigger synchronization for coordinated measurements
- Primary board controls generation and triggers secondary acquisition
- Secondary board uses external trigger from primary
- Synchronized data acquisition across both boards
- LED indicators for visual status confirmation

Hardware Requirements:
- 2x Red Pitaya boards (STEMlab 125-14 or similar)
- Click Shield board with daisy chain connectors
- Proper cables connecting the boards via Click Shield

Required Connections:
=====================
Primary Board (Control Unit):
  - Connect Click Shield to primary board
  - DIO0_N pin configured as trigger output
  - LED5 used as status indicator

Secondary Board (Follower Unit):
  - Connect Click Shield to secondary board
  - DIO0_N pin configured to receive trigger
  - LED5 used as status indicator
  - Trigger source set to external negative edge (EXT_NE)

Click Shield Connections:
  - Clock synchronization via SATA connector
  - Trigger synchronization via SATA connector
  - Connect boards in daisy chain configuration

Software Requirements:
- Red Pitaya Python API (rp module)
- NumPy library
- OS 2.00 or higher

Usage:
    # Run the entire script to execute both primary and secondary code
    python multi_1_click_shield.py
    
    The program will:
    1. Configure and run primary board (control unit)
    2. Primary generates waveform and triggers acquisition
    3. Primary sends trigger signal via DIO0_N
    4. Configure and run secondary board (follower unit)
    5. Secondary waits for external trigger
    6. Both boards acquire data synchronously
    7. Display acquired data from both boards

Configuration:
    Modify the CONFIGURATION sections to customize:
    - Signal generation parameters (waveform, frequency, amplitude)
    - Acquisition parameters (decimation, trigger level, delay)
    - Buffer size and data processing
    - Channel selection

Note:
    This example shows the code for both boards sequentially. In a real setup,
    you would run the primary code on one board and the secondary code on another.
    Alternatively, use SSH connections to each board and run them separately.

Important:
    - Ensure proper Click Shield connections before running
    - Primary board must be initialized first
    - Both boards must have clock sync enabled
    - Trigger sync must be enabled on both boards
    - Check LED5 on both boards lights up to confirm proper initialization

Author: Red Pitaya
Date: January 2026
"""

import time
import numpy as np
import rp

# ==============================================================================
# BOARD SELECTION
# ==============================================================================
# Set this variable before running to select which board's code to execute:
#   "primary"   - Run on the primary (control) board
#   "secondary" - Run on the secondary (follower) board
board = "primary"


if board == "primary":
    # ==============================================================================
    # PRIMARY BOARD - CONTROL UNIT CODE
    # ==============================================================================

    print("=" * 70)
    print("Red Pitaya Multiboard - Primary Board (Control Unit)")
    print("=" * 70)


    # ==============================================================================
    # CONFIGURATION - Primary Board Settings
    # ==============================================================================

    # Generation settings
    channel = rp.RP_CH_1                        # Output channel: rp.RP_CH_1, rp.RP_CH_2
    waveform = rp.RP_WAVEFORM_SINE              # Waveform type: SINE, SQUARE, TRIANGLE, etc.
    freq = 100000                               # Frequency in Hz (100 kHz)
    ampl = 1.0                                  # Amplitude in Volts (peak)

    # Acquisition settings
    trig_lvl = 0.5                              # Trigger level in Volts
    trig_dly = 0                                # Trigger delay in samples
    dec = 1                                     # Decimation factor (1, 2, 4, 8, 16, 32, 64, ...)

    # Trigger sources
    gen_trig_sour = rp.RP_GEN_TRIG_SRC_INTERNAL # Generator trigger: INTERNAL, EXT_PE, EXT_NE
    acq_trig_sour = rp.RP_TRIG_SRC_CHA_PE       # Acquisition trigger: CHA_PE, CHA_NE, CHB_PE, CHB_NE, EXT_PE, EXT_NE

    # Data buffer
    buff_len = 16384                            # Buffer length (max 16384)
    data_V_prim = np.zeros(buff_len, dtype=float)

    print("\nPrimary Board Configuration:")
    print(f"  Generation channel:    {channel}")
    print(f"  Waveform:              {waveform}")
    print(f"  Frequency:             {freq} Hz ({freq/1000:.1f} kHz)")
    print(f"  Amplitude:             {ampl} V")
    print(f"  Trigger level:         {trig_lvl} V")
    print(f"  Trigger delay:         {trig_dly} samples")
    print(f"  Decimation:            {dec}")
    print(f"  Buffer length:         {buff_len} samples")
    print(f"  Generator trigger:     {gen_trig_sour}")
    print(f"  Acquisition trigger:   {acq_trig_sour}")


    # ==============================================================================
    # INITIALIZATION - Primary Board
    # ==============================================================================

    print("\n" + "=" * 70)
    print("Initializing Primary Board...")
    print("=" * 70)

    # Initialize the interface
    rp.rp_Init()

    # Reset Generation and Acquisition
    rp.rp_GenReset()
    rp.rp_AcqReset()

    ###### Enable Daisy Chain #####
    rp.rp_SetEnableDiasyChainClockSync(True)        # Sync Clock
    rp.rp_SetEnableDaisyChainTrigSync(True)         # Sync Trigger
    rp.rp_SetDpinEnableTrigOutput(True)             # Enable trigger output on DIO0_N

    # Choose which trigger to synchronise (rp.OUT_TR_ADC, rp.OUT_TR_DAC)
    rp.rp_SetSourceTrigOutput(rp.OUT_TR_ADC)

    # LED indicator
    rp.rp_DpinSetState(rp.RP_LED5, rp.RP_HIGH)


    ###### Generation #####

    print("Gen_start")
    rp.rp_GenWaveform(channel, waveform)
    rp.rp_GenFreqDirect(channel, freq)
    rp.rp_GenAmp(channel, ampl)

    rp.rp_GenTriggerSource(channel, gen_trig_sour)
    rp.rp_GenOutEnable(channel)

    ##### Acquisition #####
    rp.rp_AcqSetDecimationFactor(dec)


    # Set trigger level and delay
    rp.rp_AcqSetTriggerLevel(rp.RP_T_CH_1, trig_lvl)
    rp.rp_AcqSetTriggerDelay(trig_dly)

    # Start Acquisition
    print("Acq_start")
    rp.rp_AcqStart()

    # Specify trigger - input 1 positive edge
    rp.rp_AcqSetTriggerSrc(acq_trig_sour)

    rp.rp_GenTriggerOnly(channel)       # Trigger generator

    # Trigger state
    while 1:
        trig_state = rp.rp_AcqGetTriggerState()[1]
        if trig_state == rp.RP_TRIG_STATE_TRIGGERED:
            break

    # Fill state
    print(f"Fill state: {rp.rp_AcqGetBufferFillState()}")

    while 1:
        if rp.rp_AcqGetBufferFillState()[1]:
            break


    ### Get data ###
    # Volts
    res = rp.rp_AcqGetDataVNP(rp.RP_CH_1, 0, buff_len, data_V_prim)

    print(f"Data in Volts: {data_V_prim}")


    # Release resources
    rp.rp_Release()



if board == "secondary":
    # ==============================================================================
    # SECONDARY BOARD - FOLLOWER UNIT CODE
    # ==============================================================================

    print("\n\n")
    print("=" * 70)
    print("Red Pitaya Multiboard - Secondary Board (Follower Unit)")
    print("=" * 70)


    # ==============================================================================
    # CONFIGURATION - Secondary Board Settings
    # ==============================================================================

    # Acquisition settings
    trig_lvl = 0.5                              # Trigger level in Volts (not used for EXT trigger)
    trig_dly = 0                                # Trigger delay in samples
    dec = 1                                     # Decimation factor (1, 2, 4, 8, 16, 32, 64, ...)

    # Data buffer
    buff_len = 16384                            # Buffer length (max 16384)
    data_V_sec = np.zeros(buff_len, dtype=float)

    print("\nSecondary Board Configuration:")
    print(f"  Trigger delay:         {trig_dly} samples")
    print(f"  Decimation:            {dec}")
    print(f"  Buffer length:         {buff_len} samples")
    print(f"  Acquisition trigger:   External Negative Edge (EXT_NE)")


    # ==============================================================================
    # INITIALIZATION - Secondary Board
    # ==============================================================================

    print("\n" + "=" * 70)
    print("Initializing Secondary Board...")
    print("=" * 70)

    # Initialize the interface
    rp.rp_Init()
    print("Red Pitaya API initialized")

    # Reset Generation and Acquisition
    rp.rp_GenReset()
    rp.rp_AcqReset()
    print("Generator and acquisition modules reset")


    # ==============================================================================
    # DAISY CHAIN SETUP - Secondary Board (Follower Unit)
    # ==============================================================================

    print("\nConfiguring Daisy Chain (Secondary Board as Follower Unit)...")

    # Enable clock synchronization via Click Shield
    rp.rp_SetEnableDiasyChainClockSync(True)
    print("  Clock synchronization:     Enabled")

    # Enable trigger synchronization via Click Shield
    rp.rp_SetEnableDaisyChainTrigSync(True)
    print("  Trigger synchronization:   Enabled")

    # Enable trigger output on DIO0_N pin (for potential daisy chain extension)
    rp.rp_SetDpinEnableTrigOutput(True)
    print("  Trigger output (DIO0_N):   Enabled")

    # Choose which trigger to synchronize - ADC trigger in this example
    # Options: rp.OUT_TR_ADC (acquisition trigger), rp.OUT_TR_DAC (generator trigger)
    rp.rp_SetSourceTrigOutput(rp.OUT_TR_ADC)
    print("  Trigger source:            ADC trigger")

    # Turn on LED5 as visual indicator that daisy chain is active
    rp.rp_DpinSetState(rp.RP_LED5, rp.RP_HIGH)
    print("  Status LED (LED5):         ON")


    # ==============================================================================
    # ACQUISITION SETUP - Secondary Board
    # ==============================================================================

    print("\n" + "=" * 70)
    print("Configuring Acquisition...")
    print("=" * 70)

    # Set decimation factor
    rp.rp_AcqSetDecimationFactor(dec)
    print(f"Decimation factor: {dec}")

    # Set trigger delay
    rp.rp_AcqSetTriggerDelay(trig_dly)
    print(f"Trigger delay: {trig_dly} samples")

    # Start acquisition
    rp.rp_AcqStart()
    print("Acquisition started")

    # IMPORTANT: Secondary board must use external trigger (EXT_NE)
    # This receives the trigger from primary board via DIO0_N through Click Shield
    rp.rp_AcqSetTriggerSrc(rp.RP_TRIG_SRC_EXT_NE)
    print("Acquisition trigger source: External Negative Edge (EXT_NE)")


    # ==============================================================================
    # TRIGGER AND DATA ACQUISITION - Secondary Board
    # ==============================================================================

    print("\n" + "=" * 70)
    print("Waiting for External Trigger from Primary Board...")
    print("=" * 70)

    # Wait for trigger event from primary board
    print("Waiting for trigger...")
    while True:
        trig_state = rp.rp_AcqGetTriggerState()[1]
        if trig_state == rp.RP_TRIG_STATE_TRIGGERED:
            print("Trigger detected!")
            break

    # Wait for buffer to fill
    print("Waiting for buffer to fill...")
    while True:
        fill_state = rp.rp_AcqGetBufferFillState()[1]
        if fill_state:
            print("Buffer filled!")
            break


    # ==============================================================================
    # DATA RETRIEVAL - Secondary Board
    # ==============================================================================

    print("\n" + "=" * 70)
    print("Retrieving Data from Secondary Board...")
    print("=" * 70)

    # Get data in Volts
    res = rp.rp_AcqGetDataV(rp.RP_CH_1, 0, buff_len, data_V_sec)
    print(f"Retrieved {buff_len} samples")
    print(f"First 10 samples (V): {data_V_sec[:10]}")
    print(f"Data range: {np.min(data_V_sec):.3f} V to {np.max(data_V_sec):.3f} V")


    # ==============================================================================
    # CLEANUP - Secondary Board
    # ==============================================================================

    print("\n" + "=" * 70)
    print("Releasing Secondary Board Resources...")
    print("=" * 70)

    # Release resources
    rp.rp_Release()
    print("Secondary board resources released")


# ==============================================================================
# SUMMARY
# ==============================================================================
print("\n" + "=" * 70)
print("Multiboard Acquisition Complete!")
print("=" * 70)

print("\nBoth boards have successfully acquired synchronized data.")
print("Primary board generated the signal and trigger.")
print("Secondary board received the external trigger and acquired data.")
print("\nData from both boards is now available for analysis.")
print("=" * 70)

