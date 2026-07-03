/* Red Pitaya C API example Acquiring a signal from a buffer
 * This application acquires a signal on a specific channel */

#include "rp.h"
#include "rp_hw_calib.h"
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

int main(int argc, char **argv) {

  /* Print error, if rp_Init() function failed */
  if (rp_Init() != RP_OK) {
    fprintf(stderr, "Rp api init failed!\n");
  }
  //  rp_EnableDebugReg();
  rp_GenReset();
  rp_GenFreq(RP_CH_1, 100.0);
  rp_GenAmp(RP_CH_1, 1.0);
  rp_GenWaveform(RP_CH_1, RP_WAVEFORM_SINE);
  rp_GenOutEnable(RP_CH_1);
  rp_GenTriggerOnly(RP_CH_1);

  uint32_t buff_size = 20;
  float *buff = (float *)malloc(buff_size * sizeof(float));

  rp_AcqReset();
  rp_AcqSetDecimation(RP_DEC_16384);
  rp_AcqSetTriggerDelay(0);

  int count = 10;
  rp_AcqSetArmKeep(true);
  rp_AcqStart();
  while (count--) {
    printf("Step %d\n", 10 - count);

    /* After acquisition is started some time delay is needed in order to
     * acquire fresh samples in to buffer*/
    /* Here we have used time delay of one second but you can calculate exact
     * value taking in to account buffer*/
    /*length and smaling rate*/
    int z = 5;

    while (z) {
      uint32_t c;
      rp_AcqGetPreTriggerCounter(&c);
      sleep(1);
      z--;
      printf("Pre counter %d\n", c);
    }

    sleep(1);

    rp_AcqSetTriggerSrc(RP_TRIG_SRC_NOW);
    rp_acq_trig_state_t state = RP_TRIG_STATE_TRIGGERED;

    while (1) {
      rp_AcqGetTriggerState(&state);
      if (state == RP_TRIG_STATE_TRIGGERED) {
        sleep(1);
        break;
      }
    }

    bool fillState = false;
    while (!fillState) {
      rp_AcqGetBufferFillState(&fillState);
    }

    rp_AcqGetOldestDataV(RP_CH_1, &buff_size, buff);

    uint32_t i;
    for (i = 0; i < buff_size; i++) {
      printf("%f\n", buff[i]);
    }

    // Unlocking the trigger is required for Keep Arm mode.
    // For normal mode, unlocking occurs when calling the rp_AcqStart command.
    rp_AcqUnlockTrigger();
  }

  rp_AcqStop();
  /* Releasing resources */
  free(buff);
  rp_Release();

  return 0;
}
