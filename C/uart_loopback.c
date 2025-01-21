/* @brief This is a simple application for testing UART communication on a RedPitaya
* @Author Luka Golinar <luka.golinar@redpitaya.com>
*
* (c) Red Pitaya  http://www.redpitaya.com
*
* This part of code is written in C programming language.
* Please visit http://en.wikipedia.org/wiki/C_(programming_language)
* for more details on the language used herein.
*/


#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "rp_hw.h"


int main(int argc, char *argv[]){

    char *buffer = "TEST string";
    char rx_buf[255];
    memset(rx_buf,0,255);
    int size = 255;

    int res = rp_UartInit(); // init uart api
    printf("Init result: %d\n",res);

    res = rp_UartSetSpeed(115200); // set uart speed
    printf("Set speed: %d\n",res);

    res = rp_UartSetBits(RP_UART_CS8); // set word size
    printf("Set CS8: %d\n",res);


    res = rp_UartSetSettings(); // apply settings to uart
    printf("Set settings: %d\n",res);

    res = rp_UartRead((unsigned char*)rx_buf,&size); // read from uart
    printf("Read (%s) %d\n",rx_buf,size);
    res = rp_UartWrite((unsigned char*)rx_buf,size); // write buffer to uart
    printf("Write result: %d\n",res);


    res = rp_UartRelease(); // close uart api
    printf("UnInit result: %d\n",res);
    return 0;
}
