#include "wifi_config.h"

// Define your SSID and Password here or use a config system
const char* ssid = "ENG-034"; // Use the actual network
const char* password = "Iomaguire1"; // Use the actual Network Password
String WiFiConfig::deviceId = "tapper_001";  // Define the static variable

namespace WiFiConfig {

void connect() {
  Serial.println("[WiFi] Connecting to WiFi...");
  WiFi.begin(ssid, password);
  int retryCount = 0;
  while (WiFi.status() != WL_CONNECTED && retryCount < 20) {
    delay(500);
    Serial.print(".");
    retryCount++;
  }
  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("[WiFi] Connected!");
    Serial.print("[WiFi] IP Address: ");
    Serial.println(WiFi.localIP());

    // Assign deviceId (e.g., tapper_5EBC2C)
    String mac = WiFi.macAddress();
    String suffix = mac.substring(mac.length() - 6);  // Last 6 chars
    suffix.replace(":", "");                          // Remove colons
    deviceId = "tapper_" + suffix;
    Serial.println("[WiFi] Device ID: " + deviceId);

  } else {
    Serial.println("[WiFi] Failed to connect.");
    deviceId = "tapper_unknown";
  }
}

String getDeviceID() {
  return deviceId;
}

}