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
  
  // NEW: Smart drift compensation
  int card1DriftAccumulator = 0;  // Accumulated drift in ms for Card 1
  int card2DriftAccumulator = 0;  // Accumulated drift in ms for Card 2
  static const int DRIFT_PER_TAP_MS = 5;  // 5ms drift per tap cycle
  static const int MAX_DRIFT_COMPENSATION = 50;  // Max 50ms compensation
  
  // NEW: Measured timing constants (calibrated values) - MICROSECOND PRECISION
  // 12V External Power (fast) - MEASURED VALUES in microseconds
  static const unsigned long CARD1_FROM_HOME_12V_US = 1000000;    // Card 1 tap: extend to card (1000ms = 1,000,000μs)
  static const unsigned long CARD1_TAP_PAUSE_12V_US = 100000;     // Card 1 tap: pause at card (100ms = 100,000μs)
  static const unsigned long CARD1_TO_HOME_12V_US = 995000;       // Card 1 tap: return to home (995ms = 995,000μs, 5ms drift compensation)
  static const unsigned long CARD2_FROM_HOME_12V_US = 1400000;    // Card 2 tap: retract to card (1400ms = 1,400,000μs)
  static const unsigned long CARD2_TAP_PAUSE_12V_US = 100000;     // Card 2 tap: pause at card (100ms = 100,000μs)
  static const unsigned long CARD2_TO_HOME_12V_US = 1395000;      // Card 2 tap: return to home (1395ms = 1,395,000μs, 5ms drift compensation)
  static const unsigned long HOME_FROM_EXTENDED_12V_US = 1306000; // MEASURED: middle from extended (1306ms = 1,306,000μs)
  static const unsigned long HOME_FROM_RETRACTED_12V_US = 1284000; // MEASURED: middle from retracted (1284ms = 1,284,000μs)
  static const unsigned long EXTEND_FULL_12V_US = 2568000;        // MEASURED: full extend travel time (2568ms = 2,568,000μs)
  static const unsigned long RETRACT_FULL_12V_US = 2611000;       // MEASURED: full retract travel time (2611ms = 2,611,000μs)
  
  // USB Power (slow) - Calculated from 12V measurements with 2.3x multiplier in microseconds
  static const unsigned long CARD1_FROM_HOME_USB_US = 2530000;    // 2530ms = 2,530,000μs (1100 * 2.3)
  static const unsigned long CARD1_TAP_PAUSE_USB_US = 1000000;    // 1000ms = 1,000,000μs (same pause time)
  static const unsigned long CARD1_TO_HOME_USB_US = 2530000;      // 2530ms = 2,530,000μs (balanced timing)
  static const unsigned long CARD2_FROM_HOME_USB_US = 2990000;    // 2990ms = 2,990,000μs (1300 * 2.3)
  static const unsigned long CARD2_TAP_PAUSE_USB_US = 1000000;    // 1000ms = 1,000,000μs (same pause time)
  static const unsigned long CARD2_TO_HOME_USB_US = 2990000;      // 2990ms = 2,990,000μs (balanced timing)
  static const unsigned long HOME_FROM_EXTENDED_USB_US = 3004000; // 3004ms = 3,004,000μs (1306 * 2.3)
  static const unsigned long HOME_FROM_RETRACTED_USB_US = 2953000; // 2953ms = 2,953,000μs (1284 * 2.3)
  static const unsigned long EXTEND_FULL_USB_US = 5906000;        // 5906ms = 5,906,000μs (2568 * 2.3)
  static const unsigned long RETRACT_FULL_USB_US = 6005000;       // 6005ms = 6,005,000μs (2611 * 2.3)
  
  // NEW: Timing helper functions with overflow protection
  unsigned long safeElapsedMicros(unsigned long startTime) const;
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