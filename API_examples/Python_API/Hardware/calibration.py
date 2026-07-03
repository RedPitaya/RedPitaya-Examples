#!/usr/bin/python3
"""
Red Pitaya Hardware Calibration Access Example
===============================================

This example demonstrates how to read and inspect hardware calibration parameters
stored in Red Pitaya's EEPROM. Calibration values are critical for accurate
voltage measurements and signal generation. This script shows how to:
- Read calibration IDs and parameters
- Access ADC calibration for low voltage (LV) and high voltage (HV) ranges
- Access DAC calibration for output channels
- Read FPGA filter parameters

IMPORTANT SAFETY NOTES:
=======================
The first part of this script (before DANGER ZONE) is SAFE and only READS
calibration data without making any changes. These operations cannot harm
your Red Pitaya's calibration.

The DANGER ZONE section contains operations that can MODIFY or RESET calibration
data. Incorrect use can result in inaccurate measurements requiring professional
recalibration. Only use DANGER ZONE operations if you:
- Understand calibration procedures
- Have proper calibration equipment
- Have backed up your current calibration
- Know how to restore factory calibration if needed

EEPROM STRUCTURE:
=================
Red Pitaya's EEPROM has two zones:
1. USER ZONE (modifiable) - Contains active calibration used by the system
2. FACTORY ZONE (write-protected) - Contains factory calibration backup

Danger Zone operations only modify the USER ZONE. The FACTORY ZONE remains
write-protected and can always be used to restore original calibration using
the factory reset function. Your factory calibration cannot be permanently lost.

Features (Safe Read-Only Operations):
- Read all calibration parameter IDs
- Display ADC calibration (gain and offset)
- Display DAC calibration (gain and offset)
- Read raw EEPROM calibration data
- Access FPGA filter parameters

Features (DANGER ZONE - Modify Operations):
- Backup and restore calibration settings
- Reset to default or factory calibration
- Manually modify calibration parameters
- Write new calibration to EEPROM

Hardware Requirements:
- Red Pitaya board (STEMlab 125-14 or similar)

Software Requirements:
- Red Pitaya Python API (rp module)
- Red Pitaya Hardware Calibration module (rp_hw_calib)
- OS 2.00 or higher

Usage:
    python calibration.py
    
    By default, only safe read operations are executed.
    DANGER ZONE operations are included but can be commented out.

Author: Red Pitaya
Date: January 2026
"""

import rp
import rp_hw_calib


# ==============================================================================
# SECTION EXECUTION TRACKING
# ==============================================================================
# These flags are set to True after each section completes successfully.
# The summary at the end uses them to report actual execution status.

init_done           = False
calib_ids_read      = False
eeprom_read         = False
adc_lv_read         = False
adc_hv_read         = False
dac_read            = False
raw_adc_read        = False
fpga_filters_read   = False
backup_done         = False
restore_done        = False
reset_done          = False
factory_reset_done  = False
calib_modified      = False
final_restore_done  = False
cleanup_done        = False


# ==============================================================================
# INITIALIZATION - Initialize Red Pitaya and calibration module
# ==============================================================================

print("=" * 70)
print("Red Pitaya Hardware Calibration Access")
print("=" * 70)
print("\nInitializing Red Pitaya and calibration module...")

# Initialize the Red Pitaya interface
rp.rp_Init()
print("Red Pitaya initialized")

# Initialize calibration module
rp_hw_calib.rp_CalibInit()
print("Calibration module initialized")
init_done = True


# ==============================================================================
# CALIBRATION IDs - Read all calibration parameter identifiers
# ==============================================================================

print("\n" + "=" * 70)
print("CALIBRATION PARAMETER IDs")
print("=" * 70)

# Read and display calibration ID numbers (1-64)
for i in range(1, 65, 1):
    id_name = rp_hw_calib.rp_GetNameOfUniversalId(i)[1]
    print(f"ID {i:2d}: {id_name}")
calib_ids_read = True


# ==============================================================================
# RAW EEPROM DATA - Read calibration data directly from EEPROM
# ==============================================================================

print("\n" + "=" * 70)
print("RAW EEPROM CALIBRATION DATA")
print("=" * 70)

# Reading calibration data directly from EEPROM
raw_data = rp_hw_calib.rp_CalibGetEEPROM(False)
print(f"\nEEPROM data pointer: {raw_data}")

# Convert pointer to array and display hex values
data_arr = rp_hw_calib.uint8Arr.frompointer(raw_data[1])

print(f"EEPROM data ({raw_data[2]} bytes):")
for n in range(raw_data[2]):
    if n >= raw_data[2]-1:
        print(hex(data_arr[n]), end="")
    else:
        print(hex(data_arr[n]), end=",")
    if (n + 1) % 16 == 0:  # Line break every 16 bytes
        print()
print("\n")
eeprom_read = True


# ==============================================================================
# ADC CALIBRATION - Low Voltage (LV) Range
# ==============================================================================

print("=" * 70)
print("ADC CALIBRATION - LOW VOLTAGE (LV) RANGE (±1V)")
print("=" * 70)

# Channel 1 LV calibration
ch1_lv_calib = rp_hw_calib.rp_CalibGetFastADCCalibValue(0, 0)  # Channel, AC/DC mode
print("\nIN1 (LV Range):")
print(f"  Gain:   {ch1_lv_calib[1]}")
print(f"  Offset: {ch1_lv_calib[2]}")

# Channel 2 LV calibration
ch2_lv_calib = rp_hw_calib.rp_CalibGetFastADCCalibValue(1, 0)  # Channel, AC/DC mode
print("\nIN2 (LV Range):")
print(f"  Gain:   {ch2_lv_calib[1]}")
print(f"  Offset: {ch2_lv_calib[2]}")
adc_lv_read = True


# ==============================================================================
# ADC CALIBRATION - High Voltage (HV) Range
# ==============================================================================

print("\n" + "=" * 70)
print("ADC CALIBRATION - HIGH VOLTAGE (HV) RANGE (±20V)")
print("=" * 70)

# Channel 1 HV calibration
ch1_hv_calib = rp_hw_calib.rp_CalibGetFastADCCalibValue_1_20(0, 0)  # Channel, AC/DC mode
print("\nIN1 (HV Range):")
print(f"  Gain:   {ch1_hv_calib[1]}")
print(f"  Offset: {ch1_hv_calib[2]}")

# Channel 2 HV calibration
ch2_hv_calib = rp_hw_calib.rp_CalibGetFastADCCalibValue_1_20(1, 0)  # Channel, AC/DC mode
print("\nIN2 (HV Range):")
print(f"  Gain:   {ch2_hv_calib[1]}")
print(f"  Offset: {ch2_hv_calib[2]}")
adc_hv_read = True


# ==============================================================================
# DAC CALIBRATION - Output Channels
# ==============================================================================

print("\n" + "=" * 70)
print("DAC CALIBRATION - OUTPUT CHANNELS")
print("=" * 70)

# OUT1 calibration
out1_calib = rp_hw_calib.rp_CalibGetFastDACCalibValue(0, 0)  # Channel, Generator gain mode
print("\nOUT1:")
print(f"  Gain:   {out1_calib[1]}")
print(f"  Offset: {out1_calib[2]}")

# OUT2 calibration
out2_calib = rp_hw_calib.rp_CalibGetFastDACCalibValue(1, 0)  # Channel, Generator gain mode
print("\nOUT2:")
print(f"  Gain:   {out2_calib[1]}")
print(f"  Offset: {out2_calib[2]}")
dac_read = True


# ==============================================================================
# RAW ADC CALIBRATION - Detailed Parameters
# ==============================================================================

print("\n" + "=" * 70)
print("RAW ADC CALIBRATION - DETAILED PARAMETERS")
print("=" * 70)

# Get detailed calibration structure
t = rp_hw_calib.new_p_uint_gain_calib_t()
res = rp_hw_calib.rp_CalibGetFastADCCalibValueI(0, 0, t)  # Channel, AC/DC mode, array

print("\nIN1 (LV Range) - Raw Parameters:")
print(f"  Gain:      {t.gain}")
print(f"  Base:      {t.base}")
print(f"  Precision: {t.precision}")
print(f"  Offset:    {t.offset}")
raw_adc_read = True


# ==============================================================================
# FPGA FILTER PARAMETERS - ADC Input Filters
# ==============================================================================

print("\n" + "=" * 70)
print("FPGA FILTER PARAMETERS - ADC INPUT FILTERS")
print("=" * 70)

# Allocate filter parameter structure
t = rp_hw_calib.new_p_channel_filter_t()

# Channel 1 LV FPGA filter
rp_hw_calib.rp_CalibGetFastADCFilter(0, t)  # Channel, array
print("\nIN1 (LV Range) FPGA Filter:")
print(f"  AA (coefficient): {t.aa}")
print(f"  BB (coefficient): {t.bb}")
print(f"  PP (coefficient): {t.pp}")
print(f"  KK (coefficient): {t.kk}")

# Channel 1 HV FPGA filter
rp_hw_calib.rp_CalibGetFastADCFilter_1_20(0, t)
print("\nIN1 (HV Range) FPGA Filter:")
print(f"  AA (coefficient): {t.aa}")
print(f"  BB (coefficient): {t.bb}")
print(f"  PP (coefficient): {t.pp}")
print(f"  KK (coefficient): {t.kk}")
fpga_filters_read = True


print("\n" + "=" * 70)
print("SAFE READ-ONLY OPERATIONS COMPLETED")
print("All calibration data has been read and displayed")
print("No changes have been made to your Red Pitaya's calibration")
print("=" * 70)


# ##############################################################################
# ##############################################################################
# ###                                                                        ###
# ###   !!  !!  !!        DANGER ZONE - READ CAREFULLY        !!  !!  !!    ###
# ###                                                                        ###
# ##############################################################################
# ##############################################################################
#
# !!  WARNING: THE OPERATIONS BELOW CAN MODIFY OR RESET CALIBRATION DATA  !!
#
# The following code sections demonstrate operations that can PERMANENTLY
# MODIFY your Red Pitaya's calibration settings stored in EEPROM.
#
# EEPROM CALIBRATION ZONES:
# ==========================
# Red Pitaya's EEPROM contains TWO calibration zones:
#
# 1. USER ZONE (modifiable)
#    - This is the active calibration used by the system
#    - Modified by the operations below
#    - Can be customized for specific applications
#
# 2. FACTORY ZONE (write-protected)
#    - Contains original factory calibration
#    - Cannot be modified or erased
#    - Always available for restoration
#
# IMPORTANT: The factory calibration is PERMANENTLY PRESERVED in the write-
# protected factory zone. You can always restore factory calibration using
# rp_CalibrationFactoryReset(), even if user calibration is corrupted.
#
# RISKS OF INCORRECT USE:
# ========================
# - Inaccurate voltage measurements on input channels
# - Incorrect output voltages on generator channels
# - Requires professional recalibration equipment to fix user calibration
# - Factory calibration is ALWAYS safe and can be restored
#
# ONLY PROCEED IF YOU:
# ====================
# [X] Have proper calibration equipment (precision voltage sources, DMM)
# [X] Understand Red Pitaya calibration procedures
# [X] Have documented your current calibration values
# [X] Know how to perform manual calibration
# [X] Are prepared to contact Red Pitaya support if needed
#
# RECOMMENDED SAFETY MEASURES:
# ============================
# 1. ALWAYS backup calibration before making changes
# 2. Test changes on non-critical Red Pitaya first
# 3. Remember: Factory calibration can ALWAYS be restored
# 4. Document all changes you make
#
# BY DEFAULT, DANGER ZONE OPERATIONS ARE COMMENTED OUT FOR SAFETY
#
# ##############################################################################

print("\n\n" + "!" * 70)
print("!!  DANGER ZONE: Calibration Modification Operations  !!")
print("!" * 70)
print("\n!!  The following operations are COMMENTED OUT by default for safety.")
print("!!  Uncomment only if you understand calibration procedures.")
print("!!  Incorrect use can damage your Red Pitaya's calibration.")
print("\n" + "=" * 70)


# ==============================================================================
# BACKUP CALIBRATION - Save Current Settings (SAFE)
# ==============================================================================

print("\n" + "-" * 70)
print("BACKUP: Saving current calibration settings to memory")
print("-" * 70)

# Backup calibration data (SAFE - only reads current settings)
current_settings = rp_hw_calib.rp_GetCalibrationSettings()
print("[OK] Current calibration backed up to 'current_settings' variable")
print("     (This backup is only in memory - lost when program exits)")
backup_done = True


# ==============================================================================
# !!  DANGER: RESTORE CALIBRATION FROM BACKUP
# ==============================================================================
# UNCOMMENT THE FOLLOWING SECTION TO ENABLE (USE WITH CAUTION!)

# print("\n" + "-" * 70)
# print("!!  DANGER: Restoring calibration from backup")
# print("-" * 70)
# 
# # Restore calibration data from backup
# rp_hw_calib.rp_CalibrationWriteParams(current_settings, False)
# print("[OK] Calibration restored from backup and written to EEPROM")
# restore_done = True


# ==============================================================================
# !!  DANGER: RESET CALIBRATION
# ==============================================================================
# UNCOMMENT THE FOLLOWING SECTION TO ENABLE (USE WITH EXTREME CAUTION!)

# print("\n" + "-" * 70)
# print("!!  DANGER: Resetting calibration to default values")
# print("-" * 70)
# 
# # Reset to default values (all gains = 1.0, all offsets = 0)
# rp_hw_calib.rp_CalibrationReset(False, False)
# print("[OK] Calibration reset to default values (Gain=1.0, Offset=0)")
# print("!!  Your Red Pitaya will now have UNCALIBRATED measurements!")
# reset_done = True
# 
# # Verify reset values
# ch1_lv_calib = rp_hw_calib.rp_CalibGetFastADCCalibValue(0, 0)
# ch2_lv_calib = rp_hw_calib.rp_CalibGetFastADCCalibValue(1, 0)
# 
# print(f"\nVerifying reset values:")
# print(f"  IN1 (LV): Gain = {ch1_lv_calib[1]}, Offset = {ch1_lv_calib[2]}")
# print(f"  IN2 (LV): Gain = {ch2_lv_calib[1]}, Offset = {ch2_lv_calib[2]}")


# ==============================================================================
# !!  DANGER: FACTORY RESET CALIBRATION
# ==============================================================================
# UNCOMMENT THE FOLLOWING SECTION TO ENABLE (USE WITH EXTREME CAUTION!)

# print("\n" + "-" * 70)
# print("!!  DANGER: Resetting to factory calibration")
# print("-" * 70)
# 
# # Reset to factory calibration (restores calibration done at factory)
# rp_hw_calib.rp_CalibrationFactoryReset(False)
# print("[OK] Calibration restored to factory settings")
# print("     (Only works if factory calibration is still stored in EEPROM)")
# factory_reset_done = True


# ==============================================================================
# !!  DANGER: MODIFY CALIBRATION PARAMETERS
# ==============================================================================
# UNCOMMENT THE FOLLOWING SECTION TO ENABLE (USE WITH EXTREME CAUTION!)

# print("\n" + "-" * 70)
# print("!!  DANGER: Modifying calibration parameters")
# print("-" * 70)
# 
# # Get current calibration settings
# rp_calib = rp_hw_calib.rp_GetCalibrationSettings()
# 
# # Access individual channel calibration
# calib_1 = rp_hw_calib.cCalibArr_getitem(rp_calib.fast_adc_1_1, 0)  # Channel 1
# calib_2 = rp_hw_calib.cCalibArr_getitem(rp_calib.fast_adc_1_1, 1)  # Channel 2
# 
# print(f"Current IN1 gain (calculated): {calib_1.gainCalc}")
# print(f"Current IN2 gain (calculated): {calib_2.gainCalc}")
# 
# # Save original values for restoration
# calib_1_temp_gC = calib_1.gainCalc
# calib_2_temp_gC = calib_2.gainCalc
# 
# # !!  MODIFY calibration values (EXAMPLE: DO NOT USE THESE VALUES!)
# print("\n!!  Setting new calibration values (EXAMPLE ONLY)...")
# calib_1.gainCalc = 1.1  # !!  Example value - DO NOT USE without proper calibration!
# calib_2.gainCalc = 1.1  # !!  Example value - DO NOT USE without proper calibration!
# 
# # Write modified values to calibration structure
# rp_hw_calib.cCalibArr_setitem(rp_calib.fast_adc_1_1, 0, calib_1)
# rp_hw_calib.cCalibArr_setitem(rp_calib.fast_adc_1_1, 1, calib_2)
# 
# # !!  WRITE calibration data to EEPROM (PERMANENT CHANGE!)
# print("!!  Writing modified calibration to EEPROM...")
# rp_hw_calib.rp_CalibrationWriteParams(rp_calib, False)
# print("[OK] New calibration written to EEPROM")
# 
# # Set parameters into temporary memory
# rp_hw_calib.rp_CalibrationSetParams(rp_calib)
# rp_calib1 = rp_hw_calib.rp_GetCalibrationSettings()
# 
# # Print calibration structure
# print("\nCalibration structure:")
# print(rp_hw_calib.rp_CalibPrint(rp_calib1))
# 
# # Read back and verify new values
# rp_calib = rp_hw_calib.rp_GetCalibrationSettings()
# calib_1 = rp_hw_calib.cCalibArr_getitem(rp_calib.fast_adc_1_1, 0)
# calib_2 = rp_hw_calib.cCalibArr_getitem(rp_calib.fast_adc_1_1, 1)
# 
# print(f"\nVerifying modified values:")
# print(f"  New IN1 gain: {calib_1.gainCalc}")
# print(f"  New IN2 gain: {calib_2.gainCalc}")
# 
# # !!  RESTORE original parameters (RECOMMENDED IN EXAMPLE CODE!)
# print("\n!!  Restoring original calibration values...")
# calib_1.gainCalc = calib_1_temp_gC
# calib_2.gainCalc = calib_2_temp_gC
# 
# rp_hw_calib.cCalibArr_setitem(rp_calib.fast_adc_1_1, 0, calib_1)
# rp_hw_calib.cCalibArr_setitem(rp_calib.fast_adc_1_1, 1, calib_2)
# 
# rp_hw_calib.rp_CalibrationWriteParams(rp_calib, False)
# print("[OK] Original calibration restored")
# calib_modified = True
# 
# # Verify restoration
# rp_calib = rp_hw_calib.rp_GetCalibrationSettings()
# calib_1 = rp_hw_calib.cCalibArr_getitem(rp_calib.fast_adc_1_1, 0)
# calib_2 = rp_hw_calib.cCalibArr_getitem(rp_calib.fast_adc_1_1, 1)
# 
# print(f"\nVerifying restored values:")
# print(f"  Restored IN1 gain: {calib_1.gainCalc}")
# print(f"  Restored IN2 gain: {calib_2.gainCalc}")


# ==============================================================================
# !!  DANGER: FINAL RESTORE FROM BACKUP
# ==============================================================================
# UNCOMMENT THE FOLLOWING SECTION TO ENABLE

# print("\n" + "-" * 70)
# print("!!  DANGER: Final restore from initial backup")
# print("-" * 70)
# 
# # Restore settings from the backup made at the beginning
# rp_hw_calib.rp_CalibrationWriteParams(current_settings, False)
# print("[OK] Calibration fully restored from initial backup")
# final_restore_done = True


print("\n" + "=" * 70)
print("DANGER ZONE SECTION COMPLETE")
print("All dangerous operations are commented out by default")
print("=" * 70)

# ##############################################################################
# ###                      END OF DANGER ZONE                                ###
# ##############################################################################


# ==============================================================================
# CLEANUP - Release resources
# ==============================================================================

print("\n" + "=" * 70)
print("CLEANUP - Releasing resources")
print("=" * 70)

# Release Red Pitaya resources
rp.rp_Release()
cleanup_done = True
print("[OK] Red Pitaya resources released")

print("\n" + "=" * 70)
print("Program completed successfully")
print("=" * 70)
print("\nSUMMARY:")

def _status(flag):
    return "[OK]" if flag else "[--]"

print(f"  {_status(init_done)}          Initialization")
print(f"  {_status(calib_ids_read)}     Calibration IDs read")
print(f"  {_status(eeprom_read)}        Raw EEPROM data read")
print(f"  {_status(adc_lv_read)}        ADC LV calibration read")
print(f"  {_status(adc_hv_read)}        ADC HV calibration read")
print(f"  {_status(dac_read)}           DAC calibration read")
print(f"  {_status(raw_adc_read)}       Raw ADC calibration read")
print(f"  {_status(fpga_filters_read)}  FPGA filter parameters read")
print(f"  {_status(backup_done)}        Calibration backed up")
print(f"  {_status(restore_done)}       Calibration restored from backup")
print(f"  {_status(reset_done)}         Calibration reset to defaults")
print(f"  {_status(factory_reset_done)} Factory reset performed")
print(f"  {_status(calib_modified)}     Calibration parameters modified")
print(f"  {_status(final_restore_done)} Final restore from backup")
print(f"  {_status(cleanup_done)}       Resources released")

if not any([restore_done, reset_done, factory_reset_done, calib_modified, final_restore_done]):
    print("\n  No changes were made to your Red Pitaya's calibration.")
else:
    print("\n  !!  Calibration was modified during this session.")

print("\nTo use DANGER ZONE operations:")
print("  1. READ ALL WARNINGS CAREFULLY")
print("  2. Ensure you have proper calibration equipment")
print("  3. Uncomment only the specific sections you need")
print("  4. Test on non-critical equipment first")
print("=" * 70)
