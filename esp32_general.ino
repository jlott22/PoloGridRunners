#include <WiFi.h>
#include "ESP32MQTTClient.h"

// Wi-Fi credentials
const char *ssid = "USDresearch";
const char *pass = "USDresearch";

// MQTT broker details
const char *server = "mqtt://192.168.1.10:1883"; // MQTT server IP

// Topics
const char *subscribeCommandTopic = "robots/command";  // Command topic
const char *publishTopic = "robots/status";           // Status topic for publishing
const char *lastWillMessage = "00 disconnected";   // Last Will message

ESP32MQTTClient mqttClient; // MQTT client object

// UART Configuration
#define RXD2 16  // UART RX pin
#define TXD2 17  // UART TX pin
HardwareSerial robotSerial(2); // UART2 for Pololu communication

void setup()
{
    // Initialize debugging
    Serial.begin(115200);
    robotSerial.begin(115200, SERIAL_8N1, RXD2, TXD2);

    // Connect to Wi-Fi
    Serial.println("Connecting to Wi-Fi...");
    WiFi.begin(ssid, pass);
    while (WiFi.status() != WL_CONNECTED)
    {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\nConnected to Wi-Fi!");

    // MQTT Client Setup
    mqttClient.setURI(server);
    mqttClient.enableDebuggingMessages(); // Enable MQTT debug logs

    // Set Last Will Message
    mqttClient.enableLastWillMessage(publishTopic, lastWillMessage); // Topic: robots/status, Message: 01 disconnected

    mqttClient.setKeepAlive(30); // Keep connection alive with a 30-second timeout

    // Start the MQTT loop
    mqttClient.loopStart();
}

void onMqttConnect(esp_mqtt_client_handle_t client)
{
    if (mqttClient.isMyTurn(client))
    {
        Serial.println("Connected to MQTT Broker!");

        // Subscribe to the command topic
        mqttClient.subscribe(subscribeCommandTopic, [](const String &payload)
                             {
                                 Serial.println("Received Command: " + payload);
                                 robotSerial.println(payload); // Send command to Pololu robot
                             });
        Serial.println("Subscribed to robots/command");

    }
}

void loop()
{
    // Check for responses from the Pololu robot
    if (robotSerial.available())
    {
        String response = robotSerial.readStringUntil('\n');
        Serial.println("Received from Pololu: " + response);

        // Publish response back to the robots/status topic
        mqttClient.publish(publishTopic, response, 0, false);
    }

    delay(100); // Short delay to prevent busy looping
}

void handleMQTT(void *handler_args, esp_event_base_t base, int32_t event_id, void *event_data)
{
    auto *event = static_cast<esp_mqtt_event_handle_t>(event_data);
    mqttClient.onEventCallback(event); // Pass events to the client
}
