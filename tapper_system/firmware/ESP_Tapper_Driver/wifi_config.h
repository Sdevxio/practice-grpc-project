#ifndef WIFI_CONFIG_H
#define WIFI_CONFIG_H

#include <WiFi.h>
#include <Arduino.h>

namespace WiFiConfig {
  extern String deviceId;

  void connect();
  void setup();
  String getDeviceID();
}

#endif