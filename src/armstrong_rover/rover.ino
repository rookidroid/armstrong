#include <WiFi.h>
#include <WiFiUdp.h>

#include <ESP32Servo.h>

#ifndef APSSID
#define APSSID "tank"
#define APPSK "tank1234"
#endif

/* Set these to your desired credentials. */
const char *ssid = APSSID;
const char *password = APPSK;

// buffers for receiving and sending data
char packetBuffer[4096 + 1];             // buffer to hold incoming packet,
char ReplyBuffer[] = "acknowledged\r\n"; // a string to send back

unsigned int localPort = 1234; // local port to listen on

WiFiUDP Udp;

Servo servo_l;
Servo servo_r;

const int MID = 1500;
const int MIN = 1000;
const int MAX = 2000;

const int center_var_x = 1850;
const int center_var_y = 1790;
const float scale_x_upper = (float)(MAX - MID) / (4096.0 - (float)center_var_x);
const float scale_x_lower = (float)(MAX - MID) / ((float)center_var_x);
const float scale_y_upper = (float)(MAX - MID) / (4096.0 - (float)center_var_y);
const float scale_y_lower = (float)(MAX - MID) / ((float)center_var_y);

int x_val = center_var_x;
int y_val = center_var_y;

float main_dutycycle = 0;
float offset_dutycycle = 0;

int left_duty;
int right_duty;

// Create servo objects:
Servo servoA; // control base 'left <-> right'
Servo servoB; // control arm 'extend <-> retreat'
Servo servoC; // control hand 'close <-> open'
Servo servoD; // control arm 'up <-> down'

// Define the servo pins:
#define servoAPin 5
#define servoBPin 18
#define servoCPin 19
#define servoDPin 21

// Define servo rotation range:
#define servoAMinAngle 0
#define servoAMaxAngle 180
#define servoBMinAngle 75
#define servoBMaxAngle 170
#define servoCMinAngle 25
#define servoCMaxAngle 110
#define servoDMinAngle 0
#define servoDMaxAngle 180

// Variables to store the servo positions:
int servoAAngle;
int servoBAngle;
int servoCAngle;
int servoDAngle;

int servoARange;
int servoBRange;
int servoCRange;
int servoDRange;

float scaleA;
float scaleB;
float scaleC;
float scaleD;

bool rover = false;
bool arm = false;

int str_idx;
String inputString = "";

void setup()
{
  delay(1000);
  Serial.begin(115200);
  //  Serial.println();
  //  Serial.print("Configuring access point...");
  /* You can remove the password parameter if you want the AP to be open. */
  WiFi.softAP(ssid, password);

  IPAddress myIP = WiFi.softAPIP();
  Serial.print("AP IP address: ");
  Serial.println(myIP);

  Udp.begin(localPort);

  // Attach the ESC on pin 9
  servo_l.attach(14, MIN, MAX); // (pin, min pulse width, max pulse width in microseconds);
  servo_r.attach(33, MIN, MAX); // (pin, min pulse width, max pulse width in microseconds);

  servo_l.writeMicroseconds(MID); // Send the signal to the ESC
  servo_r.writeMicroseconds(MID);

  servoA.attach(servoAPin);
  servoB.attach(servoBPin);
  servoC.attach(servoCPin);
  servoD.attach(servoDPin);

  servoARange = servoAMaxAngle - servoAMinAngle;
  servoBRange = servoBMaxAngle - servoBMinAngle;
  servoCRange = servoCMaxAngle - servoCMinAngle;
  servoDRange = servoDMaxAngle - servoDMinAngle;

  scaleA = servoARange / 4096.0;
  scaleB = servoBRange / 4096.0;
  scaleC = servoCRange / 4096.0;
  scaleD = servoDRange / 4096.0;
}

void loop()
{
  // if there's data available, read a packet
  int packetSize = Udp.parsePacket();
  if (packetSize)
  {
    rover = false;
    arm = false;

    // read the packet into packetBufffer
    int n = Udp.read(packetBuffer, 4096);
    packetBuffer[n] = 0;

    for (str_idx = 0; str_idx < n; str_idx++)
    {
      char inChar = packetBuffer[str_idx];
      //      Serial.print(inChar);
      //      Serial.print("\n");

      if (inChar != '\n' && inChar != ':')
      {
        // add it to the inputString:
        inputString += inChar;
      }
      else if (inChar == ':')
      {
        if (inputString[0] == 'X')
        {
          int sLength = inputString.length();
          String tempStr = inputString.substring(1, sLength);
          x_val = tempStr.toInt();
          rover = true;
        }
        else if (inputString[0] == 'Y')
        {
          int sLength = inputString.length();
          String tempStr = inputString.substring(1, sLength);
          y_val = tempStr.toInt();
          rover = true;
        }
        else if (inputString[0] == 'A')
        {
          int sLength = inputString.length();
          String tempStr = inputString.substring(1, sLength);
          servoAAngle = tempStr.toInt() * scaleA + servoAMinAngle;
          arm = true;
        }
        else if (inputString[0] == 'B')
        {
          int sLength = inputString.length();
          String tempStr = inputString.substring(1, sLength);
          servoBAngle = tempStr.toInt() * scaleB + servoBMinAngle;
          arm = true;
        }
        else if (inputString[0] == 'C')
        {
          int sLength = inputString.length();
          String tempStr = inputString.substring(1, sLength);
          servoCAngle = tempStr.toInt() * scaleC + servoCMinAngle;
          arm = true;
        }
        else if (inputString[0] == 'D')
        {
          int sLength = inputString.length();
          String tempStr = inputString.substring(1, sLength);
          servoDAngle = tempStr.toInt() * scaleD + servoDMinAngle;
          arm = true;
        }
        inputString = "";
      }
    }

    if (rover)
    {
      if (y_val >= center_var_y)
      {
        main_dutycycle = (float)(center_var_y - y_val) * scale_y_upper;
      }
      else
      {
        main_dutycycle = (float)(center_var_y - y_val) * scale_y_lower;
      }
  
      if (x_val >= center_var_x)
      {
        offset_dutycycle = (float)(center_var_x - x_val) * scale_x_upper;
      }
      else
      {
        offset_dutycycle = (float)(center_var_x - x_val) * scale_x_lower;
      }
  
      left_duty = round(-(main_dutycycle + offset_dutycycle) + MID);
      right_duty = round(-(main_dutycycle - offset_dutycycle) + MID);
  
      if (left_duty >= MIN && left_duty <= MAX)
      {
        servo_l.writeMicroseconds(left_duty);
      }
      else if (left_duty < MIN)
      {
        servo_l.writeMicroseconds(MIN);
      }
      else if (left_duty > MAX)
      {
        servo_l.writeMicroseconds(MAX);
      }
  
      if (right_duty >= MIN && right_duty <= MAX)
      {
        servo_r.writeMicroseconds(right_duty);
      }
      else if (right_duty < MIN)
      {
        servo_r.writeMicroseconds(MIN);
      }
      else if (right_duty > MAX)
      {
        servo_r.writeMicroseconds(MAX);
      }
    }

    if (arm)
    {
      servoA.write(servoAAngle);
      servoB.write(servoBAngle);
      servoC.write(servoCAngle);
      servoD.write(servoDAngle);

      Serial.print(servoDAngle);
      Serial.print("\n");
    }

//    Serial.print(packetBuffer);
//    Serial.print("\nleft");
//    Serial.print(left_duty);
//    Serial.print("\nright");
//    Serial.print(right_duty);
//    Serial.print("\n");
  }
}
