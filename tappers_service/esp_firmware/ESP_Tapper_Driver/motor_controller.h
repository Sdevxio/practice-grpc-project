// motor_controller.h - Simplified for relay mimicking only
#ifndef MOTOR_CONTROLLER_H
#define MOTOR_CONTROLLER_H

#include <Arduino.h>

class MotorController {
public:
  // Position states for dual card support
  enum Position {
    UNKNOWN,
    MIDDLE,
    CARD1,  // Extended position
    CARD2   // Retracted position
  };

  // Operation states for dual card support
  enum Operation {
    IDLE,
    MOVING_TO_MIDDLE,
    MOVING_TO_CARD1,
    MOVING_TO_CARD2,
    TAPPING_CARD1,
    TAPPING_CARD2,
    MANUAL_OPERATION
  };

  void init();
  void extend();
  void retract();
  void stop();
  
  // Time-based operations (relay mimicking)
  void extendForTime(unsigned long duration_ms);
  void retractForTime(unsigned long duration_ms);
  void updateTimedOperations();  // Call this in main loop
  
  // Legacy tap functions
  void tap();
  void startTap();
  void updateTap();
  bool isTapping() const;
  
  // NEW: Dual card functions
  void resetToMiddle();
  void tapCard1();
  void tapCard2();
  void updateDualCardOperations();  // Call in main loop
  
  // NEW: Calibration functions
  void manualExtend();
  void manualRetract();
  void manualStop();
  void captureCurrentAsMiddle();
  void startTimingMeasurement();
  String getTimingInfo() const;
  
  // NEW: Power source management
  void setPowerSource12V();
  void setPowerSourceUSB();
  String getPowerSourceString() const;
  
  // Enhanced status functions
  String getState() const;
  Position getCurrentPosition() const { return currentPosition; }
  Operation getCurrentOperation() const { return currentOperation; }
  String getPositionString() const;
  String getOperationString() const;
  void checkLimitSwitches();  // Safety timeout only

private:
  enum State {
    STATE_IDLE,
    STATE_EXTENDING,
    STATE_RETRACTING
  };

  enum TapState {
    TAP_IDLE,
    TAP_EXTENDING,
    TAP_PAUSE,
    TAP_RETRACTING,
    TAP_COMPLETE
  };

  // Basic motor state
  State currentState = STATE_IDLE;
  
  // Legacy tap state
  TapState tapState = TAP_IDLE;
  unsigned long tapStartTime = 0;
  unsigned long tapTimeout = 2000;    // 2 second timeout
  unsigned long tapPauseDelay = 200;  // 200ms pause between extend/retract
  
  // Time-based operation variables
  bool timedOperation = false;
  unsigned long operationStartTime = 0;
  unsigned long operationDuration = 0;
  State timedOperationState = STATE_IDLE;  // What timed operation is running
  
  // NEW: Dual card state variables
  Position currentPosition = UNKNOWN;
  Position previousPosition = UNKNOWN;
  Operation currentOperation = IDLE;
  unsigned long dualCardOperationStartTime = 0;
  
  // NEW: Manual timing measurement
  unsigned long manualTimingStart = 0;
  bool timingMeasurementActive = false;
  
  // NEW: Power source tracking
  bool is12VPower = true;  // Default to 12V
  
  // NEW: Measured timing constants (calibrated values)
  // 12V External Power (fast) - MEASURED VALUES
  static const unsigned long CARD1_FROM_HOME_12V_MS = 1100;    // Card 1 tap: extend to card
  static const unsigned long CARD1_TAP_PAUSE_12V_MS = 1000;    // Card 1 tap: pause at card
  static const unsigned long CARD1_TO_HOME_12V_MS = 1100;      // Card 1 tap: return to home (balanced)
  static const unsigned long CARD2_FROM_HOME_12V_MS = 1300;    // Card 2 tap: retract to card
  static const unsigned long CARD2_TAP_PAUSE_12V_MS = 1000;    // Card 2 tap: pause at card
  static const unsigned long CARD2_TO_HOME_12V_MS = 1300;      // Card 2 tap: return to home (balanced)
  static const unsigned long HOME_FROM_EXTENDED_12V_MS = 1306; // MEASURED: middle from extended (2611ms ÷ 2)
  static const unsigned long HOME_FROM_RETRACTED_12V_MS = 1284; // MEASURED: middle from retracted (2568ms ÷ 2)
  static const unsigned long EXTEND_FULL_12V_MS = 2568;        // MEASURED: full extend travel time
  static const unsigned long RETRACT_FULL_12V_MS = 2611;       // MEASURED: full retract travel time
  
  // USB Power (slow) - Calculated from 12V measurements with 2.3x multiplier
  static const unsigned long CARD1_FROM_HOME_USB_MS = 2530;    // 1100 * 2.3
  static const unsigned long CARD1_TAP_PAUSE_USB_MS = 1000;    // Same pause time
  static const unsigned long CARD1_TO_HOME_USB_MS = 2530;      // Balanced timing
  static const unsigned long CARD2_FROM_HOME_USB_MS = 2990;    // 1300 * 2.3
  static const unsigned long CARD2_TAP_PAUSE_USB_MS = 1000;    // Same pause time
  static const unsigned long CARD2_TO_HOME_USB_MS = 2990;      // Balanced timing
  static const unsigned long HOME_FROM_EXTENDED_USB_MS = 3004; // 1306 * 2.3
  static const unsigned long HOME_FROM_RETRACTED_USB_MS = 2953; // 1284 * 2.3
  static const unsigned long EXTEND_FULL_USB_MS = 5906;        // 2568 * 2.3
  static const unsigned long RETRACT_FULL_USB_MS = 6005;       // 2611 * 2.3
  
  // NEW: Timing helper functions
  unsigned long getCard1FromHomeMs() const;
  unsigned long getCard1TapPauseMs() const;
  unsigned long getCard1ToHomeMs() const;
  unsigned long getCard2FromHomeMs() const;
  unsigned long getCard2TapPauseMs() const;
  unsigned long getCard2ToHomeMs() const;
  unsigned long getHomeFromExtendedMs() const;
  unsigned long getHomeFromRetractedMs() const;
  unsigned long getExtendFullMs() const;
  unsigned long getRetractFullMs() const;
  
  // NEW: Internal dual card operations
  void startDualCardOperation(Operation op);
  void completeDualCardOperation();
  bool isDualCardOperationTimedOut(unsigned long timeoutMs);
};

#endif