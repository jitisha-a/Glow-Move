#include <Arduino.h>

// digital pins wiring legend for red, green, blue colours
const int RED_PINS[]   = {2, 3, 4};
const int GREEN_PINS[] = {5, 6, 7};
const int BLUE_PINS[] = {8, 9};

// pins wiring for RGB led that makes up yellow
const int RGB_R = 10;
const int RGB_G = 11;
const int RGB_B = 12;   

const int BUZZER_PIN = 13; // buzzer digital pin

// to get size of pins arrays
const int RED_N   = sizeof(RED_PINS) / sizeof(RED_PINS[0]);
const int GREEN_N = sizeof(GREEN_PINS) / sizeof(GREEN_PINS[0]);
const int BLUE_N = sizeof(BLUE_PINS) / sizeof(BLUE_PINS[0]);

// creating an empty string to later store the data recieved by rpi over serial
String buf = "";

// helper function to turn colours (so a group of leds) on or off
void setPins(const int *pins, int n, bool on) {
  for (int i = 0; i < n; i++) digitalWrite(pins[i], on ? HIGH : LOW);
}

// helper function to turn off colours
void allOff() {
  setPins(RED_PINS, RED_N, false);
  setPins(GREEN_PINS, GREEN_N, false);
  setPins(BLUE_PINS, BLUE_N, false);

  // for RGB common cathode, HIGH turns on a color channel, so using LOW
  digitalWrite(RGB_R, LOW);
  digitalWrite(RGB_G, LOW);
  digitalWrite(RGB_B, LOW);
}

void buzzerOn() {
  digitalWrite(BUZZER_PIN, HIGH);
}

void buzzerOff() {
  digitalWrite(BUZZER_PIN, LOW);
}

// some tunes 
void playStartTune() {
  buzzerOn();
  delay(200);
  buzzerOff();
  delay(100);
  buzzerOn();
  delay(200);
  buzzerOff();
}

void playEndTune() {
  buzzerOn();
  delay(600);
  buzzerOff();
}

// helper function to turn on just one colour
void showColor(const String &c) {
  allOff();

  if (c == "RED") {
    setPins(RED_PINS, RED_N, true);
  } else if (c == "GREEN") {
    setPins(GREEN_PINS, GREEN_N, true);
  } else if (c == "BLUE") {
    setPins(BLUE_PINS, BLUE_N, true);
  } else if (c == "YELLOW") {
    // yellow only
    digitalWrite(RGB_R, HIGH);
    digitalWrite(RGB_G, HIGH);
    digitalWrite(RGB_B, LOW);
  } else {
    // OFF or unknown...
    allOff();
  }
}

// helper function to handle serial info from rpi
void handleLine(String line) {
  line.trim(); // to remove any spaces or new lines
  line.toUpperCase(); // standardising 
  
  if (line.length() == 0) return;
  if (line == "OFF") showColor("OFF");
  else if (line == "RED") showColor("RED");
  else if (line == "GREEN") showColor("GREEN");
  else if (line == "BLUE") showColor("BLUE");
  else if (line == "YELLOW") showColor("YELLOW");
  else if (line == "START") {
    playStartTune();
  } else if (line == "END") {
    playEndTune();
}
}

void setup() {
  for (int i = 0; i < RED_N; i++) pinMode(RED_PINS[i], OUTPUT);
  for (int i = 0; i < GREEN_N; i++) pinMode(GREEN_PINS[i], OUTPUT);
  for (int i = 0; i < BLUE_N; i++) pinMode(BLUE_PINS[i], OUTPUT);

  pinMode(RGB_R, OUTPUT);
  pinMode(RGB_G, OUTPUT);
  pinMode(RGB_B, OUTPUT);

  pinMode(BUZZER_PIN, OUTPUT);

  allOff();
  Serial.begin(115200);
}

void loop() {
  while (Serial.available() > 0) { // runs while bytes are sent from rpi over serial
    char ch = (char)Serial.read();
    if (ch == '\n' || ch == '\r') { // new line / enter means the incoming "line" (colour command) has finished
      if (buf.length() > 0) {
        handleLine(buf); // process the serial info colour command
        buf = ""; // reset this string for next serial informations
      }
    } else {
      buf += ch;
      if (buf.length() > 64) buf = ""; // just in case some error and message too long, just throw out
    }
  }
}
