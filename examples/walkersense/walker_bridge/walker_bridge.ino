// WalkerSense — MCU side (STM32H5, Zephyr core), v2
// Linux -> Arduino Bridge (MsgPack RPC via arduino-router) providers:
//   matrix_fill(bool on)                    -> LED matrix all on/off (visible ack)
//   servo_set(int pin, int pulse_us)        -> set target pulse for a servo pin
//   servo_run(int frames)                   -> emit `frames` 20ms frames of pulses
//   servo_stop()                            -> clear all servo targets
// Servo pulses are generated in software (precise delayMicroseconds timing),
// so any digital pin works and no PWM/DTS config is involved.
// SAFETY: pulse clamped to [500, 2500] us; frames clamped to [1, 100] (= max 2 s).

#include <Arduino_RouterBridge.h>
#include <Arduino_LED_Matrix.h>

Arduino_LED_Matrix matrix;

static uint32_t FRAME_ON[4]  = {0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF};
static uint32_t FRAME_OFF[4] = {0, 0, 0, 0};

bool matrix_fill(bool on) {
  matrix.loadFrame(on ? FRAME_ON : FRAME_OFF);
  return true;
}

// ---- servos -------------------------------------------------------------
#define MAX_SERVOS 8
static int servo_pin[MAX_SERVOS];
static int servo_us[MAX_SERVOS];
static int servo_count = 0;

static int clamp_us(int us) { return us < 500 ? 500 : (us > 2500 ? 2500 : us); }

bool servo_set(int pin, int us) {
  for (int i = 0; i < servo_count; i++) {
    if (servo_pin[i] == pin) { servo_us[i] = clamp_us(us); return true; }
  }
  if (servo_count >= MAX_SERVOS) return false;
  pinMode(pin, OUTPUT);
  digitalWrite(pin, LOW);
  servo_pin[servo_count] = pin;
  servo_us[servo_count] = clamp_us(us);
  servo_count++;
  return true;
}

bool servo_run(int frames) {
  if (frames < 1) frames = 1;
  if (frames > 100) frames = 100;
  for (int f = 0; f < frames; f++) {
    unsigned long frame_start = micros();
    for (int i = 0; i < servo_count; i++) {
      digitalWrite(servo_pin[i], HIGH);
      delayMicroseconds(servo_us[i]);
      digitalWrite(servo_pin[i], LOW);
    }
    unsigned long elapsed = micros() - frame_start;
    if (elapsed < 20000UL) delayMicroseconds(20000UL - elapsed);
  }
  return true;
}

bool servo_stop() {
  servo_count = 0;
  return true;
}

void setup() {
  matrix.begin();
  matrix.loadFrame(FRAME_OFF);
  Bridge.begin();
  Bridge.provide("matrix_fill", matrix_fill);
  Bridge.provide("servo_set", servo_set);
  Bridge.provide("servo_run", servo_run);
  Bridge.provide("servo_stop", servo_stop);
}

void loop() {
  delay(100);
}
