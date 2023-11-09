#include <Wire.h>
#include <Adafruit_PN532.h>
#include <Arduino.h>
#include <Servo.h>

Servo myServo;  // Create a servo object

#define SDA_PIN 21
#define SCL_PIN 22
#define stepPin 32
#define dirPin 33
#define enPin 25
#define pointsens 13

Adafruit_PN532 nfc(SDA_PIN, SCL_PIN);

#if defined(ESP32)
#include <WiFi.h>
#elif defined(ESP8266)
#include <ESP8266WiFi.h>
#endif

#include <Firebase_ESP_Client.h>
#include "addons/TokenHelper.h"
#include "addons/RTDBHelper.h"
// Insert your network credentials
#define WIFI_SSID "Oi_robotics_Network"
#define WIFI_PASSWORD "Oi_robotics2020"

// Insert Firebase project API Key
#define API_KEY "AIzaSyBg34dGNZDx-yRdxymsfIBroH_yngnaZqM"

// Insert RTDB URLefine the RTDB URL */
#define DATABASE_URL "https://trashmaster-ea7f8-default-rtdb.firebaseio.com/" 

FirebaseData fbdo;
FirebaseAuth auth;
FirebaseConfig config;

unsigned long sendDataPrevMillis = 0;
int count = 0;
bool signupOK = false;

//-----------------
int pointer = 0 ; // 0 = plastic , 1 = metal , 2 = glass , 3 = paper 
int type = 0 ; // 0 = plastic , 1 = metal , 2 = glass , 3 = paper
int plastic = 0;
int metal = 0;
int glass = 0;
int paper = 0; 
//----------------


void setup() {
  myServo.attach(9);
  pinMode(stepPin,OUTPUT); 
  pinMode(dirPin,OUTPUT);
  pinMode(enPin,OUTPUT);
  pinMode(pointsens,INPUT);
  digitalWrite(enPin,LOW);
  
  Serial.begin(115200);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(300);
  }
  Serial.println();
  Serial.print("Connected with IP: ");
  Serial.println(WiFi.localIP());
  Serial.println();

  config.api_key = API_KEY;
  config.database_url = DATABASE_URL;

  if (Firebase.signUp(&config, &auth, "", "")) {
    Serial.println("Sign up successful");
    signupOK = true;
  } else {
    Serial.printf("Sign up failed: %s\n", config.signer.signupError.message.c_str());
  }

  config.token_status_callback = tokenStatusCallback;

  Firebase.begin(&config, &auth);
  Firebase.reconnectWiFi(true);
  nfc.begin();
  uint32_t versiondata = nfc.getFirmwareVersion();
  while(!versiondata ) {
    Serial.println("Didn't find PN53x board");
    nfc.begin();
    uint32_t versiondata = nfc.getFirmwareVersion();
    nfc.SAMConfig();
  }
  initialize();
  Serial.println("Waiting for an NFC card ...");
  myServo.write(0);
}

int cardValues[] = {520176, 621179, 622223};

uint8_t knownCards[][4] = {
  {0x83, 0x9F, 0x37, 0xC1},
  {0x33, 0x3B, 0xE6, 0xC3},
  {0x43, 0x13, 0x2B, 0xC2},
};

void loop() {
  uint8_t success;
  uint8_t uid[] = {0, 0, 0, 0, 0, 0, 0};
  uint8_t uidLength;

  success = nfc.readPassiveTargetID(PN532_MIFARE_ISO14443A, uid, &uidLength);

  if (success) {
    //Serial.println("Found an NFC card!");

    //Serial.print("UID Length: ");
    //Serial.print(uidLength, DEC);
    //Serial.println(" bytes");
    //Serial.print("UID Value: ");

    int cardValue = -1;

    for (int i = 0; i < sizeof(knownCards) / sizeof(knownCards[0]); i++) {
      bool match = true;
      for (int j = 0; j < uidLength; j++) {
        if (uid[j] != knownCards[i][j]) {
          match = false;
          break;
        }
      }
      if (match) {
        cardValue = cardValues[i];
        //Serial.print("Card ");
        //Serial.println(i + 1);
        break;
      }
    }

    if (cardValue == -1) {
      Serial.println("Unknown Card");
    } else {
      Serial.print("Card Value: ");
      Serial.println(cardValue);
      String collected = "";
      while(collected != "Done") {
        while (Serial.available() == 0) {
        }
        collected = Serial.readString();
        if (collected == "Plastic") {
          change_dir(0);
          plastic++;
        } else if (collected == "Glass") {
          change_dir(1);
          glass++;
 
        } else if (collected == "Metal") {
          change_dir(2);
          metal++;
        } else if (collected == "Paper") {
          change_dir(3);
          paper++;
        }
      } 
      if (Firebase.ready() && signupOK && (millis() - sendDataPrevMillis > 15000 || sendDataPrevMillis == 0)) {
        sendDataPrevMillis = millis();
        Firebase.RTDB.setInt(&fbdo, "user/" + String(cardValue) + "/paper", Firebase.RTDB.getInt(&fbdo, "user/" + String(cardValue) + "/paper") + paper);
        Firebase.RTDB.setInt(&fbdo, "user/" + String(cardValue) + "/plastic",Firebase.RTDB.getInt(&fbdo, "user/" + String(cardValue) + "/plastic") +  plastic);
        Firebase.RTDB.setInt(&fbdo, "user/" + String(cardValue) + "/metal", Firebase.RTDB.getInt(&fbdo, "user/" + String(cardValue) + "/metal") + metal);
        Firebase.RTDB.setInt(&fbdo, "user/" + String(cardValue) + "/glass", Firebase.RTDB.getInt(&fbdo, "user/" + String(cardValue) + "/glass") + glass);
        Firebase.RTDB.setInt(&fbdo, "user/" + String(cardValue) + "/points", Firebase.RTDB.getInt(&fbdo, "user/" + String(cardValue) + "/points") + count);
      }
      Serial.println("Sent");  
      delay(1000);
    }
  }
}

void change_dir(int type) {
  digitalWrite(dirPin,LOW); //Changes the direction of rotation
  for(int x = 0; x < type*800; x++) {
    //Serial.println('.');
    digitalWrite(stepPin,HIGH);
    delayMicroseconds(500);
    digitalWrite(stepPin,LOW);
    delayMicroseconds(500);
  }
  myServo.write(90);
  //Serial.println("Change");
  delay(5000);
  myServo.write(0);
  initialize();
}

void initialize(){
//  Serial.println("Init");
  while (digitalRead(pointsens)){
    //Serial.println(digitalRead(pointsens));
    digitalWrite(dirPin,LOW); //Changes the direction of rotation
    digitalWrite(stepPin,HIGH);
    delayMicroseconds(500);
    digitalWrite(stepPin,LOW);
    delayMicroseconds(500);
  }
  pointer = 0;
  //Serial.println("Done");
}
