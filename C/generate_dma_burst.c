/* Red Pitaya C API example Generating continuous signal via DMA
 * This application generates a specific signal */

#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <unistd.h>
#include <math.h>

#include "rp.h"
#include "rp_asg_axi.h"

int main(int argc, char **argv){

	if(rp_Init() != RP_OK){
		fprintf(stderr, "Rp api init failed!\n");
		return 1;
	}

	uint32_t adc_axi_start, adc_axi_size;
    if (rp_AcqAxiGetMemoryRegion(&adc_axi_start,&adc_axi_size) != RP_OK){
		fprintf(stderr, "Error get memory!\n");
		return 1;
	}

	uint32_t bufferSize = 1024 * 1024;
	if (adc_axi_size < bufferSize) {
		bufferSize = adc_axi_size;
	}

	if (rp_GenAxiReserveMemory(RP_CH_1,adc_axi_start, adc_axi_start + bufferSize) != RP_OK){
    	fprintf(stderr,"Error setting address for DMA mode for OUT1\n");
		return 1;
	}


	if (rp_GenAxiSetDecimationFactor(RP_CH_1,1) != RP_OK){
    	fprintf(stderr,"Error setting decimation for generator\n");
    	return 1;
	}

	if (rp_GenAxiSetEnable(RP_CH_1,true) != RP_OK){
    	fprintf(stderr,"Error enable axi mode for OUT1\n");
    	return 1;
	}

	bufferSize /= 2;

	float *t = (float *)malloc(bufferSize * sizeof(float));
	float *x = (float *)malloc(bufferSize * sizeof(float));

	for(int i = 1; i < bufferSize; i++){
		t[i] = (2 * M_PI) / bufferSize * i;
	}

	for (int i = 0; i < bufferSize; ++i){
		x[i] = sin(t[i]) + ((1.0/3.0) * sin(t[i] * 3));
	}

	rp_GenSetAmplitudeAndOffsetOrigin(RP_CH_1);
	rp_GenMode(RP_CH_1, RP_GEN_MODE_BURST);
	rp_GenBurstCount(RP_CH_1, 2);
	rp_GenBurstRepetitions(RP_CH_1, 1);
	rp_GenBurstPeriod(RP_CH_1, 100);
	rp_GenAxiWriteWaveform(RP_CH_1, x, bufferSize);
	rp_GenOutEnable(RP_CH_1);
	rp_GenTriggerOnly(RP_CH_1);

	free(t);
	free(x);

	rp_Release();

	return 0;
}
