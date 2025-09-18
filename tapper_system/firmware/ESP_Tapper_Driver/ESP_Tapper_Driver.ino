// ESP_Tapper_Driver.ino - Simplified for relay mimicking

#include "motor_controller.h"
#include "command_router.h"
#include "mqtt_handler.h"
#include "http_server.h"
#include "wifi_config.h"

// Instantiate core components
MotorController motorController;
CommandRouter commandRouter(motorController);
MQTTHandler mqttHandler(commandRouter);
HTTPServer httpServer(commandRouter);

void setup() {
  // Serial for debugging
  Serial.begin(115200);
  delay(100);  // Let serial settle

  Serial.println("[Tapper] Starting ESP32 Dual Card Relay-Mimicking Tapper...");

  // Connect to WiFi
  WiFiConfig::connect();

  // Initialize hardware and modules
  motorController.init();
  commandRouter.init();
  mqttHandler.init();
  httpServer.init();
  
  // Set motor controller reference for detailed MQTT status reporting
  mqttHandler.setMotorController(&motorController);

  Serial.println("[Tapper] ESP32 dual card tapper system ready.");
  Serial.println("[Tapper] Features:");
  Serial.println("  - Timing-based positioning (relay mimicking)");
  Serial.println("  - Dual card support via Python framework");
  Serial.println("  - HTTP and MQTT protocols");
  Serial.println("  - Time-based operations (extend_for_time, retract_for_time)");
}

void loop() {
  // HIGHEST PRIORITY: Motor control updates
  motorController.updateTap();           // Legacy tap sequences
  motorController.updateTimedOperations(); // Time-based operations (relay mimicking)
  motorController.updateDualCardOperations(); // NEW: Dual card operations

  // Safety timeout checking (no position sensors)
  motorController.checkLimitSwitches();

  // HIGHEST PRIORITY: HTTP server (user commands)
  httpServer.loop();

  // LOWER PRIORITY: MQTT (only if motor not active)
  if (!motorController.isTapping()) {
    mqttHandler.loop();
  }

  // Minimal delay for ESP32 stability
  delay(10);
}