/*
 *
 *    ArmStrong source code on Arduino Nano
 *
 *    ----------
 *    3D printed robot arm
 *    Copyright (C) 2021 - PRESENT  Zhengyu Peng
 *    E-mail: zpeng.me@gmail.com
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

#include <Servo.h>

// Create servo objects:
Servo servoA; // control base 'left <-> right'
Servo servoB; // control arm 'extend <-> retreat'
Servo servoC; // control hand 'close <-> open'
Servo servoD; // control arm 'up <-> down'

// Define the servo pins:
#define servoAPin 9
#define servoBPin 10
#define servoCPin 11
#define servoDPin 12

// Define the LED pin:
#define ledPin 5

// Define servo rotation range:
#define servoAMinAngle 0
#define servoAMaxAngle 180
#define servoBMinAngle 80
#define servoBMaxAngle 150
#define servoCMinAngle 36
#define servoCMaxAngle 180
#define servoDMinAngle 40
#define servoDMaxAngle 90

// Define potentiometer pins:
#define potentiometerAPin A3
#define potentiometerBPin A2
#define potentiometerCPin A0
#define potentiometerDPin A1
#define potentiometerEPin A4

// Variables to store the servo positions:
int servoAAngle;
int servoBAngle;
int servoCAngle;
int servoDAngle;

// Variables to store the potentiometer positions:
int potentiometerA;
int potentiometerB;
int potentiometerC;
int potentiometerD;
int potentiometerE;

int servoARange;
int servoBRange;
int servoCRange;
int servoDRange;

float scaleA;
float scaleB;
float scaleC;
float scaleD;

void setup()
{
  Serial.begin(9600); //  setup serial

  servoARange = servoAMaxAngle - servoAMinAngle;
  servoBRange = servoBMaxAngle - servoBMinAngle;
  servoCRange = servoCMaxAngle - servoCMinAngle;
  servoDRange = servoDMaxAngle - servoDMinAngle;

  scaleA = servoARange / 1024.0;
  scaleB = servoBRange / 1024.0;
  scaleC = servoCRange / 1024.0;
  scaleD = servoDRange / 1024.0;

  // Initialize servos one by one to avoid large curren draw
  potentiometerA = analogRead(potentiometerAPin); // read the input pin
  servoAAngle = potentiometerA * scaleA + servoAMinAngle;
  servoA.attach(servoAPin);
  servoA.write(servoAAngle);
  delay(500);

  potentiometerB = analogRead(potentiometerBPin); // read the input pin
  servoBAngle = potentiometerB * scaleB + servoBMinAngle;
  servoB.attach(servoBPin);
  servoB.write(servoBAngle);
  delay(500);

  potentiometerC = analogRead(potentiometerCPin); // read the input pin
  servoCAngle = potentiometerC * scaleC + servoCMinAngle;
  servoC.attach(servoCPin);
  servoC.write(servoCAngle);
  delay(500);

  potentiometerD = analogRead(potentiometerDPin); // read the input pin
  servoDAngle = potentiometerD * scaleD + servoDMinAngle;
  servoD.attach(servoDPin);
  servoD.write(servoDAngle);
  delay(500);

  pinMode(ledPin, OUTPUT); // sets the pin as output
}

void loop()
{
  potentiometerA = analogRead(potentiometerAPin); // read the input pin
  potentiometerB = analogRead(potentiometerBPin); // read the input pin
  potentiometerC = analogRead(potentiometerCPin); // read the input pin
  potentiometerD = analogRead(potentiometerDPin); // read the input pin
  potentiometerE = analogRead(potentiometerEPin); // read the input pin

  servoAAngle = potentiometerA * scaleA + servoAMinAngle;
  servoA.write(servoAAngle);
  servoBAngle = potentiometerB * scaleB + servoBMinAngle;
  servoB.write(servoBAngle);
  servoCAngle = potentiometerC * scaleC + servoCMinAngle;
  servoC.write(servoCAngle);
  servoDAngle = potentiometerD * scaleD + servoDMinAngle;
  servoD.write(servoDAngle);

  analogWrite(ledPin, potentiometerE / 4);
}
