#include <SoftwareSerial.h>

// software serial #2: RX = digital pin 8, TX = digital pin 9


#define B_SIZE 40

SoftwareSerial uart(8, 9);
uint8_t buffer[B_SIZE];

class UARTProtocol{

public:
  auto write(SoftwareSerial *uart, uint8_t *buffer, size_t size) -> size_t;
  auto read(SoftwareSerial *uart, uint8_t *buffer, size_t size) -> size_t;
private:
  auto readBlock(SoftwareSerial *uart, uint8_t *buffer, size_t size, bool first) -> size_t;
  static auto getHeaderForBlock(uint8_t *buffer, uint8_t size, bool firstBlock) -> uint8_t;
  static auto crc4(uint8_t *data, uint8_t size) -> uint8_t;
};

auto UARTProtocol::crc4(uint8_t *data, uint8_t size) -> uint8_t{
	const uint8_t CRC4_POLY = 0x13;
	uint8_t crc = 0;
	for (uint8_t z = 0; z < size; z++) {
		uint8_t byte = data[z];
		for (int i = 7; i >= 0; --i) {
			bool bit = (byte >> i) & 1;
			bool crc_msb = crc & 0x08;
			crc <<= 1;
			if (crc_msb ^ bit) {
				crc ^= CRC4_POLY;
			}
			crc &= 0x0F;
		}
	}
	return crc;
}

auto UARTProtocol::read(SoftwareSerial *uart, uint8_t *buffer, size_t size) -> size_t{
  size_t pos = 0;
  uint8_t receiveSize = size < 8 ? size : 8;
  bool first = true;
  while(pos < size){
      uint8_t ret = readBlock(uart, buffer + pos, receiveSize, first);
      if (ret != receiveSize){
          return 0;
      }
      first = false;
      pos += ret;
      receiveSize = size - pos > 8 ? 8 : size - pos;
  }
  return pos;
}

auto UARTProtocol::readBlock(SoftwareSerial *uart, uint8_t *buffer, size_t size, bool first) -> size_t{
  uint8_t header = 0;
  while (uart->available() == 0);
  uint8_t ret = uart->readBytes(&header, 1);
  if (ret != 1){
      printf("Error reading header size %d\n",ret);
      return 0;
  }
  uint8_t readSize = (header & 0x07) + 1;
  if (first != (bool)(header & 0x8)){
    uart->flush();
    printf("Error block order 0x%X\n", header);
    return 0;
  }
  if (readSize > size){
      printf("Block size %d is larger than buffer size %d\n", readSize, size);
      return 0;
  }
  while (uart->available() == 0);
  ret = uart->readBytes(buffer, readSize);
  if (ret != readSize){
      printf("Buffer read error. Read size %d\n", ret);
      return 0;
  }
  uint8_t headerReceive = getHeaderForBlock(buffer, readSize, first);
  if (headerReceive != header){
      printf("The receive does not match the packet header 0x%X != 0x%X\n", header, headerReceive);
      return 0;
  }
  ret = uart->write(&headerReceive, 1);
  if (ret != 1){
    return 0;
  }
  return readSize;
}

auto UARTProtocol::write(SoftwareSerial *uart, uint8_t *buffer, size_t size) -> size_t{
    size_t pos = 0;
    uint8_t sendSize = size < 8 ? size : 8;
    bool first = true;
    while(pos < size){
        uint8_t header = getHeaderForBlock(buffer + pos, sendSize, first);
        uint8_t ret = uart->write(&header, 1); // Send header at first
        if (ret != 1){
            return pos;
        }
        first = false;
        uart->flush();
        ret = uart->write(buffer + pos, sendSize);  // Send data block
        if (ret != sendSize){
            return pos + ret;
        }
        uart->flush();
        uint8_t headerResponse = 0;
        while (uart->available() == 0);
        ret = uart->readBytes(&headerResponse, 1);
        if (headerResponse != header){
            printf("The response does not match the packet header 0x%X != 0x%X\n",header, headerResponse);
            return pos;
        }
        uart->flush();
        pos += sendSize;
        sendSize = pos + sendSize < size ? sendSize : size - pos;
    }

    return 0;
}

auto UARTProtocol::getHeaderForBlock(uint8_t *buffer, uint8_t size, bool firstBlock) -> uint8_t{
    if (size == 0){
        printf("Buffer size cannot be 0\n");
        return 0;
    }
    if (size > 8){
        printf("The size %d is larger than the allowed 8\n",size);
        return 0;
    }
    uint8_t value = crc4(buffer, size);
  	value = value << 4;
    value = (value & 0xF0) | ((size - 1) & 0x07) | (firstBlock ? 0x8 : 0);
    return value;
}

UARTProtocol p;

FILE f_out;
int sput(char c, __attribute__((unused)) FILE* f) {return !Serial.write(c);}

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  uart.begin(9600);
  fdev_setup_stream(&f_out, sput, nullptr, _FDEV_SETUP_WRITE);
  stdout = &f_out;
}

void loop() {
  printf("Start\n");
  for(int i = 0 ; i < B_SIZE; i++){
    buffer[i] = i;
  }
  p.write(&uart, buffer, B_SIZE);
  printf("Start read\n");
  p.read(&uart, buffer, B_SIZE);
  for(int i = 0 ; i < B_SIZE; i++){
     printf("%d,",buffer[i]);
  }
  printf("\n");
  printf("All done\n");
  delay(50);
}
