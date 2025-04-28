// ESP32-S3 Camera MQTT Latency Profiling
// Captures and sends camera images to Raspberry Pi via MQTT
// Measures and reports round-trip latency

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "esp_camera.h"

// WiFi credentials
const char* ssid = "Xperia";
const char* password = "qwerasdf";

// MQTT broker settings (Raspberry Pi)
const char* mqtt_server = "192.168.17.238";  // Replace with your Pi's IP address
const int mqtt_port = 1883;

// MQTT topics
const char* mqtt_topic_image_to_pi = "esp32/image";     // Topic to send image to Pi
const char* mqtt_topic_image_from_pi = "raspi/image";   // Topic to receive image from Pi
const char* mqtt_topic_latency = "esp32/latency";       // Topic to publish latency stats

// Buffer for image data
const int MAX_PACKET_SIZE = 2048;  // Smaller packets for better stability

// Latency measurement
unsigned long sendTimestamp = 0;
unsigned long totalLatency = 0;
int latencyMeasurements = 0;
unsigned long maxLatency = 0;
unsigned long minLatency = ULONG_MAX;

// Image tracking
int imagesSent = 0;
int imagesReceived = 0;

// Packet tracking
int currentPacketId = 0;
int totalPackets = 0;
bool transmission_active = false;

// WiFi and MQTT clients
WiFiClient espClient;
PubSubClient client(espClient);


// ESP32-S3 camera pins
#define CAMERA_MODEL_XIAO_ESP32S3 //has PSRAM
#define PWDN_GPIO_NUM -1
#define RESET_GPIO_NUM -1
#define XCLK_GPIO_NUM 10
#define SIOD_GPIO_NUM 40
#define SIOC_GPIO_NUM 39
#define Y9_GPIO_NUM 48
#define Y8_GPIO_NUM 11
#define Y7_GPIO_NUM 12
#define Y6_GPIO_NUM 14
#define Y5_GPIO_NUM 16
#define Y4_GPIO_NUM 18
#define Y3_GPIO_NUM 17
#define Y2_GPIO_NUM 15
#define VSYNC_GPIO_NUM 38
#define HREF_GPIO_NUM 47
#define PCLK_GPIO_NUM 13

// Function prototypes
void setup_wifi();
void reconnect();
void callback(char* topic, byte* payload, unsigned int length);
bool initCamera();
void captureAndSendImage();
bool receiveAndProcessImage(byte* payload, unsigned int length);
void publishLatencyStats();

void setup() {
  Serial.begin(115200);
  delay(1000); // Give serial monitor time to start

  Serial.println("\n\n===== ESP32-S3 Camera MQTT Latency Profiling =====");
  
  // Initialize camera
  if (!initCamera()) {
    Serial.println("Camera initialization failed. Using test pattern instead.");
  } else {
    Serial.println("Camera initialized successfully.");
  }
  
  // Setup WiFi connection
  setup_wifi();
  
  // Configure MQTT client
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
  client.setBufferSize(MAX_PACKET_SIZE + 200);  // Set buffer size with some margin
  
  Serial.println("Setup complete. Starting main loop...");
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // Only start a new image capture if we're not in the middle of transmission
  static unsigned long lastImageTime = 0;
  if ((millis() - lastImageTime > 10000) && !transmission_active) {
    lastImageTime = millis();
    captureAndSendImage();
  }
  
  // Publish latency stats every 60 seconds
  static unsigned long lastStatsTime = 0;
  if (millis() - lastStatsTime > 60000) {
    lastStatsTime = millis();
    publishLatencyStats();
  }
}

void setup_wifi() {
  Serial.println("Connecting to WiFi...");
  WiFi.begin(ssid, password);

  int attempt = 0;
  while (WiFi.status() != WL_CONNECTED && attempt < 20) {
    delay(500);
    Serial.print(".");
    attempt++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nWiFi connection failed. Check credentials or network.");
  }
}

void reconnect() {
  int retries = 0;
  while (!client.connected() && retries < 3) {
    Serial.print("Attempting MQTT connection...");
    String clientId = "ESP32CamClient-";
    clientId += String(random(0xffff), HEX);
    
    if (client.connect(clientId.c_str())) {
      Serial.println("connected");
      client.subscribe(mqtt_topic_image_from_pi);
      Serial.println("Subscribed to raspi/image topic");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
      retries++;
    }
  }
}

void callback(char* topic, byte* payload, unsigned int length) {
  if (strcmp(topic, mqtt_topic_image_from_pi) == 0) {
    Serial.printf("Received image data from Raspberry Pi, length: %u bytes\n", length);
    
    if (receiveAndProcessImage(payload, length)) {
      // Image fully received
      imagesReceived++;
      
      // Calculate latency
      unsigned long currentTime = millis();
      unsigned long roundTripTime = currentTime - sendTimestamp;
      
      totalLatency += roundTripTime;
      
      if (roundTripTime > maxLatency) maxLatency = roundTripTime;
      if (roundTripTime < minLatency) minLatency = roundTripTime;
      
      latencyMeasurements++;
      
      float avgLatency = (float)totalLatency / latencyMeasurements;
      
      Serial.println("\n===== LATENCY STATISTICS =====");
      Serial.printf("Round-trip time: %lu ms\n", roundTripTime);
      Serial.printf("Average latency: %.2f ms\n", avgLatency);
      Serial.printf("Min latency: %lu ms\n", minLatency);
      Serial.printf("Max latency: %lu ms\n", maxLatency);
      Serial.printf("Images sent: %d, Images received: %d\n", imagesSent, imagesReceived);
      Serial.println("==============================\n");
      
      transmission_active = false;
    }
  }
}

bool initCamera() {
  // Power cycle the camera (if your board supports it)
  // Some boards have PWDN pin
  #if PWDN_GPIO_NUM != -1
    pinMode(PWDN_GPIO_NUM, OUTPUT);
    digitalWrite(PWDN_GPIO_NUM, LOW);
    delay(10);
    digitalWrite(PWDN_GPIO_NUM, HIGH);
    delay(10);
  #endif
  
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
  
  // Lower resolution for faster transmission
  config.frame_size = FRAMESIZE_QVGA;  // 320x240
  config.jpeg_quality = 15;  // 0-63, lower is higher quality
  config.fb_count = 1;

  // Initialize the camera
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x\n", err);
    return false;
  }

  // Additional camera setup
  sensor_t * s = esp_camera_sensor_get();
  if (s) {
    // Adjust camera settings for better image quality or performance
    s->set_brightness(s, 1);  // -2 to 2
    s->set_contrast(s, 0);    // -2 to 2
    s->set_saturation(s, 0);  // -2 to 2
    s->set_special_effect(s, 0); // 0 to 6 (0 - No Effect, 1 - Negative, 2 - Grayscale, etc.)
    s->set_whitebal(s, 1);    // 0 = disable, 1 = enable
    s->set_awb_gain(s, 1);    // 0 = disable, 1 = enable
    s->set_wb_mode(s, 0);     // 0 to 4 - if awb_gain enabled
    s->set_exposure_ctrl(s, 1);// 0 = disable, 1 = enable
    s->set_aec2(s, 1);        // 0 = disable, 1 = enable
    s->set_gain_ctrl(s, 1);   // 0 = disable, 1 = enable
    s->set_agc_gain(s, 0);    // 0 to 30
    s->set_gainceiling(s, (gainceiling_t)0);  // 0 to 6
    s->set_bpc(s, 0);         // 0 = disable, 1 = enable
    s->set_wpc(s, 1);         // 0 = disable, 1 = enable
    s->set_raw_gma(s, 1);     // 0 = disable, 1 = enable
    s->set_lenc(s, 1);        // 0 = disable, 1 = enable
    s->set_hmirror(s, 0);     // 0 = disable, 1 = enable
    s->set_vflip(s, 0);       // 0 = disable, 1 = enable
    s->set_dcw(s, 1);         // 0 = disable, 1 = enable
  }
  
  return true;
}

void captureAndSendImage() {
  transmission_active = true;
  
  Serial.println("Capturing image...");
  
  // Capture a frame from the camera
  camera_fb_t* fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("Camera capture failed");
    transmission_active = false;
    return;
  }
  
  Serial.printf("Image captured: %u bytes\n", fb->len);
  
  // Calculate how many packets we need to send
  totalPackets = (fb->len + MAX_PACKET_SIZE - 1) / MAX_PACKET_SIZE;
  
  // Record start time for latency measurement
  sendTimestamp = millis();
  
  // Send each packet
  for (int i = 0; i < totalPackets; i++) {
    currentPacketId = i + 1;
    
    // Create a JSON metadata header
    StaticJsonDocument<200> jsonDoc;
    jsonDoc["packetId"] = currentPacketId;
    jsonDoc["totalPackets"] = totalPackets;
    jsonDoc["timestamp"] = sendTimestamp;
    jsonDoc["imageId"] = imagesSent + 1;
    
    // Calculate data size for this packet
    int dataStart = i * MAX_PACKET_SIZE;
    int dataSize = min((int)fb->len - dataStart, MAX_PACKET_SIZE);
    
    if (dataSize <= 0) break; // Safety check
    
    // Serialize the JSON to a string
    String jsonHeader;
    serializeJson(jsonDoc, jsonHeader);
    
    // Allocate memory for the combined packet
    int headerLength = jsonHeader.length();
    int packetSize = headerLength + 1 + dataSize; // +1 for newline separator
    
    uint8_t* packet = (uint8_t*)malloc(packetSize);
    if (!packet) {
      Serial.println("Failed to allocate memory for packet");
      break;
    }
    
    // Copy header
    memcpy(packet, jsonHeader.c_str(), headerLength);
    packet[headerLength] = '\n';  // Separator between header and data
    
    // Copy image data
    memcpy(packet + headerLength + 1, fb->buf + dataStart, dataSize);
    
    // Send the packet
    bool success = client.publish(mqtt_topic_image_to_pi, packet, packetSize);
    
    if (success) {
      Serial.printf("Sent packet %d/%d (%d bytes)\n", currentPacketId, totalPackets, packetSize);
    } else {
      Serial.println("Failed to publish packet");
    }
    
    free(packet);
    delay(50);  // Small delay between packets
  }
  
  // Return the frame buffer to be reused
  esp_camera_fb_return(fb);
  
  Serial.println("Image transmission completed");
  imagesSent++;
}

bool receiveAndProcessImage(byte* payload, unsigned int length) {
  // Find the separator between header and data
  int separatorPos = -1;
  for (unsigned int i = 0; i < length && i < 200; i++) {  // Limit search to avoid long loops
    if (payload[i] == '\n') {
      separatorPos = i;
      break;
    }
  }
  
  if (separatorPos == -1) {
    Serial.println("Invalid packet format: no separator found");
    return false;
  }
  
  // Extract and parse the header
  char* headerBuffer = (char*)malloc(separatorPos + 1);
  if (!headerBuffer) {
    Serial.println("Failed to allocate memory for header");
    return false;
  }
  
  memcpy(headerBuffer, payload, separatorPos);
  headerBuffer[separatorPos] = '\0';
  
  StaticJsonDocument<200> jsonDoc;
  DeserializationError error = deserializeJson(jsonDoc, headerBuffer);
  
  free(headerBuffer);
  
  if (error) {
    Serial.print("Failed to parse JSON header: ");
    Serial.println(error.c_str());
    return false;
  }
  
  int packetId = jsonDoc["packetId"];
  int totalPackets = jsonDoc["totalPackets"];
  
  // For simplicity, we'll just acknowledge receipt
  Serial.printf("Received image packet %d/%d from Raspberry Pi\n", packetId, totalPackets);
  
  // If this is the last packet, return true to calculate latency
  return (packetId == totalPackets);
}

void publishLatencyStats() {
  if (latencyMeasurements == 0) return;

  float avgLatency = (float)totalLatency / latencyMeasurements;
  
  StaticJsonDocument<256> statsDoc;
  statsDoc["avg_latency_ms"] = avgLatency;
  statsDoc["min_latency_ms"] = minLatency;
  statsDoc["max_latency_ms"] = maxLatency;
  statsDoc["measurements"] = latencyMeasurements;
  statsDoc["images_sent"] = imagesSent;
  statsDoc["images_received"] = imagesReceived;
  
  String statsJson;
  serializeJson(statsDoc, statsJson);
  
  client.publish(mqtt_topic_latency, statsJson.c_str());
  Serial.println("Published latency statistics to MQTT");
}