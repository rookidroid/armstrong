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

#define servoAInitAngle 90
#define servoBInitAngle 90
#define servoCInitAngle 90
#define servoDInitAngle 90

#define servoAMinAngle 0
#define servoAMaxAngle 180
#define servoBMinAngle 80
#define servoBMaxAngle 140
#define servoCMinAngle 15
#define servoCMaxAngle 85
#define servoDMinAngle 36
#define servoDMaxAngle 180

#define potentiometerAPin A0
#define potentiometerBPin A1
#define potentiometerCPin A2
#define potentiometerDPin A3

// Create a variable to store the servo position:
int servoAAngle;
int servoBAngle;
int servoCAngle;
int servoDAngle;

int potentiometerA;
int potentiometerB;
int potentiometerC;
int potentiometerD;

int servoARange;
int servoBRange;
int servoCRange;
int servoDRange;

float scaleA;
float scaleB;
float scaleC;
float scaleD;

void setup() {
  // Create a variable to store the servo position:
  servoAAngle = servoAInitAngle;
  servoBAngle = servoBInitAngle;
  servoCAngle = servoCInitAngle;
  servoDAngle = servoDInitAngle;
  
  potentiometerA = 0;
  potentiometerB = 0;
  potentiometerC = 0;
  potentiometerD = 0;
  
  servoARange = servoAMaxAngle - servoAMinAngle;
  servoBRange = servoBMaxAngle - servoBMinAngle;
  servoCRange = servoCMaxAngle - servoCMinAngle;
  servoDRange = servoDMaxAngle - servoDMinAngle;
  
  scaleA = servoARange/1024.0;
  scaleB = servoBRange/1024.0;
  scaleC = servoCRange/1024.0;
  scaleD = servoDRange/1024.0;

  
  Serial.begin(9600);           //  setup serial
  // Attach the Servo variable to a pin:
  servoA.attach(servoAPin);
  servoA.write(servoAAngle);

  servoB.attach(servoBPin);
  servoB.write(servoBAngle);

  servoC.attach(servoCPin);
  servoC.write(servoCAngle);

  servoD.attach(servoDPin);
  servoD.write(servoDAngle);
}

void loop() {
   potentiometerA = analogRead(potentiometerAPin);  // read the input pin
//   Serial.println("A: "); 
//   Serial.println(potentiometerA);          // debug value
   potentiometerB = analogRead(potentiometerBPin);  // read the input pin
//   Serial.println("B: "); 
//   Serial.println(potentiometerB);          // debug value
   potentiometerC = analogRead(potentiometerCPin);  // read the input pin
//   Serial.println("C: "); 
//   Serial.println(potentiometerC);          // debug value
   potentiometerD = analogRead(potentiometerDPin);  // read the input pin
//   Serial.println("D: "); 
//   Serial.println(potentiometerD);          // debug value
//
//   Serial.println(scaleA);

   servoAAngle = potentiometerA*scaleA+servoAMinAngle;
   servoA.write(servoAAngle);
//   Serial.println("A angle: "); 
//   Serial.println(servoAAngle);
   servoBAngle = potentiometerB*scaleB+servoBMinAngle;
   servoB.write(servoBAngle);
//   Serial.println("B angle: "); 
//   Serial.println(servoBAngle);
   servoCAngle = potentiometerC*scaleC+servoCMinAngle;
   servoC.write(servoCAngle);
//   Serial.println("C angle: "); 
//   Serial.println(servoCAngle);
   servoDAngle = potentiometerD*scaleD+servoDMinAngle;
   servoD.write(servoDAngle);
//   Serial.println("D angle: "); 
//   Serial.println(servoDAngle);

//   delay(1000);

}
