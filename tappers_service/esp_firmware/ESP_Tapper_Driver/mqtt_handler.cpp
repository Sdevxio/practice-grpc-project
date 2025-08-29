// mqtt_handler.cpp - ENHANCED FOR DUAL CARD OPERATIONS
#include "mqtt_handler.h"
#include "motor_controller.h"  // Include for detailed status access
#include "wifi_config.h"
#include <PubSubClient.h>

MQTTHandler* MQTTHandler::instance = nullptr;

MQTTHandler::MQTTHandler(CommandRouter& router)
  : client(espClient), commandRouter(router), motorController(nullptr) {
  instance = this;
}

void MQTTHandler::init() {
  // Set MQTT broker
  client.setServer("10.153.138.254", 1883);
  
  // Set aggressive timeouts to prevent blocking
  client.setSocketTimeout(1);      // 1 second socket timeout
  client.setKeepAlive(5);          // 5 second keepalive
  
  // Set the callback for incoming messages
  client.setCallback(callback);

  // Set up status topic
  String deviceId = WiFiConfig::getDeviceID();
  statusTopic = "tappers/" + deviceId + "/status";
  Serial.println("[MQTT] Status topic: " + statusTopic);

  // Try initial connection
  tryConnection();
}

void MQTTHandler::loop() {
  unsigned long now = millis();
  
  if (!client.connected()) {
    // Only try reconnecting every 15 seconds after failures
    if (now - lastReconnectAttempt > (connectionFailed ? 15000 : 5000)) {
      lastReconnectAttempt = now;
      tryConnection();
    }
  } else {
    // Connected - process MQTT messages
    client.loop();
    connectionFailed = false;  // Reset failure flag
  }
}

void MQTTHandler::tryConnection() {
  String deviceId = WiFiConfig::getDeviceID();
  String clientId = "ESP32Tapper-" + deviceId;
  String topic = "tappers/" + deviceId + "/command";

  Serial.print("[MQTT] Quick connection attempt...");
  
  // The key fix: This connect() call will now fail fast (1-2 seconds max)
  bool connected = client.connect(clientId.c_str());
  
  if (connected) {
    Serial.println(" SUCCESS!");
    client.subscribe(topic.c_str());
    Serial.println("[MQTT] Subscribed to: " + topic);
    connectionFailed = false;
    
    // Publish initial status
    publishStatus("idle");
  } else {
    Serial.print(" FAILED (rc=");
    Serial.print(client.state());
    Serial.println(") - HTTP server remains responsive");
    connectionFailed = true;
  }
}

void MQTTHandler::publishStatus(String status) {
  if (client.connected()) {
    bool success = client.publish(statusTopic.c_str(), status.c_str());
    if (success) {
      Serial.println("[MQTT] Published status: " + status);
    } else {
      Serial.println("[MQTT] Failed to publish status: " + status);
    }
  } else {
    Serial.println("[MQTT] Cannot publish status - not connected");
  }
}

void MQTTHandler::callback(char* topic, byte* payload, unsigned int length) {
  String message;
  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }

  Serial.println("[MQTT] Received on " + String(topic) + ": " + message);

  if (instance) {
    instance->commandRouter.handleJsonCommand(message);
  }
}

// ============ NEW: ENHANCED DUAL CARD STATUS FUNCTIONS ============

void MQTTHandler::setMotorController(MotorController* controller) {
  motorController = controller;
  Serial.println("[MQTT] Motor controller reference set for detailed status reporting");
}

void MQTTHandler::publishDetailedStatus() {
  if (!client.connected() || !motorController) {
    return;
  }
  
  // Create detailed status string with dual card information
  String detailedStatus = "Position: " + motorController->getPositionString() + 
                         ", Operation: " + motorController->getOperationString() + 
                         ", Power: " + motorController->getPowerSourceString();
  
  // Add timing info if measurement is active
  String timingInfo = motorController->getTimingInfo();
  if (timingInfo != "No timing measurement active") {
    detailedStatus += ", " + timingInfo;
  }
  
  bool success = client.publish(statusTopic.c_str(), detailedStatus.c_str());
  if (success) {
    Serial.println("[MQTT] Published detailed status: " + detailedStatus);
  } else {
    Serial.println("[MQTT] Failed to publish detailed status");
  }
}