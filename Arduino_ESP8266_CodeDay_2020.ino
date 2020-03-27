#define DEBUG 1  //Print to Serial
#define PRINTDEBUG(STR) \
  {  \
    if (DEBUG) Serial.println(STR); \
  } //PRINTDEBUG prints lines to serial

#include <ESP8266WiFi.h>

//initialize variables
const char* ssid     = " ";
const char* password = " ";
//WiFi.hostname("SMARTLOCK"); // does not work for whatever reason
WiFiClient client;
const char* host = "192.168.1.1";
const int port = 25566;
boolean alreadyConnected = false; // whether or not the client was connected previously

//functions

// in case the doorbell or smartlock isn't working over the air, we can tell it to reset itself
void resetSelf() {
  PRINTDEBUG("Reseting...");
  while (1) {}
}

//fucntion to connect wifi
void connectWifi(const char* ssid, const char* password) {
  int WiFiCounter = 0;
  //connect to wifi
  PRINTDEBUG("Connecting to ");
  PRINTDEBUG(ssid);
  WiFi.disconnect();
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED && WiFiCounter < 30) {

    delay(1000);
    WiFiCounter++; //counts how many seconds it takes to connect
    PRINTDEBUG("Current seconds: ");
    PRINTDEBUG(WiFiCounter);

    if (WiFiCounter >= 30)
      PRINTDEBUG("It has taken more than 30 seconds for esp... to connect. Going to reset...");
    resetSelf();
  }

  PRINTDEBUG("");
  PRINTDEBUG("WiFi connected");
  PRINTDEBUG("IP address: ");
  PRINTDEBUG(WiFi.localIP());
}

//where the stuff happens
void setup() {
  // put your setup code here, to run once

  connectWifi(ssid, password);

  if (client.connect(host, port)) {
    Serial.println("Connected to python server");
    Serial.println("Sending hostname to server");
    client.write('S'); //S is for smartlock, D is for doorbell
    client.write(':'); //end the packet

  }
}

void loop() {
    // put your main code here, to run repeatedly:

    delay(10); //run loop every ten miliseconds
    int connectFails = 0;

    //check to make sure esp... is connected, if not attempt to reconnect
    while ((WiFi.status() != WL_CONNECTED)) {
      connectWifi(ssid, password);

      connectFails++;

      if (connectFails > 6) {
        resetSelf();  // If 30 seconds have passed with no connection, reset the esp...
      }
      delay(5000); //wait five seconds before attempting to reconnect
    }

    if (client.available() > 0) {
      // read the bytes incoming from the client:
      char thisChar = client.read();

      if (thisChar == 'l') {
        //lock the door
      }
      if (thisChar == 'u') {
        //check if door is locked
        char locked = 'l'; //l means locked, n means not locked
        client.write(locked);
        client.write(':'); //end of packet
      }
      //insert code here!
      //for example, if thisChar = "lock", then the smart lock should lock the door!!
      //
      //
      //
      //
      //
      //add reponse text in the future with server.write()
    }
}
