#ifndef COMMAND_ROUTER_H
#define COMMAND_ROUTER_H

#include <Arduino.h>

class MotorController;

class CommandRouter {
public:
  CommandRouter(MotorController& motor);
  void init();
  void handleCommand(const String& command);
  void handleJsonCommand(const String& json);

private:
  MotorController& motorController;
};

#endif