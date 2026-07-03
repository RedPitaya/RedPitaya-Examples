/* Red Pitaya C++ API example - Two-thread trigger timing measurement */

#include "rp.h"
#include "rp_hw_calib.h"
#include <atomic>
#include <chrono>
#include <cmath>
#include <csignal>
#include <iostream>
#include <thread>
#include <vector>

std::atomic<bool> running{true};

void signal_handler(int signal) {
  if (signal == SIGINT) {
    std::cout << "\nCtrl+C pressed. Stopping..." << std::endl;
    running = false;
  }
}

void generator_thread() {
  rp_GenReset();
  rp_GenWaveform(RP_CH_1, RP_WAVEFORM_SINE);
  rp_GenFreq(RP_CH_1, 1000.0);
  rp_GenAmp(RP_CH_1, 1.0);
  rp_GenMode(RP_CH_1, RP_GEN_MODE_BURST);
  rp_GenBurstCount(RP_CH_1, 1);
  rp_GenOutEnable(RP_CH_1);

  while (running) {
    rp_GenTriggerOnly(RP_CH_1);
    std::cout << "Gen signal" << std::endl;
    std::this_thread::sleep_for(std::chrono::seconds(1));
  }

  std::cout << "Generator thread stopped" << std::endl;
}

void acquisition_thread() {
  // rp_EnableDebugReg();
  rp_AcqReset();
  rp_AcqSetDecimation(RP_DEC_1024);
  rp_AcqSetTriggerDelay(0);
  rp_AcqSetTriggerLevel(RP_T_CH_1, 0.15);
  rp_AcqSetInitTimestamp(0);

  uint64_t prev_timestamp = 0;
  uint64_t cur_timestamp = 0;

  while (running) {
    rp_AcqStart();
    rp_AcqSetTriggerSrc(RP_TRIG_SRC_CHA_PE);
    int result = rp_AcqIntTriggerRead(3000);
    if (!running)
      break;

    if (result == RP_OK) {
      rp_AcqGetTimestamp(RP_CH_1, &cur_timestamp);

      if (prev_timestamp != 0) {
        double delta_time = (cur_timestamp - prev_timestamp) / 1e9;
        std::cout << "Time between triggers: " << delta_time << " s"
                  << std::endl;
      } else {
        std::cout << "First trigger detected" << std::endl;
      }
      prev_timestamp = cur_timestamp;
      std::this_thread::sleep_for(std::chrono::milliseconds(100));
    } else if (result == RP_ETIM) {
      std::cerr << "Timeout" << std::endl;
    } else {
      std::cerr << "Error: " << rp_GetError(result) << std::endl;
      break;
    }
  }

  rp_AcqStop();
  std::cout << "Acquisition thread stopped" << std::endl;
}

int main() {
  std::signal(SIGINT, signal_handler);
  if (rp_Init() != RP_OK) {
    std::cerr << "API initialization failed!" << std::endl;
    return 1;
  }

  std::cout << "Starting trigger timing measurement..." << std::endl;
  std::cout << "Press Ctrl+C to stop" << std::endl;

  std::thread gen(generator_thread);
  std::thread acq(acquisition_thread);

  gen.join();
  acq.join();

  std::cout << "Program finished successfully" << std::endl;

  rp_Release();
  return 0;
}
