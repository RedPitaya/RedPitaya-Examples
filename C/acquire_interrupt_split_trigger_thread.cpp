/* Red Pitaya C++ API example for acquiring data from all 4 channels in split
 * trigger mode with per-channel threads and multiple acquisitions */

#include "rp.h"
#include "rp_hw-profiles.h"
#include "rp_hw_calib.h"
#include <algorithm>
#include <chrono>
#include <iomanip>
#include <iostream>
#include <mutex>
#include <random>
#include <sstream>
#include <thread>
#include <vector>

#define MAX_NUM 4
#define BUFF_SIZE 6001
#define TIMEOUT_MS 3000
#define ACQUISITIONS_PER_CHANNEL 5 // Number of acquisitions per channel

using namespace std;

/* ============================================================ */
/* CHANNEL CONFIGURATION STRUCTURE */
/* ============================================================ */

struct ChannelConfig {
  int channel_num;           // Channel number: 1, 2, 3, 4
  rp_channel_t ch;           // Red Pitaya channel handle
  rp_channel_trigger_t trig; // Trigger channel
  uint32_t decimation;       // Decimation factor
  float trig_lvl;            // Trigger level in Volts
  int trig_dly;              // Trigger delay
  rp_acq_trig_src_t src;     // Trigger source
  uint32_t trig_pos;         // Trigger position in buffer
  vector<float> data;        // Acquired data buffer
  int acquisition_count;     // Number of successful acquisitions

  ChannelConfig() : channel_num(0), trig_pos(0), acquisition_count(0) {
    data.resize(BUFF_SIZE);
  }
};

/* ============================================================ */
/* RED PITAYA INITIALIZATION */
/* ============================================================ */

/**
 * Initialize Red Pitaya hardware and enable split trigger mode
 * Initialization ends with rp_AcqSetSplitTrigger(true)
 * Returns true on success, false on failure
 */
bool initRedPitaya() {
  if (rp_InitReset(false) != RP_OK) {
    cerr << "RP init failed!" << endl;
    return false;
  }

  if (rp_CalibInit() != RP_HW_CALIB_OK) {
    cerr << "Calibration failed!" << endl;
    return false;
  }

  rp_AcqReset();
  rp_AcqSetSplitTrigger(true); // <-- INITIALIZATION ENDS HERE

  return true;
}

/* ============================================================ */
/* THREAD-SAFE PRINT FUNCTION */
/* ============================================================ */

/**
 * Thread-safe print function using variadic templates
 * Automatically locks mutex and appends newline
 */
template <typename... Args> void safePrint(mutex &cout_mutex, Args... args) {
  lock_guard<mutex> lock(cout_mutex);
  ((cout << args), ...); // C++17 fold expression
  cout << endl;
}

/* ============================================================ */
/* PER-CHANNEL THREAD FUNCTION */
/* ============================================================ */

/**
 * Thread function for a single channel
 * Each thread performs: configuration -> multiple acquisitions -> output
 */
void channelThread(ChannelConfig &cfg, int thread_id, mutex &cout_mutex) {
  // ============================================================
  // STEP 1: CHANNEL CONFIGURATION (done once)
  // ============================================================

  safePrint(cout_mutex, "[THREAD ", thread_id, "] Configuring channel ",
            cfg.channel_num);

  // Disable interrupt for trigger point
  rp_AcqSetIntMaskCh(cfg.ch, RP_INT_TRIGGER, false);

  // Reset channel
  rp_AcqResetCh(cfg.ch);

  // Set decimation factor
  rp_AcqSetDecimationFactorCh(cfg.ch, cfg.decimation);

  // Set gain to low range
  rp_AcqSetGain(cfg.ch, RP_LOW);

  // Set trigger level
  rp_AcqSetTriggerLevel(cfg.trig, cfg.trig_lvl);

  // Set trigger delay
  rp_AcqSetTriggerDelayCh(cfg.ch, cfg.trig_dly);

  safePrint(cout_mutex, "[THREAD ", thread_id, "] Channel ", cfg.channel_num,
            " configured");

  // ============================================================
  // STEP 2: MULTIPLE DATA ACQUISITIONS
  // ============================================================

  for (int acq = 0; acq < ACQUISITIONS_PER_CHANNEL; acq++) {
    // --------------------------------------------------------
    // 2a. START ACQUISITION AND SET TRIGGER SOURCE
    // --------------------------------------------------------

    // Start acquisition on channel
    rp_AcqStartCh(cfg.ch);

    // Set trigger source for channel
    rp_AcqSetTriggerSrcCh(cfg.ch, cfg.src);

    // --------------------------------------------------------
    // 2b. WAIT FOR TRIGGER
    // --------------------------------------------------------

    safePrint(cout_mutex, "[THREAD ", thread_id, "] Acquisition ", acq + 1,
              ": Waiting for trigger on channel ", cfg.channel_num);

    // Wait for trigger and buffer full (timeout in ms)
    auto ret = rp_AcqIntFillReadCh(cfg.ch, TIMEOUT_MS);

    // Check if trigger was successful
    if (ret != RP_OK) {
      safePrint(cout_mutex, "[THREAD ", thread_id, "] Acquisition ", acq + 1,
                ": Channel ", cfg.channel_num,
                " trigger failed! Error: ", rp_GetError(ret));
      continue; // Skip this acquisition attempt
    }

    safePrint(cout_mutex, "[THREAD ", thread_id, "] Acquisition ", acq + 1,
              ": Channel ", cfg.channel_num, " triggered, ret = ", ret);

    // Check if trigger was successful
    if (ret != RP_OK) {
      safePrint(cout_mutex, "[THREAD ", thread_id, "] Acquisition ", acq + 1,
                ": Channel ", cfg.channel_num, " trigger failed!");
      continue; // Skip this acquisition attempt
    }

    // --------------------------------------------------------
    // 2c. ACQUIRE DATA
    // --------------------------------------------------------

    safePrint(cout_mutex, "[THREAD ", thread_id, "] Acquisition ", acq + 1,
              ": Acquiring data from channel ", cfg.channel_num);

    // Get trigger position in buffer
    rp_AcqGetWritePointerAtTrigCh(cfg.ch, &cfg.trig_pos);

    safePrint(cout_mutex, "[THREAD ", thread_id, "] Acquisition ", acq + 1,
              ": Channel ", cfg.channel_num, " trig pos = ", cfg.trig_pos);

    // Read data from buffer starting at trigger position
    uint32_t size = BUFF_SIZE;
    rp_AcqGetDataV(cfg.ch, cfg.trig_pos, &size, cfg.data.data());

    // Increment acquisition counter
    cfg.acquisition_count++;

    safePrint(cout_mutex, "[THREAD ", thread_id, "] Acquisition ", acq + 1,
              ": Channel ", cfg.channel_num, " data acquired (", size,
              " samples)");

    // --------------------------------------------------------
    // 2d. OUTPUT DATA
    // --------------------------------------------------------

    {
      lock_guard<mutex> lock(cout_mutex);
      cout << "[THREAD " << thread_id << "] Acquisition " << acq + 1
           << ": Channel " << cfg.channel_num << " data:" << endl;

      // Print only first 20 samples for brevity
      int print_samples = min(20, (int)cfg.data.size());
      cout << fixed << setprecision(3);
      for (int j = 0; j < print_samples; j++) {
        cout << cfg.data[j];
        if (j < print_samples - 1)
          cout << ", ";
      }
      cout << endl << endl;
    }

    // Small delay between acquisitions to allow hardware to settle
    this_thread::sleep_for(chrono::milliseconds(100));
  }

  // ============================================================
  // STEP 3: COMPLETION SUMMARY
  // ============================================================

  safePrint(cout_mutex, "[THREAD ", thread_id, "] Channel ", cfg.channel_num,
            " completed ", cfg.acquisition_count, " acquisitions");
}

/* ============================================================ */
/* MAIN FUNCTION */
/* ============================================================ */

int main() {
  // Get number of available ADC channels
  int ch_num = rp_HPGetFastADCChannelsCountOrDefault();

  // Initialize Red Pitaya hardware
  if (!initRedPitaya()) {
    return -1;
  }

  // ============================================================
  // CHANNEL CONFIGURATION SETUP
  // ============================================================

  // Channel hardware mappings
  rp_channel_t ch_list[MAX_NUM] = {RP_CH_1, RP_CH_2, RP_CH_3, RP_CH_4};
  rp_channel_trigger_t trig_list[MAX_NUM] = {RP_T_CH_1, RP_T_CH_2, RP_T_CH_3,
                                             RP_T_CH_4};
  rp_acq_trig_src_t src_list[MAX_NUM] = {
      RP_TRIG_SRC_CHA_PE, // Channel A positive edge
      RP_TRIG_SRC_CHB_PE, // Channel B positive edge
      RP_TRIG_SRC_CHC_PE, // Channel C positive edge
      RP_TRIG_SRC_CHD_PE  // Channel D positive edge
  };

  // Default configuration values
  uint32_t dec_list[MAX_NUM] = {64, 64, 64, 64};
  float lvl_list[MAX_NUM] = {0, 0, 0, 0};
  int dly_list[MAX_NUM] = {0, 0, 0, 0};

  // Create channel configurations
  vector<ChannelConfig> channels(ch_num);
  for (int i = 0; i < ch_num; i++) {
    channels[i].channel_num = i + 1;
    channels[i].ch = ch_list[i];
    channels[i].trig = trig_list[i];
    channels[i].decimation = dec_list[i];
    channels[i].trig_lvl = lvl_list[i];
    channels[i].trig_dly = dly_list[i];
    channels[i].src = src_list[i];
  }

  // Mutex for thread-safe console output
  mutex cout_mutex;

  // Print initial configuration info
  safePrint(cout_mutex, "Acquisitions per channel: ", ACQUISITIONS_PER_CHANNEL);
  safePrint(cout_mutex, "");

  // ============================================================
  // START PER-CHANNEL THREADS
  // ============================================================

  vector<thread> threads;
  for (int i = 0; i < ch_num; i++) {
    threads.emplace_back(channelThread, ref(channels[i]), i + 1,
                         ref(cout_mutex));
  }

  // Wait for all threads to complete
  for (auto &t : threads) {
    t.join();
  }

  // ============================================================
  // FINAL SUMMARY
  // ============================================================

  safePrint(cout_mutex, "");
  safePrint(cout_mutex, "[MAIN] ===== SUMMARY =====");

  int total_acquisitions = 0;
  for (auto &cfg : channels) {
    safePrint(cout_mutex, "[MAIN] Channel ", cfg.channel_num, ": ",
              cfg.acquisition_count, " acquisitions");
    total_acquisitions += cfg.acquisition_count;
  }
  safePrint(cout_mutex, "[MAIN] Total acquisitions: ", total_acquisitions);

  // ============================================================
  // CLEANUP
  // ============================================================

  rp_Release();

  return 0;
}