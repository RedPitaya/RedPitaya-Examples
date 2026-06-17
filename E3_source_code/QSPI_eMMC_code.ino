// Program for the Red Pitaya E3 add-on extension board (QSPI & EMMC) //
#include <PeripheralPins.h>
#include <Wire.h>

// STM32L412K8T6 pinout
// Pins not described here are not connected on the E3 board
// For full pinout see the datasheet https://www.st.com/en/microcontrollers-microprocessors/stm32l412k8.html

/* REDEFINE DEFAULT PINMAP */
const PinMap PinMap_I2C_SDA[] = {
  { PB_4, I2C3, STM_PIN_DATA(STM_MODE_AF_OD, GPIO_NOPULL, GPIO_AF4_I2C3) },
  { PB_7, I2C1, STM_PIN_DATA(STM_MODE_AF_OD, GPIO_NOPULL, GPIO_AF4_I2C1) },
  { NC, NP, 0 }
};

const PinMap PinMap_I2C_SCL[] = {
  { PA_7, I2C3, STM_PIN_DATA(STM_MODE_AF_OD, GPIO_NOPULL, GPIO_AF4_I2C3) },
  { PB_6, I2C1, STM_PIN_DATA(STM_MODE_AF_OD, GPIO_NOPULL, GPIO_AF4_I2C1) },
  { NC, NP, 0 }
};

const PinMap PinMap_UART_TX[] = {
  { PA_2, USART2, STM_PIN_DATA(STM_MODE_AF_PP, GPIO_PULLUP, GPIO_AF7_USART2) },
  { NC, NP, 0 }
};

const PinMap PinMap_UART_RX[] = {
  { PA_3, USART2, STM_PIN_DATA(STM_MODE_AF_PP, GPIO_PULLUP, GPIO_AF7_USART2) },
  { NC, NP, 0 }
};

const PinMap PinMap_USB[] = {
  { PA_11, USB, STM_PIN_DATA(STM_MODE_AF_PP, GPIO_NOPULL, GPIO_AF10_USB_FS) },  // USB_DM
  { PA_12, USB, STM_PIN_DATA(STM_MODE_AF_PP, GPIO_NOPULL, GPIO_AF10_USB_FS) },  // USB_DP
  { NC, NP, 0 }
};

/* PIN DEFINITIONS */
#define PWR_ON_CN_PIN (PA0)    // Power On signal from CN7
#define PWR_ON_PB_PIN (PA1)    // Controlled with P-ON button
#define UART_TX_PIN (PA2)      // UART (NC) - Shares the bus with I2C1
#define UART_RX_PIN (PA3)      // Populate R17, R18, R3 and R4 to connect to DIO12_N, DIO12_P
#define E3_WDT_KICK_PIN (PA4)  // Watchdog timer
#define E3_SHDN_PIN (PA5)      // Shutdown signal
#define PS_POR_PIN (PA6)       // PS signal (Power-On reset) - Read only
#define PWR_ON_PIN (PB1)       // Power supply control
#define LED_RED_PIN (PA8)      // Red LED
#define LED_GREEN_PIN (PA9)    // Green LED
#define USB_N_PIN (PA11)
#define USB_P_PIN (PA12)
#define UC_SWDIO_PIN (PA13)  // ST-LINK SWD communication
#define UC_SWCLK_PIN (PA14)
#define I2C0_SCL_PIN (PB6)  // I2C0 bus connected to Red Pitaya I2C
#define I2C0_SDA_PIN (PB7)
#define I2C1_SCL_PIN (PA7)  // I2C1 (NC) - Shares the bus with UART
#define I2C1_SDA_PIN (PB4)  // Populate R3 and R4 to connect to DIO12_N, DIO12_P

/* TIMINGS */
#define RP_WDT_BOOT_TIME 10000   // Min boot time for the watchdog to start kicking \
                                 // Infinite loop (CLK not present) starts 20 seconds into booting process
#define BTN_PWR_UP_TIME 500      // Button turn on/off time
#define BOOT_TIME 45000          // Red Pitaya boot time (PWR_UP to PWR_ON)
#define PWR_DOWN_TIME 20000      // Power down time
#define PWR_DOWN_TIME_EXT 10000  // Extended power down time
#define PWR_RST_TIME 5000        // Reset state time
#define PWR_OFF_TIME 4000        // Force shut down time

#define PWR_CHECK_TIME 8000  // Max power good check time
#define WDT_MAX_TIME 5000    // Max watchdog inactive time
#define BLINK_TIME 1000      // Normal blink time
#define BOOT_DLY_TIME 1000   // Delayed boot time (15 sec prev)

/* Additional Constants for Better Code Readability */
#define LED_FAST_BLINK_DIVISOR 4     // Divider for fast LED blink (4x faster)
#define LED_SLOW_BLINK_MULTIPLIER 2  // Multiplier for slow LED blink (2x slower)
#define PWR_OFF_FLASH_ON_TIME 250    // LED on time during power off flash
#define PWR_OFF_FLASH_OFF_TIME 9500  // LED off time during power off flash
#define MAX_REBOOT_COUNT 3           // Maximum number of reboots before failure
#define I2C_BUFFER_SIZE 4            // Standard I2C message size
#define VERBOSE_TOGGLE_CMD 0xFF      // Command to toggle verbose output

/* Button Press Detection Constants */
#define WDT_SHORT_PRESS_MAX_TIME 1000     // Maximum time for a short press (ms)
#define WDT_PRESS_SEQUENCE_TIMEOUT 5000  // Time window for 5 consecutive presses (ms)
#define WDT_REQUIRED_PRESS_COUNT 3       // Number of consecutive short presses needed

/* E3 ID and hardware ID */
#define E3_ID_HEX 0xE3AD0000
#define E3_ERR_ID_HEX 0xE3330000
#define HW_ID 0x01     // E3 Add-on hardware ID/revision number
#define I2C_ADDR 0x10  // Change later if necessary
/* REGISTER DEFINES */
// Not implemented
// #define EMMC_REG      0x00000000   // Booting from EMMC
// #define I2C1_nUART    0x00000000  // Select I2C1 or UART (on the bus)

// UART and I2C startup
HardwareSerial Serial1(UART_RX_PIN, UART_TX_PIN);
TwoWire Wire0(I2C0_SDA_PIN, I2C0_SCL_PIN);  // I2C 0
// TwoWire Wire1(I2C1_SDA_PIN, I2C1_SCL_PIN);     // I2C 1


/* Global Variables */
volatile enum {
  PWR_OFF,
  PWR_UP,
  PWR_ON,
  PWR_DWN,
  PWR_DWN_RST,
  PWR_RST,
  PWR_FAIL
} RP_PWR_state,
  RP_E3_I2C_state;

volatile enum {
  E3_OK,
  E3_NOK,
  E3_ERR
} RP_E3_ERR;

enum {
  BTN_PE,
  BTN_NE
};

bool first = true;             // First time in a state
bool pwr_dwn_blink = false;    // Fast LED blink flag
bool wdt_start = false;        // Watchdog check flag
bool wdt_disable = false;       // Watchdog disable flag
bool pwr_check_start = false;  // Power check flag

unsigned long wdt_start_timer = 0;  // Timer for checking WDT
unsigned long shut_down_timer = 0;
unsigned long pwr_on_timer = 0;

volatile bool i2c_err_rspnd = false;     // Respond with any errors
volatile bool i2c_state_change = false;  // State change over I2C
volatile bool verb_out = true;           // Enable verbose output through UART


/* ### LED functions ### */

void LED_blink(int led, unsigned int led_interval_ms, bool reset) {
  // Checks the system time and toggles LED state if the specified amount of time has passed
  static bool green_led_state = false;
  static bool red_led_state = false;
  static unsigned long led_time_old = millis();
  unsigned long led_time = millis();

  // Reset interval, clear state, turn off LEDs
  if (reset) {
    led_time_old = millis();
    green_led_state = false;
    red_led_state = false;
    LED_off(LED_RED_PIN);
    LED_off(LED_GREEN_PIN);
  } else {
    // Check time interval
    if (led_time - led_time_old >= led_interval_ms / 2) {
      led_time_old = led_time;
      // Toggle the correct LED
      if (led == LED_RED_PIN) {
        if (red_led_state) {
          LED_on(led);
        } else {
          LED_off(led);
        }
        red_led_state = !red_led_state;
      } else {
        if (green_led_state) {
          LED_on(led);
        } else {
          LED_off(led);
        }
        green_led_state = !green_led_state;
      }
    }
  }
  return;
}

void LED_pwrOff_flash(bool reset) {
  /* Flash LED once every 10 seconds */
  static bool red_led_state = false;
  static unsigned long red_led_time_old = millis();
  static bool flash = false;
  unsigned long red_led_time = millis();

  if (reset) {
    red_led_state = false;
    red_led_time_old = millis();
    flash = false;
  } else {
    // Check state
    if (flash) {
      // Flash LED once (1 Hz)
      if (red_led_time - red_led_time_old >= 250) {
        red_led_time_old = red_led_time;

        // Flash LED
        if (red_led_state) {
          LED_on(LED_RED_PIN);
        } else {
          LED_off(LED_RED_PIN);
          flash = false;  // After one flash change state
        }
        red_led_state = !red_led_state;
      }
    } else {
      // LED OFF time
      if (red_led_time - red_led_time_old >= 9500) {
        red_led_time_old = red_led_time;
        flash = true;
      }
    }
  }
  return;
}

void LED_on(int led) {
  // Turn LED on - negative logic
  digitalWrite(led, LOW);
  return;
}

void LED_off(int led) {
  // Turn LED off - negative logic
  digitalWrite(led, HIGH);
  return;
}


/* ### Pin interaction ### */

int pin_read(int pin) {
  // Read state of specified pin
  return digitalRead(pin);
}

void pin_set(int pin, bool state) {
  // Set state of specified pin
  if (state) {
    digitalWrite(pin, HIGH);
  } else {
    digitalWrite(pin, LOW);
  }

  return;
}

bool PON_check(int edge, bool reset) {
  // Check PON button or pin press/release
  static int pon_button_state_old = 0;
  static int pon_conn_state_old = 0;
  int pon_button_state_new = pin_read(PWR_ON_PB_PIN);
  int pon_conn_state_new = pin_read(PWR_ON_CN_PIN);
  bool press = false;

  // Reset static variables
  if (reset) {
    pon_button_state_old = 0;
    pon_conn_state_old = 0;
  } else {
    // Define positive or negative edge
    if (edge == BTN_PE) {
      // Button press
      press = (pon_button_state_old == 0 && pon_button_state_new == 1) || (pon_conn_state_old == 0 && pon_conn_state_new == 1);
    } else {
      // Button release
      press = (pon_button_state_old == 1 && pon_button_state_new == 0) || (pon_conn_state_old == 1 && pon_conn_state_new == 0);
    }

    pon_button_state_old = pon_button_state_new;
    pon_conn_state_old = pon_conn_state_new;
  }
  return press;
}

bool PON_state() {
  // Check PON state - negative logic
  if ((pin_read(PWR_ON_PB_PIN) == 0) || (pin_read(PWR_ON_CN_PIN) == 0)) {
    return true;
  } else {
    return false;
  }
}

/* ### Power and Watchdog ### */

void RP_poweroff() {
  // Disable power on Red Pitaya

  digitalWrite(PWR_ON_PIN, HIGH);
  digitalWrite(E3_SHDN_PIN, LOW);

  return;
}

void RP_powerup() {
  // Enable power on Red Pitaya

  digitalWrite(PWR_ON_PIN, LOW);
  digitalWrite(E3_SHDN_PIN, LOW);

  return;
}

void RP_shutdown() {
  // Send shutdown signal to Red Pitaya

  digitalWrite(PWR_ON_PIN, LOW);
  digitalWrite(E3_SHDN_PIN, HIGH);

  return;
}


int RP_reboot_cnt(bool reset, bool check) {
  // Count reboots
  static int rst_num = 0;

  if (reset) {
    rst_num = 0;
  } else {
    if (!check) {
      rst_num++;  // Count number of reboots
    }
  }

  return rst_num;
}

int RP_WDTKickCheck(bool check_wdt, bool wdt_disable, bool reset) {
  // Check the kick on WatchDogTimer (should activate trice per second)
  static int wdt_state_old = 0;
  int wdt_state_new = pin_read(E3_WDT_KICK_PIN);
  static unsigned long time_old = millis();
  unsigned long time_new = millis();

  if (reset || wdt_disable) {
    wdt_state_old = 0;
    time_old = millis();  // Reset timer to prevent state change issues
  } else {
    // Watchdog pin active
    if (wdt_state_old != wdt_state_new) {
      time_old = time_new;
    }
    wdt_state_old = wdt_state_new;
    // If watchdog pin is not active start Red Pitaya reset proceedure
    if ((time_new - time_old >= WDT_MAX_TIME) && check_wdt) {  // Check only if wdt checking is enabled
      return 1;
    }
  }
  return 0;
}

bool RP_PSCheck() {
  // Check power supply state

  if (pin_read(PS_POR_PIN)) {
    return true;
  } else {
    return false;
  }
}

bool RP_power_on_off(bool reset) {
  // Check power on/off button press return whether power state change is necessary
  static bool start_check = false;
  static unsigned long first_press_time = 0;
  unsigned long press_time = 0;

  if (reset) {
    start_check = false;
    pwr_dwn_blink = false;
    first_press_time = 0;
  } else {
    /* Power off procedure */
    if (!start_check) {
      // Inactive - start timer
      if (PON_check(BTN_NE, false)) {
        first_press_time = millis();
        start_check = true;
      }
      pwr_dwn_blink = false;
      return false;
    } else {
      // Active - check P_ON state and timers
      if (PON_state()) {
        // Calculate press time
        press_time = millis() - first_press_time;
        if (press_time >= PWR_OFF_TIME) {  // Pressed for 10 seconds - PWR_OFF
          // Configure flags
          if (verb_out) {
            Serial1.println("BTN OFF sec");
          }
          start_check = false;
          pwr_dwn_blink = false;
          return true;
        } else if (press_time >= BTN_PWR_UP_TIME) {  // Pressed for 2 seconds
          if ((RP_PWR_state == PWR_OFF) || (RP_PWR_state == PWR_FAIL)) {
            if (verb_out) {
              Serial1.println("BTN ON sec");
            }
            start_check = false;
            pwr_dwn_blink = false;
            return true;
          } else {
            pwr_dwn_blink = true;
          }
        }
      } else {  // If released sooner than 10 seconds exit
        // Check for P_ON release during PWR_ON
        if (PON_check(BTN_PE, false) && pwr_dwn_blink && RP_PSCheck() && (RP_PWR_state == PWR_ON)) {
          if (verb_out) {
            Serial1.println("BTN ON sec");
          }
          start_check = false;
          // power_down_blink is disabled the next time this function is executed
          return true;
        } else {
          start_check = false;
          pwr_dwn_blink = false;
        }
      }
    }
  }

  return false;
}


/* I2C setup */
void I2C0_request_handler(void) {
  // Processes the request from the I2C line and sends the correct response
  // Use stack allocation instead of malloc for better embedded performance
  uint8_t e3_i2c_data[4] = { 0 };  // Initialize to zero without memset

  if (i2c_err_rspnd) {
    // Prepare data
    e3_i2c_data[0] = (uint8_t)((E3_ERR_ID_HEX & 0xFF000000) >> 24);
    e3_i2c_data[1] = (uint8_t)((E3_ERR_ID_HEX & 0x00FF0000) >> 16);
    e3_i2c_data[2] = (uint8_t)HW_ID;
    e3_i2c_data[3] = (uint8_t)RP_E3_ERR;

    Wire0.write(e3_i2c_data, 4);  // If state change was requested beforehand send back Error code
    i2c_err_rspnd = false;

    if (verb_out) {
      Serial1.print("Err ");
      for (int i = 0; i < 4; i++) {
        Serial1.print(e3_i2c_data[i], HEX);
      }
      Serial1.println();
    }

  } else {
    // Prepare data
    e3_i2c_data[0] = (uint8_t)((E3_ID_HEX & 0xFF000000) >> 24);
    e3_i2c_data[1] = (uint8_t)((E3_ID_HEX & 0x00FF0000) >> 16);
    e3_i2c_data[2] = (uint8_t)HW_ID;
    e3_i2c_data[3] = (uint8_t)RP_PWR_state;

    Wire0.write(e3_i2c_data, 4);  // Send data to Red Pitaya

    if (verb_out) {
      Serial1.print("I2C0 req rec ");
      for (int i = 0; i < 4; i++) {
        Serial1.print(e3_i2c_data[i], HEX);
      }
      Serial1.println();
    }
  }
  // No need to free() with stack allocation
  return;
}

void I2C0_receive_handler(int numBytes) {
  // Receives data from the I2C line
  static uint32_t e3_id = E3_ID_HEX + (HW_ID << 8);
  uint32_t data_id = 0;

  // Safety check for buffer size
  const int MAX_I2C_BYTES = 8;
  if (numBytes > MAX_I2C_BYTES || numBytes < 4) {
    // Drain the buffer and return on invalid size
    while (Wire0.available()) {
      Wire0.read();
    }
    if (verb_out) {
      Serial1.println("I2C invalid size");
    }
    return;
  }

  uint8_t data[MAX_I2C_BYTES] = { 0 };  // Initialize to zero

  for (int i = 0; i < numBytes; i++) {
    data[i] = Wire0.read();  // Receive a byte as uint8_t
  }

  if (verb_out) {
    for (int i = 0; i < numBytes; i++) {
      Serial1.print(data[i], HEX);
    }
    Serial1.println();
  }

  // Check if the data is intended for this board
  data_id = ((uint32_t)data[0] << 24) + ((uint32_t)data[1] << 16) + ((uint32_t)data[2] << 8);

  if (e3_id == data_id) {
    I2C_check_state(data[3]);
  }

  // No need to free() with stack allocation
  return;
}

void I2C_check_state(uint8_t state) {
  /* Checks the sent state and determines a response */

  switch (state) {

    case (uint8_t)PWR_UP:
      RP_E3_I2C_state = PWR_UP;
      RP_E3_ERR = E3_OK;
      i2c_state_change = true;
      i2c_err_rspnd = true;

      if (verb_out) {
        Serial1.println("I2C switch PWR_UP");
      }
      return;

    case (uint8_t)PWR_ON:
      RP_E3_I2C_state = PWR_ON;
      RP_E3_ERR = E3_OK;
      i2c_state_change = true;
      i2c_err_rspnd = true;

      if (verb_out) {
        Serial1.println("I2C switch PWR_ON");
      }
      return;

    case (uint8_t)PWR_DWN:
      RP_E3_I2C_state = PWR_DWN;
      RP_E3_ERR = E3_OK;
      i2c_state_change = true;
      i2c_err_rspnd = true;

      if (verb_out) {
        Serial1.println("I2C switch PWR_DWN");
      }
      return;

    case (uint8_t)PWR_DWN_RST:
      RP_E3_I2C_state = PWR_DWN_RST;
      RP_E3_ERR = E3_OK;
      i2c_state_change = true;
      i2c_err_rspnd = true;

      if (verb_out) {
        Serial1.println("I2C switch PWR_DWN_RST");
      }
      return;

    case VERBOSE_TOGGLE_CMD:
      // Toggle verbose output
      verb_out = !verb_out;
      RP_E3_ERR = E3_OK;
      i2c_state_change = false;
      i2c_err_rspnd = true;

      if (verb_out) {
        Serial1.println("I2C verbose enabled");
      }
      return;

    default:
      i2c_state_change = false;

      if (state > (uint8_t)PWR_FAIL) {
        RP_E3_ERR = E3_ERR;  // Invalid state

        if (verb_out) {
          Serial1.println("I2C invalid state");
        }
      } else {
        RP_E3_ERR = E3_NOK;  // Cannot change to the requested state

        if (verb_out) {
          Serial1.println("I2C cant switch state");
        }
      }
      i2c_err_rspnd = true;
      return;
  }
}


/* Setup */
// the setup function runs once when you press reset or power the board
void setup() {
  // Initialize pin IO
  pinMode(PWR_ON_CN_PIN, INPUT);    // Connector Power ON signal
  pinMode(PWR_ON_PB_PIN, INPUT);    // Button Power ON signal
  pinMode(E3_WDT_KICK_PIN, INPUT);  // Watchdog timer kick from Red Pitaya
  pinMode(E3_SHDN_PIN, OUTPUT);     // Shutdown signal for Red Pitaya
  pinMode(PS_POR_PIN, INPUT);       // Monitor Power Supply Ready activity from Red Pitaya (Power ON Reset)
  pinMode(PWR_ON_PIN, OUTPUT);      // Power ON signal for Red Pitaya
  pinMode(LED_GREEN_PIN, OUTPUT);   // Green LED
  pinMode(LED_RED_PIN, OUTPUT);     // Red LED

  // Disable LEDs
  LED_off(LED_RED_PIN);
  LED_off(LED_GREEN_PIN);

  // I2C and UART init
  // TODO add I2C timeout?
  Serial1.begin(115200);                  // Start UART interface
  Wire0.begin(I2C_ADDR);                  // Start I2C0 - available at address I2C_ADDR
  Wire0.setClock(400000);                 // Set I2C speed
  Wire0.onReceive(I2C0_receive_handler);  // On I2C recieve and request from master execute a handler function
  Wire0.onRequest(I2C0_request_handler);
  /*
    // I2C1 not implemented currently
    Wire1.begin(I2C_ADDR);                  // Start I2C1
    Wire1.setClock(400000);
    Wire1.onReceive(I2C1_recieve_handler);
    Wire1.onRequest(I2C1_request_handler);
    */

  // State machine starting point
  RP_PWR_state = PWR_OFF;  // Start in OFF state
  RP_E3_ERR = E3_OK;
  RP_E3_I2C_state = PWR_UP;

  // Initialize button functions
  PON_check(BTN_PE, true);           // Reset PON_check state
}

// the loop function runs over and over again forever
void loop() {

  switch (RP_PWR_state) {

    case PWR_UP:
      if (first) {
        RP_powerup();                               // Turn on Red Pitaya power
        LED_blink(0, 0, true);                      // Reset LED states
        RP_WDTKickCheck(false, wdt_disable, true);  // Reset WDT state
        first = false;                              // disable first time state
        pwr_on_timer = millis();                    // Timer to switch state to PWR_ON if WDT is working
        wdt_start = false;                          // Start checking WDT
        pwr_check_start = false;                    // Start checking Power

        if (verb_out) {
          Serial1.println("PWR_UP");
        }
      }

      /* I2C forced state change */
      if (i2c_state_change) {
        i2c_state_change = false;
        RP_PWR_state = RP_E3_I2C_state;  // Change state to the requested one (no check if already in that state)
        first = true;
        break;
      }

      /* LED Blink */
      LED_blink(LED_GREEN_PIN, BLINK_TIME, false);  // Blink Green LED with 1 Hz

      /* Check Power Supply start condition */
      if ((millis() - pwr_on_timer >= PWR_CHECK_TIME + BOOT_DLY_TIME) && !pwr_check_start) {
        pwr_check_start = true;

        if (verb_out) {
          Serial1.println("Power check start");
        }
      }

      /* Check Power Supply */
      if (pwr_check_start && !RP_PSCheck()) {
        RP_reboot_cnt(false, false);  // Increase reboot counter
        RP_PWR_state = PWR_RST;
        first = true;

        if (verb_out) {
          Serial1.println("Power failure PWR UP");
        }
        break;
      }

      /* Check WDT start condition */
      if ((millis() - pwr_on_timer >= RP_WDT_BOOT_TIME + BOOT_DLY_TIME) && !wdt_start && !wdt_disable) {
        wdt_start = true;                           // Prevent recheck after first execution
        RP_WDTKickCheck(false, wdt_disable, true);  // Reset WDT timer

        if (verb_out) {
          Serial1.println("WDT start");
        }
      }

      /* Check WDT */
      if (wdt_start && RP_PSCheck()) {
        if (RP_WDTKickCheck(true, wdt_disable, false) == 0) {
          if (millis() - pwr_on_timer >= BOOT_TIME + BOOT_DLY_TIME) {  // If WDT works
            RP_PWR_state = PWR_ON;
            first = true;
          }
        } else {
          // Reset Red Pitaya and clear flags
          RP_reboot_cnt(false, false);  // Increase reboot counter
          RP_PWR_state = PWR_RST;
          first = true;

          if (verb_out) {
            Serial1.println("WDT fail PWR UP");
          }
          break;
        }
      }

      if (RP_power_on_off(false)) {
        RP_PWR_state = PWR_OFF;
        first = true;
      }

      // End PWR_UP state code
      break;

    case PWR_ON:

      if (first) {
        RP_powerup();                               // Turn on Red Pitaya power
        LED_blink(0, 0, true);                      // Reset LED states
        RP_WDTKickCheck(false, wdt_disable, true);  // Reset WDT
        first = false;                              // disable first time state
        wdt_start = true;                           // Start checking WDT

        LED_on(LED_GREEN_PIN);  // Turn on Green LED

        if (verb_out) {
          Serial1.println("PWR_ON");
        }
      }

      /* I2C forced state change */
      if (i2c_state_change) {
        i2c_state_change = false;
        RP_PWR_state = RP_E3_I2C_state;  // Change state to the requested one (no check if already in that state)
        first = true;
        break;
      }

      /* Fast LED blink */
      if (pwr_dwn_blink) {
        LED_blink(LED_GREEN_PIN, BLINK_TIME / LED_FAST_BLINK_DIVISOR, false);  // 4 Hz Green blink - ready to power down
      }

      /* WDT and power check */
      if ((RP_WDTKickCheck(true, wdt_disable, false) == 1) || !RP_PSCheck()) {
        RP_reboot_cnt(false, false);  // Increase reboot counter
        RP_PWR_state = PWR_RST;
        first = true;

        if (verb_out) {
          if (!RP_PSCheck()) {
            Serial1.println("Power failure PWR ON");
          } else {
            Serial1.println("WDT fail PWR ON");
          }
        }
        break;
      }

      /* Power off proceedure */
      if (RP_power_on_off(false)) {
        first = true;
        if (pwr_dwn_blink && RP_PSCheck()) {
          RP_PWR_state = PWR_DWN;
        } else {
          RP_PWR_state = PWR_OFF;
        }
      }

      // End PWR_ON state code
      break;

    case PWR_DWN_RST:  // Reboot after entering power down

      if (first) {
        RP_shutdown();               // Send shutdown signal to RP
        LED_blink(0, 0, true);       // Reset LED states
        RP_reboot_cnt(true, false);  // Reset boot time counter
        first = false;               // disable first time state
        shut_down_timer = millis();  // Start PWR RST timer

        if (verb_out) {
          Serial1.println("PWR_DWN_RST");
        }
      }

      /* I2C forced state change */
      if (i2c_state_change) {
        i2c_state_change = false;
        RP_PWR_state = RP_E3_I2C_state;  // Change state to the requested one (no check if already in that state)
        first = true;
        break;
      }

      /* Red LED blink */
      LED_blink(LED_RED_PIN, BLINK_TIME * LED_SLOW_BLINK_MULTIPLIER, false);  // 0.5 Hz

      /* Check for state switch conditions */  //! ?NEED TO CHECK PS_GOOD?
      if (!RP_PSCheck() || RP_power_on_off(false) || (millis() - shut_down_timer >= PWR_DOWN_TIME + PWR_DOWN_TIME_EXT)) {
        RP_PWR_state = PWR_RST;  // Switch to reset state
        first = true;
        if (!RP_PSCheck() && verb_out) {
          Serial1.println("Power failure PWR_DWN_RST");
        }
      }

      // End PWR_DWN_RST state code
      break;

    case PWR_OFF:

      if (first) {
        RP_poweroff();               // Turn off Red Pitaya power
        LED_blink(0, 0, true);       // Reset LED states and times
        LED_pwrOff_flash(true);      // Reset PWR OFF LED state and times
        RP_reboot_cnt(true, false);  // Reset boot time counter
        RP_power_on_off(true);       // Reset power_on_off flag
        first = false;

        if (verb_out) {
          Serial1.println("PWR_OFF");
        }
      }

      /* LED blink once every 10 s*/
      LED_pwrOff_flash(false);

      /* Power on proceedure */
      if (RP_power_on_off(false)) {
        RP_PWR_state = PWR_UP;
        first = true;
      }

      // End PWR_OFF state code
      break;

    case PWR_RST:

      // Start reset proceedure
      if (first) {
        RP_poweroff();            // Turn off Red Pitaya power
        LED_blink(0, 0, true);    // Reset LED states and times
        pwr_on_timer = millis();  // Boot timer
        first = false;

        if (verb_out) {
          Serial1.println("PWR_RST");
        }
      }

      /* Reboot after PWR_RST_TIME secods */
      if (millis() - pwr_on_timer >= PWR_RST_TIME) {
        /*
                // Check if the number of reboots is less than 3
                if (RP_reboot_cnt(false, true) < 3){
                    RP_PWR_state = PWR_UP;
                }
                else{
                    RP_PWR_state = PWR_FAIL;
                }
                */
        RP_PWR_state = PWR_UP;
        first = true;
      }

      /* Power off proceedure */
      if (RP_power_on_off(false)) {
        RP_PWR_state = PWR_OFF;
        first = true;
      }

      // End PWR_RST state code
      break;

    case PWR_FAIL:

      if (first) {
        RP_poweroff();               // Turn off Red Pitaya power
        LED_blink(0, 0, true);       // Reset LED states and times
        LED_pwrOff_flash(true);      // Reset PWR OFF LED state and times
        RP_reboot_cnt(true, false);  // Reset boot time counter
        RP_power_on_off(true);       // Reset power_on_off flag
        first = false;

        if (verb_out) {
          Serial1.println("PWR_FAIL");
        }
      }

      /* LED Blink */
      LED_on(LED_RED_PIN);  // Turn ON Red LED

      /* Power off proceedure */
      if (RP_power_on_off(false)) {
        RP_PWR_state = PWR_OFF;
        first = true;
      }

      // End PWR_FAIL state code
      break;

    default:
      // PWR_DWN (so that the board shuts down properly in case of program errors)

      if (first) {
        RP_shutdown();               // Send shutdown signal to RP
        LED_blink(0, 0, true);       // Reset LED states
        first = false;               // disable first time state
        shut_down_timer = millis();  // Start PWR OFF timer

        if (verb_out) {
          Serial1.println("PWR_DWN");
        }
      }

      /* I2C forced state change */
      if (i2c_state_change) {
        i2c_state_change = false;
        RP_PWR_state = RP_E3_I2C_state;  // Change state to the requested one (no check if already in that state)
        first = true;
        break;
      }

      /* Red LED blink */
      LED_blink(LED_RED_PIN, BLINK_TIME * LED_SLOW_BLINK_MULTIPLIER, false);  // 0.5 Hz

      /* Check for one of PWR_OFF condition */
      if (!RP_PSCheck() || RP_power_on_off(false) || (millis() - shut_down_timer >= PWR_DOWN_TIME + PWR_DOWN_TIME_EXT)) {
        // Immediately power down Red Pitaya and clear flags
        RP_PWR_state = PWR_OFF;
        first = true;

        if (!RP_PSCheck() && verb_out) {
          Serial1.println("Power failure PWR_DWN");
        }
      }

      // End PWR_DWN state code
      break;
  }
}
