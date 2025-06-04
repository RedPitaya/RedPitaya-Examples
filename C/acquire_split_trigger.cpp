/* Red Pitaya C API example for acquiring data from all 4 channels in split
 * trigger mode */

#include "rp.h"
#include "rp_hw-profiles.h"
#include <algorithm>
#include <chrono>
#include <iostream>
#include <random>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

void mixArray(int *array, int n);

int main(int argc, char **argv) {
  int res;
  int ch_num = rp_HPGetFastADCChannelsCountOrDefault();
  rp_channel_t ch[ch_num] = {RP_CH_1, RP_CH_2, RP_CH_3, RP_CH_4};
  rp_channel_trigger_t ch_trig[ch_num] = {RP_T_CH_1, RP_T_CH_2, RP_T_CH_3,
                                          RP_T_CH_4};
  uint32_t decimation[ch_num] = {64, 64, 64, 64};
  float trig_lvl[ch_num] = {0.1, 0.1, 0.1, 0.1};
  int trig_dly[ch_num] = {0, 0, 0, 0};
  rp_acq_trig_src_t trig_src[ch_num] = {RP_TRIG_SRC_CHA_PE, RP_TRIG_SRC_CHB_PE,
                                        RP_TRIG_SRC_CHC_NE, RP_TRIG_SRC_CHD_NE};
  uint32_t acq_trig_pos[ch_num] = {0, 0, 0, 0};
  int trig_ord[ch_num] = {1, 2, 3, 4};

  mixArray(trig_ord, ch_num);
  for (int i = 0; i < ch_num; i++)
    std::cout << trig_ord[i] << " ";
  std::cout << std::endl;

  if (rp_Init() != RP_OK) {
    std::cerr << "Rp api init failed!" << std::endl;
  }

  /* Reserve space for data */
  uint32_t buff_size = 6001;
  float **buff = (float **)malloc(ch_num * sizeof(float *));
  for (int i = 0; i < ch_num; i++) {
    buff[i] = (float *)malloc(buff_size * sizeof(float));
  }

  rp_AcqReset();
  rp_AcqSetSplitTrigger(true); // Enable split trigger mode

  /* Configure acquisition settings for each channel */
  for (int i = 0; i < ch_num; i++) {
    rp_AcqResetCh(ch[i]);
    rp_AcqSetDecimationFactorCh(ch[i], decimation[i]); // Decimation factor
    rp_AcqSetGain(ch[i], RP_LOW);
    rp_AcqSetTriggerLevel(ch_trig[i], trig_lvl[i]);
    rp_AcqSetTriggerDelayCh(ch[i], trig_dly[i]);
    rp_AcqStartCh(ch[i]);                      // Start acquisition on channel
    rp_AcqSetTriggerSrcCh(ch[i], trig_src[i]); // Set channel trigger source
  }

  /* Wait for trigger and buffer full */
  for (int i = 0; i < ch_num; i++) {
    bool fillState = false;
    while (!fillState) {
      rp_AcqGetBufferFillStateCh(ch[trig_ord[i] - 1], &fillState);
    }
    std::cout << "Channel " << trig_ord[i] << " data acquired" << std::endl;
  }

  /* Get data */
  for (int i = 0; i < ch_num; i++) {
    rp_AcqGetWritePointerAtTrigCh(ch[i], &acq_trig_pos[i]);
    std::cout << "Channel " << trig_ord[i] << " trig position "
              << acq_trig_pos[i] << std::endl;
    res = rp_AcqGetDataV(ch[i], acq_trig_pos[i], &buff_size, buff[i]);
    if (res != RP_OK) {
      std::cout << "Error: " << res << std::endl;
    }
  }

  /* Print data */
  for (int i = 0; i < ch_num; i++) {
    std::cout << "Channel " << i + 1 << std::endl;
    for (int j = 0; j < 100; j++) { //(int)buff_size
      std::cout << buff[i][j];
      if (j != 100 - 1) { //(int)buff_size -1
        std::cout << ", ";
      }
    }
    std::cout << std::endl << std::endl;
  }

  /* Release resources */
  for (int i = 0; i < ch_num; i++) {
    free(buff[i]);
  }
  free(buff);

  rp_Release();
  return 0;
}

void mixArray(int *array, int n) {
  /* Randomly shuffle the array */
  unsigned seed = std::chrono::system_clock::now().time_since_epoch().count();
  std::shuffle(array, array + n, std::default_random_engine(seed));
}
