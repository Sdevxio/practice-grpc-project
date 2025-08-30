#include "command_router.h"
#include "motor_controller.h"
#include <ArduinoJson.h>

CommandRouter::CommandRouter(MotorController& motor)
  : motorController(motor) {}

void CommandRouter::init() {
  Serial.println("[Router] Relay-mimicking command router initialized");
}

void CommandRouter::handleCommand(const String& command) {
  Serial.println("[Router] Handling command: " + command);

  // Basic motor commands
  if (command == "extend") {
    motorController.extend();
  } else if (command == "retract") {
    motorController.retract();
  } else if (command == "stop") {
    motorController.stop();
  } else if (command == "tap") {
    motorController.startTap();
  } 
  // NEW: Dual card commands
  else if (command == "reset_to_middle") {
    motorController.resetToMiddle();
  } else if (command == "tap_card1") {
    motorController.tapCard1();
  } else if (command == "tap_card2") {
    motorController.tapCard2();
  }
  // NEW: Calibration commands
  else if (command == "manual_extend") {
    motorController.manualExtend();
  } else if (command == "manual_retract") {
    motorController.manualRetract();
  } else if (command == "manual_stop") {
    motorController.manualStop();
  } else if (command == "capture_middle") {
    motorController.captureCurrentAsMiddle();
  }
  // NEW: Power source commands
  else if (command == "power_12v") {
    motorController.setPowerSource12V();
  } else if (command == "power_usb") {
    motorController.setPowerSourceUSB();
  } else {
    Serial.println("[Router] Unknown command: " + command);
  }
}

void CommandRouter::handleJsonCommand(const String& json) {
  StaticJsonDocument<512> doc;
  DeserializationError err = deserializeJson(doc, json);

  if (err) {
    Serial.println("[Router] Invalid JSON received: " + String(err.c_str()));
    return;
  }

  if (!doc.containsKey("action")) {
    Serial.println("[Router] No 'action' in JSON");
    return;
  }

  String action = doc["action"].as<String>();
  Serial.println("[Router] JSON Action: " + action);

  // Handle time-based commands (relay mimicking)
  if (action == "extend_for_time") {
    if (doc.containsKey("duration_ms")) {
      unsigned long duration = doc["duration_ms"].as<unsigned long>();
      motorController.extendForTime(duration);
    } else {
      Serial.println("[Router] Missing duration_ms for extend_for_time");
    }
  } 
  else if (action == "retract_for_time") {
    if (doc.containsKey("duration_ms")) {
      unsigned long duration = doc["duration_ms"].as<unsigned long>();
      motorController.retractForTime(duration);
    } else {
      Serial.println("[Router] Missing duration_ms for retract_for_time");
    }
  }
  // Handle legacy tap command
  else if (action == "tap") {
    motorController.tap();
  } 
  // Handle basic commands
  else {
    handleCommand(action);
  }
}