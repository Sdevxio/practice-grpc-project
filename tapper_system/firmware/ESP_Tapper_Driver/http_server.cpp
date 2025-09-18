#include "http_server.h"
#include "motor_controller.h"
#include "command_router.h"
#include <SPIFFS.h>
#include <WebServer.h>
#include <WiFi.h>
#include <ArduinoJson.h>
#include "wifi_config.h"

extern MotorController motorController;
uint8_t assignedStationId = 0;
bool isAssignmentPersistent = false;

HTTPServer::HTTPServer(CommandRouter& router)
  : commandRouter(router) {}

void HTTPServer::init() {
  if (!SPIFFS.begin(true)) {
    Serial.println("[HTTP] Failed to mount SPIFFS");
  } else {
    Serial.println("[HTTP] SPIFFS mounted successfully");
  }

  server.on("/", HTTP_GET, [this]() {
    this->serveIndex();
  });

  server.on("/command", HTTP_POST, [this]() {
    if (server.hasArg("plain")) {
      String body = server.arg("plain");
      Serial.println("[HTTP] Received JSON: " + body);
      commandRouter.handleJsonCommand(body);
      server.send(200, "application/json", "{\"success\": true}");
    } else {
      server.send(400, "application/json", "{\"success\": false, \"error\": \"No body\"}");
    }
  });

  server.on("/style.css", HTTP_GET, [this]() {
    if (SPIFFS.exists("/style.css")) {
      File file = SPIFFS.open("/style.css", "r");
      server.streamFile(file, "text/css");
      file.close();
    } else {
      server.send(404, "text/plain", "style.css not found");
    }
  });

  // Basic motor control endpoints
  server.on("/extend", HTTP_GET, [this]() {
    unsigned long start = millis();
    commandRouter.handleCommand("extend");
    server.send(200, "text/plain", "Extending");
    Serial.println("[HTTP] /extend processed in " + String(millis() - start) + "ms");
  });

  server.on("/retract", HTTP_GET, [this]() {
    unsigned long start = millis();
    commandRouter.handleCommand("retract");
    server.send(200, "text/plain", "Retracting");
    Serial.println("[HTTP] /retract processed in " + String(millis() - start) + "ms");
  });

  server.on("/stop", HTTP_GET, [this]() {
    unsigned long start = millis();
    commandRouter.handleCommand("stop");
    server.send(200, "text/plain", "Stopped");
    Serial.println("[HTTP] /stop processed in " + String(millis() - start) + "ms");
  });

  server.on("/tap", HTTP_GET, [this]() {
    unsigned long start = millis();
    commandRouter.handleCommand("tap");
    server.send(200, "text/plain", "Tap started");
    Serial.println("[HTTP] /tap processed in " + String(millis() - start) + "ms");
  });

  // NEW: Dual card operation endpoints
  server.on("/reset_to_middle", HTTP_GET, [this]() {
    commandRouter.handleCommand("reset_to_middle");
    server.send(200, "text/plain", "Reset to middle initiated");
  });

  server.on("/tap_card1", HTTP_GET, [this]() {
    commandRouter.handleCommand("tap_card1");
    server.send(200, "text/plain", "Card 1 tap initiated");
  });

  server.on("/tap_card2", HTTP_GET, [this]() {
    commandRouter.handleCommand("tap_card2");
    server.send(200, "text/plain", "Card 2 tap initiated");
  });

  // NEW: Manual control endpoints
  server.on("/manual_extend", HTTP_GET, [this]() {
    commandRouter.handleCommand("manual_extend");
    server.send(200, "text/plain", "Manual extend started");
  });

  server.on("/manual_retract", HTTP_GET, [this]() {
    commandRouter.handleCommand("manual_retract");
    server.send(200, "text/plain", "Manual retract started");
  });

  server.on("/manual_stop", HTTP_GET, [this]() {
    commandRouter.handleCommand("manual_stop");
    server.send(200, "text/plain", "Manual operation stopped");
  });

  server.on("/capture_middle", HTTP_GET, [this]() {
    commandRouter.handleCommand("capture_middle");
    server.send(200, "text/plain", "Current position captured as middle");
  });

  // NEW: Power source endpoints
  server.on("/power_12v", HTTP_GET, [this]() {
    commandRouter.handleCommand("power_12v");
    server.send(200, "text/plain", "Power source set to 12V external");
  });

  server.on("/power_usb", HTTP_GET, [this]() {
    commandRouter.handleCommand("power_usb");
    server.send(200, "text/plain", "Power source set to USB (slow timing)");
  });

  // NEW: Time-based operation endpoints (relay mimicking)
  server.on("/extend_for_time", HTTP_POST, [this]() {
    if (server.hasArg("duration")) {
      unsigned long duration = server.arg("duration").toInt();

      StaticJsonDocument<128> cmd;
      cmd["action"] = "extend_for_time";
      cmd["duration_ms"] = duration;

      String cmdStr;
      serializeJson(cmd, cmdStr);
      commandRouter.handleJsonCommand(cmdStr);

      server.send(200, "application/json", "{\"success\": true, \"action\": \"extend_for_time\", \"duration_ms\": " + String(duration) + "}");
    } else {
      server.send(400, "application/json", "{\"success\": false, \"error\": \"Missing duration parameter\"}");
    }
  });

  server.on("/retract_for_time", HTTP_POST, [this]() {
    if (server.hasArg("duration")) {
      unsigned long duration = server.arg("duration").toInt();

      StaticJsonDocument<128> cmd;
      cmd["action"] = "retract_for_time";
      cmd["duration_ms"] = duration;

      String cmdStr;
      serializeJson(cmd, cmdStr);
      commandRouter.handleJsonCommand(cmdStr);

      server.send(200, "application/json", "{\"success\": true, \"action\": \"retract_for_time\", \"duration_ms\": " + String(duration) + "}");
    } else {
      server.send(400, "application/json", "{\"success\": false, \"error\": \"Missing duration parameter\"}");
    }
  });

  // Enhanced status endpoint with dual card information
  server.on("/status", HTTP_GET, [this]() {
    String detailedStatus = "Position: " + motorController.getPositionString() + ", Operation: " + motorController.getOperationString() + ", Power: " + motorController.getPowerSourceString();

    // Add timing info if measurement is active
    String timingInfo = motorController.getTimingInfo();
    if (timingInfo != "No timing measurement active") {
      detailedStatus += ", " + timingInfo;
    }

    server.send(200, "text/plain", detailedStatus);
  });

  // Device info endpoint
  server.on("/api/info", HTTP_GET, [this]() {
    StaticJsonDocument<256> doc;
    doc["device_id"] = WiFiConfig::getDeviceID();
    doc["ip"] = WiFi.localIP().toString();
    doc["mqtt_connected"] = true;  // or actual status
    doc["supports_dual_cards"] = true;
    doc["positioning_method"] = "timing_based";
    String json;
    serializeJson(doc, json);
    server.send(200, "application/json", json);
  });

  // Enhanced status endpoint with dual card info
  server.on("/api/detailed_status", HTTP_GET, [this]() {
    StaticJsonDocument<512> doc;
    doc["device_id"] = WiFiConfig::getDeviceID();
    doc["state"] = motorController.getState();
    doc["is_tapping"] = motorController.isTapping();
    doc["positioning_method"] = "timing_based";
    doc["supports_time_operations"] = true;
    doc["timestamp"] = millis();

    // NEW: Dual card status information
    doc["supports_dual_cards"] = true;
    doc["position"] = motorController.getPositionString();
    doc["operation"] = motorController.getOperationString();
    doc["power_source"] = motorController.getPowerSourceString();
    doc["timing_info"] = motorController.getTimingInfo();

    String json;
    serializeJson(doc, json);
    server.send(200, "application/json", json);
  });

  // Station assignment endpoints (unchanged)
  server.on("/api/station", HTTP_GET, [this]() {
    StaticJsonDocument<128> doc;
    doc["station_id"] = assignedStationId;
    doc["station_name"] = assignedStationId == 0 ? "unassigned" : "Station " + String(assignedStationId);
    doc["is_persistent"] = isAssignmentPersistent;
    String json;
    serializeJson(doc, json);
    server.send(200, "application/json", json);
  });

  server.on("/api/station", HTTP_POST, [this]() {
    if (!server.hasArg("plain")) {
      server.send(400, "application/json", R"({"success":false,"message":"Missing body"})");
      return;
    }

    StaticJsonDocument<128> doc;
    DeserializationError err = deserializeJson(doc, server.arg("plain"));

    if (err || !doc.containsKey("station_id")) {
      server.send(400, "application/json", R"({"success":false,"message":"Invalid JSON"})");
      return;
    }

    assignedStationId = doc["station_id"];
    isAssignmentPersistent = doc["persistent"] | false;

    Serial.printf("[Station] Assigned to Station %d (persistent: %s)\n",
                  assignedStationId,
                  isAssignmentPersistent ? "true" : "false");

    StaticJsonDocument<128> response;
    response["success"] = true;
    response["message"] = "Station assignment updated";
    String out;
    serializeJson(response, out);
    server.send(200, "application/json", out);
  });

  server.begin();
  Serial.println("[HTTP] Relay-mimicking server started");
}

void HTTPServer::loop() {
  server.handleClient();
}

void HTTPServer::serveIndex() {
  if (SPIFFS.exists("/index.html")) {
    File file = SPIFFS.open("/index.html", "r");
    server.streamFile(file, "text/html");
    file.close();
  } else {
    // Fallback HTML with dual card support info
    String html = R"rawliteral(
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ESP32 Dual Card Tapper Control</title>
    <style>
        :root {
            --primary: #6366f1;
            --primary-hover: #4f46e5;
            --success: #10b981;
            --success-hover: #059669;
            --warning: #f59e0b;
            --warning-hover: #d97706;
            --danger: #ef4444;
            --danger-hover: #dc2626;
            --bg-primary: #ffffff;
            --bg-secondary: #f8fafc;
            --bg-tertiary: #f1f5f9;
            --text-primary: #1e293b;
            --text-secondary: #64748b;
            --border: #e2e8f0;
            --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        }

        [data-theme="dark"] {
            --primary: #818cf8;
            --primary-hover: #6366f1;
            --success: #34d399;
            --success-hover: #10b981;
            --warning: #fbbf24;
            --warning-hover: #f59e0b;
            --danger: #f87171;
            --danger-hover: #ef4444;
            --bg-primary: #1e293b;
            --bg-secondary: #334155;
            --bg-tertiary: #475569;
            --text-primary: #f8fafc;
            --text-secondary: #cbd5e1;
            --border: #475569;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: var(--text-primary);
            background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-tertiary) 100%);
            min-height: 100vh;
            transition: all 0.3s ease;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
            background: var(--bg-primary);
            border-radius: 20px;
            box-shadow: var(--shadow-lg);
            margin: 2rem auto;
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid var(--border);
        }

        .title {
            font-size: 2.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, var(--primary) 0%, var(--success) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .theme-toggle {
            background: var(--bg-secondary);
            border: 2px solid var(--border);
            border-radius: 50px;
            padding: 0.5rem;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .theme-toggle:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow);
        }

        .status-card {
            background: linear-gradient(135deg, var(--primary) 0%, var(--success) 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 15px;
            margin-bottom: 2rem;
            box-shadow: var(--shadow);
            position: relative;
            overflow: hidden;
        }

        .status-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.1) 50%, transparent 70%);
            animation: shimmer 3s infinite;
        }

        @keyframes shimmer {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }

        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            position: relative;
            z-index: 1;
        }

        .status-item {
            display: flex;
            flex-direction: column;
        }

        .status-label {
            font-size: 0.875rem;
            opacity: 0.9;
            margin-bottom: 0.25rem;
        }

        .status-value {
            font-size: 1.125rem;
            font-weight: 600;
        }

        .section {
            margin-bottom: 2rem;
        }

        .section-title {
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .section-title::before {
            content: '';
            width: 4px;
            height: 1.5rem;
            background: linear-gradient(135deg, var(--primary) 0%, var(--success) 100%);
            border-radius: 2px;
        }

        .button-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 1rem;
        }

        .btn {
            padding: 1rem 1.5rem;
            border: none;
            border-radius: 12px;
            font-weight: 600;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            box-shadow: var(--shadow);
            position: relative;
            overflow: hidden;
        }

        .btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            transition: left 0.5s;
        }

        .btn:hover::before {
            left: 100%;
        }

        .btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        }

        .btn:active {
            transform: translateY(-1px);
        }

        .btn-primary {
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-hover) 100%);
            color: white;
        }

        .btn-success {
            background: linear-gradient(135deg, var(--success) 0%, var(--success-hover) 100%);
            color: white;
        }

        .btn-warning {
            background: linear-gradient(135deg, var(--warning) 0%, var(--warning-hover) 100%);
            color: white;
        }

        .btn-danger {
            background: linear-gradient(135deg, var(--danger) 0%, var(--danger-hover) 100%);
            color: white;
        }

        .custom-controls {
            background: var(--bg-secondary);
            padding: 1.5rem;
            border-radius: 15px;
            border: 2px solid var(--border);
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            align-items: center;
        }

        .input-group {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }

        .input-label {
            font-weight: 600;
            color: var(--text-secondary);
            font-size: 0.875rem;
        }

        .input-field {
            padding: 0.75rem 1rem;
            border: 2px solid var(--border);
            border-radius: 8px;
            background: var(--bg-primary);
            color: var(--text-primary);
            font-size: 1rem;
            transition: all 0.3s ease;
            width: 120px;
        }

        .input-field:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
        }

        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255,255,255,.3);
            border-radius: 50%;
            border-top-color: #fff;
            animation: spin 1s ease-in-out infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .pulse {
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        @media (max-width: 768px) {
            .container {
                margin: 1rem;
                padding: 1.5rem;
            }

            .title {
                font-size: 2rem;
            }

            .button-grid {
                grid-template-columns: 1fr;
            }

            .custom-controls {
                flex-direction: column;
                align-items: stretch;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 class="title">ESP32 Dual Card Tapper</h1>
            <button class="theme-toggle" onclick="toggleTheme()">
                <span id="theme-icon">🌙</span>
                <span id="theme-text">Dark</span>
            </button>
        </div>

        <div class="status-card">
            <div class="status-grid">
                <div class="status-item">
                    <div class="status-label">System Status</div>
                    <div class="status-value" id="status">
                        <span class="loading"></span> Connecting...
                    </div>
                </div>
                <div class="status-item">
                    <div class="status-label">Positioning Mode</div>
                    <div class="status-value">Timing-Based (Relay Mimicking)</div>
                </div>
                <div class="status-item">
                    <div class="status-label">Device ID</div>
                    <div class="status-value" id="device-id">
                        <span class="loading"></span> Loading...
                    </div>
                </div>
                <div class="status-item">
                    <div class="status-label">Connection</div>
                    <div class="status-value" id="connection-status">
                        <span class="pulse">●</span> Online
                    </div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2 class="section-title">⚡ Basic Controls</h2>
            <div class="button-grid">
                <button class="btn btn-success" onclick="sendCommand('extend')">
                    ⬆️ Extend
                </button>
                <button class="btn btn-warning" onclick="sendCommand('retract')">
                    ⬇️ Retract
                </button>
                <button class="btn btn-danger" onclick="sendCommand('stop')">
                    ⏹️ Emergency Stop
                </button>
                <button class="btn btn-primary" onclick="sendCommand('tap')">
                    👆 Legacy Tap
                </button>
            </div>
        </div>

        <div class="section">
            <h2 class="section-title">🎯 Dual Card Operations</h2>
            <div class="button-grid">
                <button class="btn btn-primary" onclick="sendCommand('reset_to_middle')">
                    🏠 Reset to Middle
                </button>
                <button class="btn btn-success" onclick="sendCommand('tap_card1')">
                    📱 Tap Card 1
                </button>
                <button class="btn btn-success" onclick="sendCommand('tap_card2')">
                    💳 Tap Card 2
                </button>
                <button class="btn btn-warning" onclick="sendTimedCommand('extend_for_time', 2000)">
                    ⏱️ Extend 2s
                </button>
                <button class="btn btn-warning" onclick="sendTimedCommand('retract_for_time', 2000)">
                    ⏱️ Retract 2s
                </button>
                <button class="btn btn-primary" onclick="sendTimedCommand('extend_for_time', 1500)">
                    🎯 To Middle (1.5s)
                </button>
            </div>
        </div>

        <div class="section">
            <h2 class="section-title">🔧 Custom Timing Controls</h2>
            <div class="custom-controls">
                <div class="input-group">
                    <label class="input-label">Duration (ms)</label>
                    <input type="number" id="duration" class="input-field" value="1000" min="100" max="5000">
                </div>
                <button class="btn btn-success" onclick="customExtend()">
                    ⬆️ Custom Extend
                </button>
                <button class="btn btn-warning" onclick="customRetract()">
                    ⬇️ Custom Retract
                </button>
            </div>
        </div>

        <div class="section">
            <h2 class="section-title">⚙️ Power & Calibration</h2>
            <div class="button-grid">
                <button class="btn btn-primary" onclick="sendCommand('power_12v')">
                    🔋 12V Power Mode
                </button>
                <button class="btn btn-warning" onclick="sendCommand('power_usb')">
                    🔌 USB Power Mode
                </button>
                <button class="btn btn-success" onclick="sendCommand('capture_middle')">
                    📍 Capture Middle Position
                </button>
                <button class="btn btn-primary" onclick="sendCommand('manual_extend')">
                    🎛️ Manual Extend
                </button>
                <button class="btn btn-warning" onclick="sendCommand('manual_retract')">
                    🎛️ Manual Retract
                </button>
                <button class="btn btn-danger" onclick="sendCommand('manual_stop')">
                    🛑 Manual Stop
                </button>
            </div>
        </div>
    </div>

    <script>
        // Theme management
        function toggleTheme() {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);

            const icon = document.getElementById('theme-icon');
            const text = document.getElementById('theme-text');

            if (newTheme === 'dark') {
                icon.textContent = '🌙';
                text.textContent = 'Dark';
            } else {
                icon.textContent = '☀️';
                text.textContent = 'Light';
            }
        }

        // Initialize theme
        function initTheme() {
            const savedTheme = localStorage.getItem('theme') || 'light';
            document.documentElement.setAttribute('data-theme', savedTheme);

            const icon = document.getElementById('theme-icon');
            const text = document.getElementById('theme-text');

            if (savedTheme === 'dark') {
                icon.textContent = '🌙';
                text.textContent = 'Dark';
            } else {
                icon.textContent = '☀️';
                text.textContent = 'Light';
            }
        }

        // Command functions
        function sendCommand(command) {
            const button = event.target;
            const originalText = button.innerHTML;

            // Show loading state
            button.innerHTML = '<span class="loading"></span> Executing...';
            button.disabled = true;

            fetch('/' + command)
                .then(response => response.text())
                .then(data => {
                    console.log('Command sent:', data);
                    setTimeout(updateStatus, 500);

                    // Show success feedback
                    button.innerHTML = '✅ Success';
                    setTimeout(() => {
                        button.innerHTML = originalText;
                        button.disabled = false;
                    }, 1000);
                })
                .catch(error => {
                    console.error('Error:', error);

                    // Show error feedback
                    button.innerHTML = '❌ Error';
                    setTimeout(() => {
                        button.innerHTML = originalText;
                        button.disabled = false;
                    }, 2000);
                });
        }

        function sendTimedCommand(command, duration) {
            const button = event.target;
            const originalText = button.innerHTML;

            button.innerHTML = '<span class="loading"></span> Executing...';
            button.disabled = true;

            fetch('/' + command, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: 'duration=' + duration
            })
                .then(response => response.json())
                .then(data => {
                    console.log('Timed command sent:', data);
                    setTimeout(updateStatus, 500);

                    button.innerHTML = '✅ Success';
                    setTimeout(() => {
                        button.innerHTML = originalText;
                        button.disabled = false;
                    }, 1000);
                })
                .catch(error => {
                    console.error('Error:', error);

                    button.innerHTML = '❌ Error';
                    setTimeout(() => {
                        button.innerHTML = originalText;
                        button.disabled = false;
                    }, 2000);
                });
        }

        function customExtend() {
            const duration = document.getElementById('duration').value;
            sendTimedCommand('extend_for_time', duration);
        }

        function customRetract() {
            const duration = document.getElementById('duration').value;
            sendTimedCommand('retract_for_time', duration);
        }

        function updateStatus() {
            fetch('/status')
                .then(response => response.text())
                .then(data => {
                    document.getElementById('status').textContent = data;
                    updateConnectionStatus(true);
                })
                .catch(error => {
                    console.error('Status update error:', error);
                    document.getElementById('status').textContent = 'Connection Error';
                    updateConnectionStatus(false);
                });
        }

        function updateDeviceInfo() {
            fetch('/api/info')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('device-id').textContent = data.device_id || 'Unknown';
                })
                .catch(error => {
                    console.error('Device info error:', error);
                    document.getElementById('device-id').textContent = 'Unavailable';
                });
        }

        function updateConnectionStatus(isConnected) {
            const statusElement = document.getElementById('connection-status');
            if (isConnected) {
                statusElement.innerHTML = '<span class="pulse" style="color: #10b981;">●</span> Online';
            } else {
                statusElement.innerHTML = '<span class="pulse" style="color: #ef4444;">●</span> Offline';
            }
        }

        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            initTheme();
            updateStatus();
            updateDeviceInfo();

            // Update status every 2 seconds
            setInterval(updateStatus, 2000);
        });
    </script>
</body>
</html>
    )rawliteral";

    server.send(200, "text/html", html);
  }
}