#pragma once
#include <WebServer.h>
#include "command_router.h"

class HTTPServer {
public:
  HTTPServer(CommandRouter& router);
  void init();
  void loop();
  void serveIndex();


private:
  WebServer server{ 80 };
  CommandRouter& commandRouter;
};