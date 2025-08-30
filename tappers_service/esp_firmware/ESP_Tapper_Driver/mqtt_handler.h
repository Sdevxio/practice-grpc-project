// mqtt_handler.h - ENHANCED FOR DUAL CARD OPERATIONS
#pragma once
#include <PubSubClient.h>
#include <WiFi.h>
#include "command_router.h"

// Forward declaration to avoid circular dependency
class MotorController;

class MQTTHandler {
public:
  MQTTHandler(CommandRouter& router);
  void init();
  void loop();
  void publishStatus(String status);  // Basic status publishing
  void publishDetailedStatus();       // Enhanced dual card status
  void setMotorController(MotorController* controller);  // Set motor controller reference

private:
  void tryConnection();  // Non-blocking connection attempt
  static void callback(char* topic, byte* payload, unsigned int length);  // Must be static

  WiFiClient espClient;
  PubSubClient client;
  CommandRouter& commandRouter;
  MotorController* motorController;  // Reference to motor controller for detailed status
  static MQTTHandler* instance;      // for static callback

  unsigned long lastReconnectAttempt = 0;
  bool connectionFailed = false;   // Track if last connection failed
  static const unsigned long reconnectInterval = 5000;

  String statusTopic;  // Status topic for publishing
};