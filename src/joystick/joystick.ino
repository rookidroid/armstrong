/*
 *
 *    This sketch is for the WiFi joystick
 *
 *    ----------
 *    Copyright (C) 2022 - PRESENT  Zhengyu Peng
 *    Website: https://zpeng.me
 *
 *    `                      `
 *    -:.                  -#:
 *    -//:.              -###:
 *    -////:.          -#####:
 *    -/:.://:.      -###++##:
 *    ..   `://:-  -###+. :##:
 *           `:/+####+.   :##:
 *    .::::::::/+###.     :##:
 *    .////-----+##:    `:###:
 *     `-//:.   :##:  `:###/.
 *       `-//:. :##:`:###/.
 *         `-//:+######/.
 *           `-/+####/.
 *             `+##+.
 *              :##:
 *              :##:
 *              :##:
 *              :##:
 *              :##:
 *               .+:
 *
 */

#include <WiFi.h>
#include <WiFiUdp.h>

// GPIO pin number for the LEDs
#define PIN_GREEN 27
#define PIN_YELLOW 26
#define PIN_BLUE 25

// GPIO pin number for the joystick
#define PIN_Y 35
#define PIN_X 34
#define PIN_SW 4

// GPIO pin number for the pot
#define PIN_A 33
#define PIN_B 32
#define PIN_C 39
#define PIN_D 36

// PWM channels
#define PWM_GREEN 0
#define PWM_YELLOW 1
#define PWM_BLUE 2

// WiFi parameters
const char *ssid = "tank";
const char *password = "tank1234";
//const char *ssid = "emmawifi";
//const char *password = "8067868889";
boolean connected = false;

// UDP
WiFiUDP udp;
const char *udpAddress = "192.168.4.1";
//const char *udpAddress = "192.168.1.202";
const int udpPort = 1234;

// PWM properties
const int pwmFreq = 5000;
const int pwmResolution = 8;

// joystick values
int valX = 0;
int valY = 0;
int valSw = 0;

int valA = 0;
int valB = 0;
int valC = 0;
int valD = 0;

// old joystick values
int valX_old = 0;
int valY_old = 0;
int valSw_old = 0;

int valA_old = 0;
int valB_old = 0;
int valC_old = 0;
int valD_old = 0;

void setup()
{
    adcAttachPin(PIN_Y);
    adcAttachPin(PIN_X);

    adcAttachPin(PIN_A);
    adcAttachPin(PIN_B);
    adcAttachPin(PIN_C);
    adcAttachPin(PIN_D);
    
    analogSetClockDiv(64);
  
    // initilize hardware serial:
    Serial.begin(921600);

    // configure joystick pin mode
    pinMode(PIN_Y, ANALOG);
    pinMode(PIN_X, ANALOG);

    pinMode(PIN_A, ANALOG);
    pinMode(PIN_B, ANALOG);
    pinMode(PIN_C, ANALOG);
    pinMode(PIN_D, ANALOG);
    pinMode(PIN_SW, INPUT_PULLUP);

    // configure LED PWM functionalitites
    pinMode(PIN_GREEN, OUTPUT);
    pinMode(PIN_YELLOW, OUTPUT);
    pinMode(PIN_BLUE, OUTPUT);

    ledcSetup(PWM_GREEN, pwmFreq, pwmResolution);
    ledcAttachPin(PIN_GREEN, PWM_GREEN);

    ledcSetup(PWM_YELLOW, pwmFreq, pwmResolution);
    ledcAttachPin(PIN_YELLOW, PWM_YELLOW);

    ledcSetup(PWM_BLUE, pwmFreq, pwmResolution);
    ledcAttachPin(PIN_BLUE, PWM_BLUE);

    // blink LEDs
    ledcWrite(PWM_GREEN, 1);
    ledcWrite(PWM_YELLOW, 1);
    ledcWrite(PWM_BLUE, 1);
    delay(1000);
    ledcWrite(PWM_GREEN, 0);
    ledcWrite(PWM_YELLOW, 0);
    ledcWrite(PWM_BLUE, 0);

    // connect to the WiFi network
    connectToWiFi(ssid, password);
}

void loop()
{
    valX = analogRead(PIN_X);
    valY = analogRead(PIN_Y);
    valSw = digitalRead(PIN_SW);

    valA = analogRead(PIN_A);
    valB = analogRead(PIN_B);
    valC = analogRead(PIN_C);
    valD = analogRead(PIN_D);

    int temp_valX = floor(valX/32);
    int temp_valY = floor(valY/32);

    int temp_valX_old = floor(valX_old/32);
    int temp_valY_old = floor(valY_old/32);

    // only send UDP when the joystick is moved
    if ((temp_valX != temp_valX_old) || (temp_valY != temp_valY_old) || (valSw != valSw_old))
    {
        valX_old = valX;
        valY_old = valY;
        valSw_old = valSw;
        if (connected)
        {
            ledcWrite(PWM_BLUE, 1);
            // send joystick values to the UDP server
            udp.beginPacket(udpAddress, udpPort);
            udp.printf("X%d:Y%d:S%d:", valX, valY, valSw);
//            udp.printf("X%d:Y%d:S%d:", temp_valX, temp_valY, valSw);
            udp.endPacket();
            ledcWrite(PWM_BLUE, 0);
        }
    }


    int temp_valA = floor(valA/8);
    int temp_valB = floor(valB/8);
    int temp_valC = floor(valC/8);
    int temp_valD = floor(valD/8);

    int temp_valA_old = floor(valA_old/8);
    int temp_valB_old = floor(valB_old/8);
    int temp_valC_old = floor(valC_old/8);
    int temp_valD_old = floor(valD_old/8);

    if ((temp_valA != temp_valA_old) || (temp_valB != temp_valB_old) || (temp_valC != temp_valC_old) || (temp_valD != temp_valD_old))
    {
        valA_old = valA;
        valB_old = valB;
        valC_old = valC;
        valD_old = valD;

        if (connected)
        {
            ledcWrite(PWM_BLUE, 1);
            // send joystick values to the UDP server
            udp.beginPacket(udpAddress, udpPort);
            udp.printf("A%d:B%d:C%d:D%d:", valA, valB, valC, valD);
//            udp.printf("X%d:Y%d:S%d:", temp_valX, temp_valY, valSw);
            udp.endPacket();
            ledcWrite(PWM_BLUE, 0);
        }
    }
    delay(100);
}

void connectToWiFi(const char *ssid, const char *pwd)
{
    ledcWrite(PWM_YELLOW, 1);
    Serial.println("Connecting to WiFi network: " + String(ssid));

    // delete old config
    WiFi.disconnect(true);
    // register event handler
    WiFi.onEvent(WiFiEvent);

    // initiate connection
    WiFi.begin(ssid, pwd);

    Serial.println("Waiting for WIFI connection...");
}

// WiFi event handler
void WiFiEvent(WiFiEvent_t event)
{
    switch (event)
    {
    case ARDUINO_EVENT_WIFI_STA_GOT_IP:
        // when connected set
        Serial.print("WiFi connected! IP address: ");
        Serial.println(WiFi.localIP());
        // initializes the UDP state
        // this initializes the transfer buffer
        udp.begin(WiFi.localIP(), udpPort);
        connected = true;
        ledcWrite(PWM_YELLOW, 0);
        ledcWrite(PWM_GREEN, 1);
        break;
    case ARDUINO_EVENT_WIFI_STA_DISCONNECTED:
        Serial.println("WiFi lost connection");
        connected = false;
        ledcWrite(PWM_YELLOW, 1);
        ledcWrite(PWM_GREEN, 0);
        break;
    default:
        break;
    }
}
