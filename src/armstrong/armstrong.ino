/*
 *
 *    Source code for ArmStrong
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

// Create a new servo object:
Servo servoA;
Servo servoB;
Servo servoC;
Servo servoD;

// Define the servo pin:
#define servoAPin 9
#define servoBPin 10
#define servoCPin 11
#define servoDPin 12
#define servoEPin 5 //LED

#define servoAInitAngle 90
#define servoBInitAngle 90
#define servoCInitAngle 90
#define servoDInitAngle 90
#define servoEInitAngle 90

#define servoAMinAngle 0
#define servoAMaxAngle 180
#define servoBMinAngle 80
#define servoBMaxAngle 150
#define servoCMinAngle 36
#define servoCMaxAngle 180
#define servoDMinAngle 40
#define servoDMaxAngle 90
#define servoEMinAngle 0
#define servoEMaxAngle 180

#define potentiometerAPin A3
#define potentiometerBPin A2
#define potentiometerCPin A0
#define potentiometerDPin A1
#define potentiometerEPin A4

// Create a variable to store the servo position:
int servoAAngle;
int servoBAngle;
int servoCAngle;
int servoDAngle;
int servoEAngle;

int potentiometerA;
int potentiometerB;
int potentiometerC;
int potentiometerD;
int potentiometerE;

int servoARange;
int servoBRange;
int servoCRange;
int servoDRange;
int servoERange;

float scaleA;
float scaleB;
float scaleC;
float scaleD;
float scaleE;

void setup()
{
  // Create a variable to store the servo position:
  servoAAngle = servoAInitAngle;
  servoBAngle = servoBInitAngle;
  servoCAngle = servoCInitAngle;
  servoDAngle = servoDInitAngle;
  servoEAngle = servoEInitAngle;

  potentiometerA = 0;
  potentiometerB = 0;
  potentiometerC = 0;
  potentiometerD = 0;
  potentiometerE = 0;

  servoARange = servoAMaxAngle - servoAMinAngle;
  servoBRange = servoBMaxAngle - servoBMinAngle;
  servoCRange = servoCMaxAngle - servoCMinAngle;
  servoDRange = servoDMaxAngle - servoDMinAngle;
  servoERange = servoEMaxAngle - servoEMinAngle;

  scaleA = servoARange / 1024.0;
  scaleB = servoBRange / 1024.0;
  scaleC = servoCRange / 1024.0;
  scaleD = servoDRange / 1024.0;
  scaleE = servoERange / 1024.0;

  Serial.begin(9600); //  setup serial
  // Attach the Servo variable to a pin:
  servoA.attach(servoAPin);
  servoA.write(servoAAngle);

  servoB.attach(servoBPin);
  servoB.write(servoBAngle);

  servoC.attach(servoCPin);
  servoC.write(servoCAngle);

  servoD.attach(servoDPin);
  servoD.write(servoDAngle);

  pinMode(servoEPin, OUTPUT); // sets the pin as output
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

  analogWrite(servoEPin, potentiometerE / 4);
}
