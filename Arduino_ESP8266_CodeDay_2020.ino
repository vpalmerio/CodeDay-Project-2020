#define DEBUG 1  //Print to Serial
#define PRINTDEBUG(STR) \
  {  \
    if (DEBUG) Serial.println(STR); \
} //PRINTDEBUG prints lines to serial

#include <ESP8266WiFi.h>

//initialize variables
const char* ssid     = " ";
const char* password = " ";

WiFiServer server(25566);
boolean alreadyConnected = false; // whether or not the client was connected previously

//functions

// Fucntion to connect WiFi
void connectWifi(const char* ssid, const char* password) {
  int WiFiCounter = 0;
  //Connect to wifi
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
        PRINTDEBUG("It has taken more than 30 seconds for esp... to connect. Try again?");
 }

  PRINTDEBUG("");
  PRINTDEBUG("WiFi connected");
  PRINTDEBUG("IP address: ");
  PRINTDEBUG(WiFi.localIP());
}

// in case the doorbell or smartlock isn't working over the air, we can tell it to reset itself
void resetSelf() {
  PRINTDEBUG("Reseting...");
  while (1) {}
}

//where the stuff happens
void setup() {
  // put your setup code here, to run once:

  connectWifi(ssid, password);

  server.begin(); //start server (not too experienced with this :| )

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

   // wait for the python server to connect:
  WiFiClient client = server.available();
  
  if (client) {
    //checks if python server is already connected, if not, then it performs some operations
    if (!alreadyConnected) {
      // clear out the input buffer: // whatever this means... it was in the sample code so \_:|_/
      client.flush();
      Serial.println("Connected to python server!");
     
      alreadyConnected = true;
    }

    if (client.available() > 0) {
      // read the bytes incoming from the client:
      char thisChar = client.read();
      //insert code here!
      //for example, if thisChar = "lock", then the smart lock should lock the door!!
      //
      //
      //
      //
      //
      //
    }
  }
}
