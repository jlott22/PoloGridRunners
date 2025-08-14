# Pololu_coordination
# Multi-Agent Grid Navigation with MQTT and Pololu Robots

## Overview
This project implements a coordinated control system for **Pololu 3pi+ 2040 OLED robots** using a central MQTT hub, ESP32 bridges, and on-board robot navigation code. The system allows robots to navigate a grid, follow predefined search patterns, and report findings (e.g., line detection or object detection) back to the hub in real time.

---

## Features
- **Centralized Coordination**: A single hub script manages multiple robots.
- **MQTT Communication**: Commands and status updates are sent over a local network.
- **Grid Navigation**: Robots move to waypoints using line-following and intersection counting.
- **Search Patterns**: Hub assigns step-by-step directions for coverage.
- **Event Handling**: Robots can report special events (`line`, `bingo`, etc.) to stop or adjust movement.

---

## Repository Structure
├── MQTT_hub.py # Central hub script managing robot coordination over MQTT
├── pololu_code.py # Robot script for waypoint navigation and reporting over UART
├── esp32_general.ino # ESP32 firmware acting as MQTT-to-UART bridge between hub and robot

---

## System Architecture
       +------------------+
       |   MQTT Hub (PC)  |
       |  MQTT_hub.py     |
       +--------+---------+
                |
        MQTT over LAN
                |
       +--------+---------+
       |   MQTT Broker    |
       +--------+---------+
                |
+------+-------+ +------+-------+
| ESP32 #1 | | ESP32 #2 | ...
| esp32_general| | esp32_general|
+------+-------+ +------+-------+
| UART | UART
+------+-------+ +------+-------+
| Pololu Robot | | Pololu Robot |
| pololu_code | | pololu_code |
+--------------+ +--------------+

---

## Requirements

### Hardware
- Pololu 3pi+ 2040 OLED robots
- ESP32 module for each robot (UART connection to Pololu)
- Wi-Fi router or access point for LAN communication
- Computer to run the hub script

### Software & Libraries
**Python 3.x** on hub computer:
- `paho-mqtt`

**Arduino IDE** for ESP32:
- `ESP32MQTTClient` library
- `WiFi` library

**Pololu MicroPython environment** on robots:
- `pololu_3pi_2040_robot` package

---

## Setup

### 1. ESP32 Bridge
1. Open `esp32_general.ino` in Arduino IDE.
2. Set your Wi-Fi SSID, password, and MQTT broker IP (`192.168.1.10` by default).
3. Upload to the ESP32 connected to a Pololu robot (TX/RX pins configured for UART0).

### 2. Pololu Robot Code
1. Load `pololu_code.py` onto the Pololu 3pi+ 2040 OLED.
2. Ensure UART pins match ESP32 wiring (TX=GP28, RX=GP29).
3. The robot will receive waypoints from the ESP32 and navigate accordingly.

### 3. Hub Script
1. Run `MQTT_hub.py` on your control computer.
2. The hub will:
   - Subscribe to all robot status topics.
   - Assign search directions or waypoints.
   - Stop all robots if a special event is reported.

---

## Usage
1. Power on all ESP32 bridges and Pololu robots.
2. Start the MQTT broker (e.g., Mosquitto) on the hub’s network.
3. Run the hub script:
   ```bash
   python MQTT_hub.py
4. The hub will begin sending movement commands according to the search pattern.
5. Robots execute commands, navigate the grid, and report back their coordinates or events.

Example Workflow
1. Hub sends a 1 (move forward one cell) to a robot’s command topic.
2. Robot moves forward, counts intersections, updates its (x, y) position.
3. Robot sends updated coordinates to its status topic.
4. If robot detects a line or object (line, bingo), the hub sends stop to all robots.
