import sys
print("Python version:", sys.version)
print("Python paths:", sys.path)

import paho.mqtt.client as mqtt
print("paho-mqtt imported successfully")

#stop search pattern if line found
stop_flag = False

#establishes repeating directions for robot search
def search_pattern(robotid):
    pattern_leg = pattern_dict.get(robotid)
    if pattern_leg%16 == 1:
        pattern_dict[robotid] += 1
        return "1"
    elif pattern_leg%16 == 2:
        pattern_dict[robotid] += 1
        return "R"
    elif pattern_leg%16 == 3:
        pattern_dict[robotid] += 1
        return "1"
    elif pattern_leg%16 == 4:
        pattern_dict[robotid] += 1
        return "R"
    elif pattern_leg%16 == 5:
        pattern_dict[robotid] += 1
        return "1"
    elif pattern_leg%16 == 6:
        pattern_dict[robotid] += 1
        return "L"
    elif pattern_leg%16 == 7:
        pattern_dict[robotid] += 1
        return "1"
    elif pattern_leg%16 == 8:
        pattern_dict[robotid] += 1
        return "L"  
    elif pattern_leg%16 == 9:
        pattern_dict[robotid] += 1
        return "1" 
    elif pattern_leg%16 == 10:
        pattern_dict[robotid] += 1
        return "L"  
    elif pattern_leg%16 == 11:
        pattern_dict[robotid] += 1
        return "1" 
    elif pattern_leg%16 == 12:
        pattern_dict[robotid] += 1
        return "L"  
    elif pattern_leg%16 == 13:
        pattern_dict[robotid] += 1
        return "1" 
    elif pattern_leg%16 == 14:
        pattern_dict[robotid] += 1
        return "R"
    elif pattern_leg%16 == 15:
        pattern_dict[robotid] += 1
        return "1"
    elif pattern_leg%16 == 0:
        pattern_dict[robotid] += 1
        return "R"

#function to parse message
def parse_message(message):
    if ':' in message:
        directive, coordinates = message.split(':')
        x, y = coordinates.split('/')
        return (directive, x, y)
    elif "L" or "R" in message:
        return message
    else:
        x, y = message.split('/')
        return ('update', x, y)


# MQTT Configuration
BROKER_IP = "192.168.1.10"  
robotstatus = ["00/status","01/status","02/status","03/status"] 
generalcommand = "general/command"
robotcommand = ["00/command","01/command","02/command","03/command"]

# Initialize a dictionary to store robot statuses
#key is robot id (ex: 00), value is robot contents in the form of (directive, x, y)
status_dict = {}
#tracks which leg of search pattern robot is on. All intialized on leg 1 (100)
pattern_dict = {"00":2,"01":2,"02":2,"03":2,"04":2}

# Callback for when a message is received
def on_message(hub, userdata, msg):
    """Handle received messages."""
    global stop_flag
    topic = msg.topic
    message = msg.payload.decode("utf-8")
    robot_id = topic.split("/")[0]
    
   #contents = (directive(either line, bingo, stop or none), x-coordinate, y-coordinate)
    if message == 'disconnected':
        hub.publish(generalcommand, "stop")
    else:
        contents = parse_message(message)
        if contents[0] == 'line':
            hub.publish(generalcommand, "stop")
            stop_flag = True
        elif contents[0] == 'bingo':
            hub.publish(generalcommand, "stop")
            retur
        elif contents[0] == 'stop':
            return
        elif not stop_flag:
            leg_dir = search_pattern(robot_id)
            hub.publish(str(robot_id) + "/command", leg_dir)
        #update coordinates and directive of robot if status wasnt just a turn
        if "L" or "R" not in contents[0]:
            status_dict[robot_id] = contents

# Set up the MQTT client and assign it to `hub`
hub = mqtt.Client()
hub.on_message = on_message  # Register the callback
hub.connect(BROKER_IP, 1883, 60)
# Subscribe to the robots' status topic
for bot in robotstatus:
    hub.subscribe(bot)  

hub.loop_start()  # Start processing events in the background

print("Hub running. Press Ctrl+C to stop.")

#start bots
hub.publish(generalcommand, "1")

try:
    while True:
        pass  # Keep the program running
except KeyboardInterrupt:
    print("Shutting down hub...")
    hub.publish(generalcommand, "stop")
    
finally:
    hub.loop_stop()
    hub.disconnect()

'''
setup to monitor bots and hub comms in terminal:
mosquitto_sub -h 192.168.1.10 -t "00/status"
mosquitto_sub -h 192.168.1.10 -t "01/status"
mosquitto_sub -h 192.168.1.10 -t "02/status"
mosquitto_sub -h 192.168.1.10 -t "03/status"
mosquitto_sub -h 192.168.1.10 -t "general/command"
ex manual command:
mosquitto_pub -h 192.168.1.10 -t "general/command" -m "100"
'''