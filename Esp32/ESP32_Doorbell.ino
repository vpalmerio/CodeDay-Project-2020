#include "esp_camera.h"
#include <WiFi.h>

//
// WARNING!!! Make sure that you have either selected ESP32 Wrover Module,
//            or another board which has PSRAM enabled
//

// Select camera model
#define CAMERA_MODEL_WROVER_KIT
//#define CAMERA_MODEL_ESP_EYE
//#define CAMERA_MODEL_M5STACK_PSRAM
//#define CAMERA_MODEL_M5STACK_WIDE
//#define CAMERA_MODEL_AI_THINKER

#include "camera_pins.h"

const char* ssid = "*********";
const char* password = "*********";
boolean alreadyConnected = false; // whether or not the client was connected previously
//WiFi.hostname("DOORBELL"); does not work for whatever reason
WiFiClient client;

//server info
const char* host = "192.168.1.1";
const int port = 25566;

void startCameraServer();

// in case the doorbell or smartlock isn't working over the air, we can tell it to reset itself
void resetSelf() {
  Serial.println("Reseting...");
  while (1) {}
}

void connectWifi(const char* ssid, const char* password) {
  int WiFiCounter = 0;
  //connect to wifi
  Serial.println("Connecting to ");
  Serial.print(ssid);
  WiFi.disconnect();
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED && WiFiCounter < 30) {

    delay(1000);
    WiFiCounter++; //counts how many seconds it takes to connect
    Serial.println("Current seconds: ");
    Serial.println(WiFiCounter);

    if (WiFiCounter >= 30)
      Serial.println("It has taken more than 30 seconds for esp... to connect. Going to reset...");
    resetSelf();
  }

  Serial.println("");
  Serial.println("Wifi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}



void setup() {
  Serial.begin(115200);
  Serial.setDebugOutput(true);
  Serial.println();

  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  //init with high specs to pre-allocate larger buffers
  if (psramFound()) {
    config.frame_size = FRAMESIZE_UXGA;
    config.jpeg_quality = 10;
    config.fb_count = 2;
  } else {
    config.frame_size = FRAMESIZE_SVGA;
    config.jpeg_quality = 12;
    config.fb_count = 1;
  }

#if defined(CAMERA_MODEL_ESP_EYE)
  pinMode(13, INPUT_PULLUP);
  pinMode(14, INPUT_PULLUP);
#endif

  // camera init
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    return;
  }

  sensor_t * s = esp_camera_sensor_get();
  //initial sensors are flipped vertically and colors are a bit saturated
  if (s->id.PID == OV3660_PID) {
    s->set_vflip(s, 1);//flip it back
    s->set_brightness(s, 1);//up the blightness just a bit
    s->set_saturation(s, -2);//lower the saturation
  }
  //drop down frame size for higher initial frame rate
  s->set_framesize(s, FRAMESIZE_QVGA);

#if defined(CAMERA_MODEL_M5STACK_WIDE)
  s->set_vflip(s, 1);
  s->set_hmirror(s, 1);
#endif
  /*
    WiFi.hostname("Doorbell");
    WiFi.begin(ssid, password);

    while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    }
    Serial.println("");
    Serial.println("WiFi connected");
  */
  connectWifi(ssid, password);

  startCameraServer();

  Serial.print("Camera Ready! Use 'http://");
  Serial.print(WiFi.localIP());
  Serial.println(" to connect");

  if (client.connect(host, port)) {
    Serial.println("Connected to python server");
    Serial.println("Sending hostname to server");
    client.write('D'); //S is for smartlock, D is for doorbell
    client.write(':'); //end the packet


  } else {
    Serial.println("Failed to connect. Resetting...");
    resetSelf();
  }


}

void loop() {
  // put your main code here, to run repeatedly:
  delay(10); //run loop every ten miliseconds

  int connectFails = 0;

  //check to make sure esp32 is connected, if not attempt to reconnect
  while ((WiFi.status() != WL_CONNECTED)) {
    connectWifi(ssid, password);

    connectFails++;

    if (connectFails > 6) {

      //resetSelf();  // If 30 seconds have passed with no connection, reset the esp...
    }
    delay(5000); //wait five seconds before attempting to reconnect
  }

  if (client.available() > 0) { //client.available() checks if there is data to be read
    // read the bytes incoming from the client:
    char thisChar = client.read();
    Serial.println("Received data: ");
    Serial.print(thisChar);
    //i am lazy, so for now I won't check for the end of the packet
    if (thisChar == 'u') {
      //check for stats, like motion sensor and proximity sensor
      char mTriggered = 't'; //motion sensor, t = triggered, n = not triggered
      char pTriggered = 'i'; //proximity sensor, h = triggered, i = not triggered
      Serial.println("Sending update to server");
      client.write(mTriggered);
      client.write(pTriggered); //send info to server
      client.write(':');
      Serial.println("Update sent to server");
    }
    //insert code here!
    //
    //
    //
    //
    //
    //
    //
  }
  if (!client.connected()) {
    Serial.println("Lost connection. Did server disconnect? Reconnecting...");
    client.connect(host, port);
  }
}
