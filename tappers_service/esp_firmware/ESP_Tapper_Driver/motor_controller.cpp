#include "motor_controller.h"
#include "mqtt_handler.h"
#include <Arduino.h>

#define IN1_PIN 12
#define IN2_PIN 13

extern MQTTHandler mqttHandler;

void MotorController::init() {
  pinMode(IN1_PIN, OUTPUT);
  pinMode(IN2_PIN, OUTPUT);
  stop();
  
  // Initialize dual card state
  currentPosition = UNKNOWN;
  previousPosition = UNKNOWN;
  currentOperation = IDLE;

  Serial.println("[Motor] Enhanced dual card relay-mimicking controller initialized");
  Serial.println("  - Dual card support with position tracking");
  Serial.println("  - Timing-based positioning (no sensors)");
  Serial.println("  - Measured timing constants for accurate positioning");
  Serial.println("  - Power-aware timing (12V/USB modes)");
}

// ============ BASIC MOTOR CONTROLS ============
void MotorController::extend() {
  digitalWrite(IN1_PIN, HIGH);
  digitalWrite(IN2_PIN, LOW);
  currentState = STATE_EXTENDING;
  Serial.println("[Motor] Extending...");
  mqttHandler.publishStatus("extending");
}

void MotorController::retract() {
  digitalWrite(IN1_PIN, LOW);
  digitalWrite(IN2_PIN, HIGH);
  currentState = STATE_RETRACTING;
  Serial.println("[Motor] Retracting...");
  mqttHandler.publishStatus("retracting");
}

void MotorController::stop() {
  digitalWrite(IN1_PIN, LOW);
  digitalWrite(IN2_PIN, LOW);
  currentState = STATE_IDLE;
  Serial.println("[Motor] Stopped");
  mqttHandler.publishStatus("idle");
}

// ============ TIME-BASED OPERATIONS (RELAY MIMICKING) ============

void MotorController::extendForTime(unsigned long duration_ms) {
  Serial.println("[Motor] Extend for " + String(duration_ms) + "ms");
  
  // Stop any current timed operation
  if (timedOperation) {
    stop();
    timedOperation = false;
  }
  
  // Start extend operation
  extend();
  operationStartTime = millis();
  operationDuration = duration_ms;
  timedOperationState = STATE_EXTENDING;
  timedOperation = true;
}

void MotorController::retractForTime(unsigned long duration_ms) {
  Serial.println("[Motor] Retract for " + String(duration_ms) + "ms");
  
  // Stop any current timed operation
  if (timedOperation) {
    stop();
    timedOperation = false;
  }
  
  // Start retract operation
  retract();
  operationStartTime = millis();
  operationDuration = duration_ms;
  timedOperationState = STATE_RETRACTING;
  timedOperation = true;
}

void MotorController::updateTimedOperations() {
  if (!timedOperation) return;

  unsigned long elapsed = millis() - operationStartTime;
  
  if (elapsed >= operationDuration) {
    Serial.println("[Motor] Timed operation complete (" + String(elapsed) + "ms)");
    stop();
    timedOperation = false;
    
    // Publish completion status
    switch (timedOperationState) {
      case STATE_EXTENDING:
        mqttHandler.publishStatus("extend_complete");
        break;
      case STATE_RETRACTING:
        mqttHandler.publishStatus("retract_complete");
        break;
      default:
        mqttHandler.publishStatus("operation_complete");
        break;
    }
  }
}

// ============ LEGACY TAP FUNCTIONS (SIMPLIFIED) ============
void MotorController::startTap() {
  Serial.println("[Motor] Starting legacy tap sequence");
  extend();
  tapState = TAP_EXTENDING;
  tapStartTime = millis();
}

void MotorController::updateTap() {
  if (tapState == TAP_IDLE) return;

  unsigned long currentTime = millis();

  switch (tapState) {
    case TAP_EXTENDING:
      if (currentTime - tapStartTime > tapTimeout) {
        Serial.println("[Motor] Legacy tap: Extend timeout, pausing");
        stop();
        tapState = TAP_PAUSE;
        tapStartTime = currentTime;
      }
      break;

    case TAP_PAUSE:
      if (currentTime - tapStartTime > tapPauseDelay) {
        Serial.println("[Motor] Legacy tap: Starting retract");
        retract();
        tapState = TAP_RETRACTING;
        tapStartTime = currentTime;
      }
      break;

    case TAP_RETRACTING:
      if (currentTime - tapStartTime > tapTimeout) {
        Serial.println("[Motor] Legacy tap: Retract timeout, stopping");
        stop();
        tapState = TAP_COMPLETE;
      }
      break;

    case TAP_COMPLETE:
      Serial.println("[Motor] Legacy tap sequence completed");
      tapState = TAP_IDLE;
      mqttHandler.publishStatus("idle");
      break;
  }
}

bool MotorController::isTapping() const {
  return tapState != TAP_IDLE || timedOperation || currentOperation != IDLE;
}

void MotorController::tap() {
  startTap();
}

// ============ STATUS AND STATE ============
String MotorController::getState() const {
  // PRIORITY 1: Check dual card operations first
  if (currentOperation != IDLE) {
    return getOperationString();
  }
  
  // PRIORITY 2: Check if in timed operation
  if (timedOperation) {
    switch (timedOperationState) {
      case STATE_EXTENDING: return "timed_extending";
      case STATE_RETRACTING: return "timed_retracting";
      default: return "timed_operation";
    }
  }
  
  // PRIORITY 3: Check legacy tap states
  if (tapState != TAP_IDLE) {
    switch (tapState) {
      case TAP_EXTENDING: return "tap_extending";
      case TAP_PAUSE: return "tap_pausing";
      case TAP_RETRACTING: return "tap_retracting";
      case TAP_COMPLETE: return "tap_complete";
      default: return "tapping";
    }
  }
  
  // PRIORITY 4: Check basic motor states
  switch (currentState) {
    case STATE_EXTENDING: return "extending";
    case STATE_RETRACTING: return "retracting";
    case STATE_IDLE: return "idle";
    default: return "unknown";
  }
}

// ============ SAFETY TIMEOUT ONLY ============
void MotorController::checkLimitSwitches() {
  // Safety timeout for both directions (but not during legacy tap or timed operations)
  static unsigned long moveStartTime = 0;
  
  // Skip safety timeout if any controlled operation is active
  if (isTapping()) {  // This checks both tapState != TAP_IDLE AND timedOperation
    moveStartTime = 0;  // Reset timeout during controlled operations
    return;
  }
  
  if (currentState == STATE_EXTENDING || currentState == STATE_RETRACTING) {
    if (moveStartTime == 0) {
      moveStartTime = millis();
    } else if (millis() - moveStartTime > 5000) {  // 5 second safety timeout
      Serial.println("[Motor] Safety timeout - AUTO STOP (uncontrolled movement)");
      stop();
      moveStartTime = 0;
    }
  } else {
    moveStartTime = 0;
  }
}

// ============ NEW: DUAL CARD FUNCTIONS ============

void MotorController::resetToMiddle() {
  if (currentOperation != IDLE) {
    Serial.println("[DualCard] Cannot reset - operation in progress");
    return;
  }
  
  Serial.println("[DualCard] Resetting to middle position from: " + getPositionString());
  
  if (currentPosition == MIDDLE) {
    Serial.println("[DualCard] Already at middle position");
    return;
  }
  
  if (currentPosition == CARD1) {
    // From Card 1 (extended), retract to middle
    Serial.println("[DualCard] From Card 1: retracting " + String(getCard1ToHomeMs()) + "ms to middle");
    retract();
  } else if (currentPosition == CARD2) {
    // From Card 2 (retracted), extend to middle  
    Serial.println("[DualCard] From Card 2: extending " + String(getCard2ToHomeMs()) + "ms to middle");
    extend();
  } else {
    // Unknown position - full retract first, then partial extend to middle
    Serial.println("[DualCard] Unknown position, doing full reset sequence");
    retract();  // Will timeout and extend to middle
  }
  
  startDualCardOperation(MOVING_TO_MIDDLE);
}

void MotorController::tapCard1() {
  if (currentOperation != IDLE) {
    Serial.println("[DualCard] Cannot tap Card 1 - operation in progress");
    return;
  }
  
  Serial.println("[DualCard] Starting Card 1 tap - extend from middle");
  Serial.println("[DualCard] Sequence: extend " + String(getCard1FromHomeMs()) + "ms → pause " + String(getCard1TapPauseMs()) + "ms → retract " + String(getCard1ToHomeMs()) + "ms");
  Serial.println("[DualCard] Power mode: " + getPowerSourceString());
  
  if (currentPosition != MIDDLE) {
    Serial.println("[DualCard] Must be at middle position first - resetting");
    resetToMiddle();
    return;
  }
  
  // Card 1 = Extended position from middle
  Serial.println("[DualCard] Step 1: Extending to Card 1 position...");
  extend();
  startDualCardOperation(MOVING_TO_CARD1);
}

void MotorController::tapCard2() {
  if (currentOperation != IDLE) {
    Serial.println("[DualCard] Cannot tap Card 2 - operation in progress");
    return;
  }
  
  Serial.println("[DualCard] Starting Card 2 tap - retract from middle");
  Serial.println("[DualCard] Sequence: retract " + String(getCard2FromHomeMs()) + "ms → pause " + String(getCard2TapPauseMs()) + "ms → extend " + String(getCard2ToHomeMs()) + "ms");
  Serial.println("[DualCard] Power mode: " + getPowerSourceString());
  
  if (currentPosition != MIDDLE) {
    Serial.println("[DualCard] Must be at middle position first - resetting");
    resetToMiddle();
    return;
  }
  
  // Card 2 = Retracted position from middle
  Serial.println("[DualCard] Step 1: Retracting to Card 2 position...");
  retract();
  startDualCardOperation(MOVING_TO_CARD2);
}

void MotorController::updateDualCardOperations() {
  if (currentOperation == IDLE) return;
  
  switch (currentOperation) {
    case MOVING_TO_MIDDLE:
      // Use exact timing based on where we came from
      if (previousPosition == CARD1) {
        // Moving from Card 1 (extended) to home
        if (isDualCardOperationTimedOut(getCard1ToHomeMs())) {
          currentPosition = MIDDLE;
          completeDualCardOperation();
          Serial.println("[DualCard] Reached home from Card 1");
        }
      } else if (previousPosition == CARD2) {
        // Moving from Card 2 (retracted) to home
        if (isDualCardOperationTimedOut(getCard2ToHomeMs())) {
          currentPosition = MIDDLE;
          completeDualCardOperation();
          Serial.println("[DualCard] Reached home from Card 2");
        }
      } else {
        // Unknown position - two-step process: full retract, then extend to middle
        if (previousPosition == UNKNOWN) {
          // Step 1: Full retract (first time through)
          if (isDualCardOperationTimedOut(getRetractFullMs())) {
            Serial.println("[DualCard] Step 1 complete - fully retracted, now extending to middle");
            extend();  // Start extending to middle
            previousPosition = CARD2;  // Now we know we're at retracted position
            dualCardOperationStartTime = millis();  // Reset timer for extend phase
          }
        } else {
          // Step 2: Extend from fully retracted to middle
          if (isDualCardOperationTimedOut(getHomeFromRetractedMs())) {
            currentPosition = MIDDLE;
            completeDualCardOperation();
            Serial.println("[DualCard] Reached middle from unknown position (2-step process complete)");
          }
        }
      }
      break;
      
    case MOVING_TO_CARD1:
      if (isDualCardOperationTimedOut(getCard1FromHomeMs())) {
        Serial.println("[DualCard] Reached Card 1, starting tap pause");
        currentPosition = CARD1;
        stop();  // Stop motor during tap pause
        currentOperation = TAPPING_CARD1;
        dualCardOperationStartTime = millis();  // Reset timer for tap
      }
      break;
      
    case MOVING_TO_CARD2:
      if (isDualCardOperationTimedOut(getCard2FromHomeMs())) {
        Serial.println("[DualCard] Reached Card 2, starting tap pause");
        currentPosition = CARD2;
        stop();  // Stop motor during tap pause
        currentOperation = TAPPING_CARD2;
        dualCardOperationStartTime = millis();  // Reset timer for tap
      }
      break;
      
    case TAPPING_CARD1:
      if (isDualCardOperationTimedOut(getCard1TapPauseMs())) {
        // Tap complete, return to home by retracting (opposite direction)
        Serial.println("[DualCard] Card 1 tap complete, retracting " + String(getCard1ToHomeMs()) + "ms to home");
        retract();  // Card 1 is extended, so retract to return home
        previousPosition = CARD1;
        currentOperation = MOVING_TO_MIDDLE;
        dualCardOperationStartTime = millis();
      }
      break;
      
    case TAPPING_CARD2:
      if (isDualCardOperationTimedOut(getCard2TapPauseMs())) {
        // Tap complete, return to home by extending (opposite direction)
        Serial.println("[DualCard] Card 2 tap complete, extending " + String(getCard2ToHomeMs()) + "ms to home");
        extend();  // Card 2 is retracted, so extend to return home
        previousPosition = CARD2;
        currentOperation = MOVING_TO_MIDDLE;
        dualCardOperationStartTime = millis();
      }
      break;
  }
}

// ============ NEW: CALIBRATION FUNCTIONS ============

void MotorController::manualExtend() {
  if (currentOperation != IDLE) {
    Serial.println("[Manual] Stopping current operation for manual control");
    completeDualCardOperation();
  }
  
  Serial.println("[Manual] Manual extend started");
  startTimingMeasurement();
  extend();
  currentPosition = UNKNOWN;  // Manual control invalidates position
  currentOperation = MANUAL_OPERATION;
}

void MotorController::manualRetract() {
  if (currentOperation != IDLE) {
    Serial.println("[Manual] Stopping current operation for manual control");
    completeDualCardOperation();
  }
  
  Serial.println("[Manual] Manual retract started");
  startTimingMeasurement();
  retract();
  currentPosition = UNKNOWN;  // Manual control invalidates position
  currentOperation = MANUAL_OPERATION;
}

void MotorController::manualStop() {
  if (currentOperation != IDLE) {
    Serial.println("[Manual] Stopping current operation");
    completeDualCardOperation();
  } else {
    Serial.println("[Manual] Manual stop");
    stop();
  }
  
  currentOperation = IDLE;
  
  // Capture timing measurement if active
  if (timingMeasurementActive) {
    unsigned long elapsed = millis() - manualTimingStart;
    Serial.println("[Timing] CAPTURED: " + String(elapsed) + "ms");
    Serial.println("[Timing] Use this value in your timing constants");
    timingMeasurementActive = false;
  }
}

void MotorController::captureCurrentAsMiddle() {
  // Stop any current operation
  if (currentOperation != IDLE) {
    completeDualCardOperation();
  }
  
  // Set current position as middle
  currentPosition = MIDDLE;
  Serial.println("[Calibration] Current position captured as MIDDLE");
  Serial.println("[Calibration] You can now use tap functions from this position");
  mqttHandler.publishDetailedStatus();  // Enhanced: publish updated position status
}

void MotorController::startTimingMeasurement() {
  manualTimingStart = millis();
  timingMeasurementActive = true;
  Serial.println("[Timing] Started measurement - use manual stop to capture duration");
}

String MotorController::getTimingInfo() const {
  if (!timingMeasurementActive) {
    return "No timing measurement active";
  }
  
  unsigned long elapsed = millis() - manualTimingStart;
  return "Manual timing: " + String(elapsed) + "ms (active since manual start)";
}

// ============ NEW: POWER SOURCE MANAGEMENT ============

void MotorController::setPowerSource12V() {
  is12VPower = true;
  Serial.println("[Power] Set to 12V external power - using fast measured timing");
}

void MotorController::setPowerSourceUSB() {
  is12VPower = false;
  Serial.println("[Power] Set to USB power - using slow timing (2.3x multiplier)");
}

String MotorController::getPowerSourceString() const {
  return is12VPower ? "12V" : "USB";
}

// ============ NEW: ENHANCED STATUS REPORTING ============

String MotorController::getPositionString() const {
  switch (currentPosition) {
    case UNKNOWN: return "unknown";
    case MIDDLE: return "middle";
    case CARD1: return "card1";
    case CARD2: return "card2";
    default: return "invalid";
  }
}

String MotorController::getOperationString() const {
  switch (currentOperation) {
    case IDLE: return "idle";
    case MOVING_TO_MIDDLE: return "moving_to_middle";
    case MOVING_TO_CARD1: return "moving_to_card1";
    case MOVING_TO_CARD2: return "moving_to_card2";
    case TAPPING_CARD1: return "tapping_card1";
    case TAPPING_CARD2: return "tapping_card2";
    case MANUAL_OPERATION: return "manual_operation";
    default: return "invalid";
  }
}

// ============ NEW: TIMING HELPER FUNCTIONS ============

unsigned long MotorController::getCard1FromHomeMs() const {
  return is12VPower ? CARD1_FROM_HOME_12V_MS : CARD1_FROM_HOME_USB_MS;
}

unsigned long MotorController::getCard1TapPauseMs() const {
  return is12VPower ? CARD1_TAP_PAUSE_12V_MS : CARD1_TAP_PAUSE_USB_MS;
}

unsigned long MotorController::getCard1ToHomeMs() const {
  return is12VPower ? CARD1_TO_HOME_12V_MS : CARD1_TO_HOME_USB_MS;
}

unsigned long MotorController::getCard2FromHomeMs() const {
  return is12VPower ? CARD2_FROM_HOME_12V_MS : CARD2_FROM_HOME_USB_MS;
}

unsigned long MotorController::getCard2TapPauseMs() const {
  return is12VPower ? CARD2_TAP_PAUSE_12V_MS : CARD2_TAP_PAUSE_USB_MS;
}

unsigned long MotorController::getCard2ToHomeMs() const {
  return is12VPower ? CARD2_TO_HOME_12V_MS : CARD2_TO_HOME_USB_MS;
}

unsigned long MotorController::getHomeFromExtendedMs() const {
  return is12VPower ? HOME_FROM_EXTENDED_12V_MS : HOME_FROM_EXTENDED_USB_MS;
}

unsigned long MotorController::getHomeFromRetractedMs() const {
  return is12VPower ? HOME_FROM_RETRACTED_12V_MS : HOME_FROM_RETRACTED_USB_MS;
}

unsigned long MotorController::getExtendFullMs() const {
  return is12VPower ? EXTEND_FULL_12V_MS : EXTEND_FULL_USB_MS;
}

unsigned long MotorController::getRetractFullMs() const {
  return is12VPower ? RETRACT_FULL_12V_MS : RETRACT_FULL_USB_MS;
}

// ============ NEW: INTERNAL DUAL CARD OPERATIONS ============

void MotorController::startDualCardOperation(Operation op) {
  Serial.println("[DualCard] Starting operation: " + getOperationString() + " at " + String(millis()) + "ms");
  Serial.println("[DualCard] From position: " + getPositionString());
  
  previousPosition = currentPosition;
  currentOperation = op;
  dualCardOperationStartTime = millis();
}

void MotorController::completeDualCardOperation() {
  unsigned long operationDuration = millis() - dualCardOperationStartTime;
  Serial.println("[DualCard] Operation completed after " + String(operationDuration) + "ms");
  Serial.println("[DualCard] Final position: " + getPositionString());
  
  stop();
  currentOperation = IDLE;
  mqttHandler.publishDetailedStatus();  // Enhanced: publish detailed dual card status
}

bool MotorController::isDualCardOperationTimedOut(unsigned long timeoutMs) {
  return (millis() - dualCardOperationStartTime) >= timeoutMs;
}