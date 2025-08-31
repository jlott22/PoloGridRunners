import time
from machine import Pin, UART
from pololu_3pi_2040_robot import robot
from pololu_3pi_2040_robot.extras import editions

# Set up UART0 to communicate with ESP32
# TX = GP28, RX = GP29
uart = UART(0, baudrate=230400, tx=28, rx=29)

##display for debugging
display = robot.Display()

# Initialize robot components
motors = robot.Motors()
line_sensors = robot.LineSensors()
bump_sensors = robot.BumpSensors()
display = robot.Display()

command = " "
while_break = False  # Flag for breaking out of loops
first_command_received = False  # Flag to track if calibration is needed

# Grid location tracking variables
direction = ['N', 'E', 'S', 'W']  # Possible movement directions
x, y = 0, 0  # Robot's coordinates
index = 0  # Tracks direction index (0=N, 1=E, 2=S, 3=W)

# Count grid intersections
intersections_passed = 0
pending_command = None  # Store pending UART command
stop_pending = False  # Flag to indicate stop is requested

# Possible commands to move a distance
possible_distances = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']

# Base speed
base_speed = 900
max_speed = 1000  # Limit max speed

movement_target = 0  # Stores the number of intersections to move before stopping

def calibrate_sensors():
    """Performs a quick calibration before executing the first command."""
    motors.set_speeds(920, -920)  # Rotate for calibration at controlled speed
    for _ in range(50):  # Calibration loop
        line_sensors.calibrate()
        time.sleep(0.01)
    motors.set_speeds(0, 0)
    bump_sensors.calibrate()
    time.sleep(0.5)  # Pause before starting

def update_location():
    """Updates robot's position based on the direction and grid intersections passed."""
    global x, y, index, intersections_passed
    if direction[index] == 'N':
        y += intersections_passed
    elif direction[index] == 'S':
        y -= intersections_passed
    elif direction[index] == 'E':
        x += intersections_passed
    elif direction[index] == 'W':
        x -= intersections_passed
    intersections_passed = 0  # Reset after updating

def check_line_left():
    """Check if there is a line on the left sensor."""
    line = line_sensors.read_calibrated()
    return line[1] > 500

def check_line_right():
    """Check if there is a line on the right sensor."""
    line = line_sensors.read_calibrated()
    return line[3] > 500

def ride_the_line():
    """Aligns the robot with the line using proportional control and ensures accurate intersection detection."""
    last_p = 0
    global intersections_passed, pending_command, command, base_speed, max_speed, movement_target, stop_pending
    ignore_intersection_timer = time.time()

    while intersections_passed < movement_target:
        if uart.any():
            pending_command = uart.read().decode('utf-8').strip()
            if pending_command == "stop":
                stop_pending = True  # Set flag to stop at next intersection

        line = line_sensors.read_calibrated()
        line_sensors.start_read()

        if sum(line) == 0:
            continue  # Avoid division by zero

        l = (1000*line[1] + 2000*line[2] + 3000*line[3] + 4000*line[4]) // sum(line)
        p = l - 2000
        d = p - last_p
        last_p = p

        if abs(p) < 50:
            pid = 0
        else:
            pid = p * 90 + d * 300

        smoothed_pid = 0.7 * last_p + 0.3 * pid

        left = max(300, min(max_speed, base_speed + smoothed_pid))
        right = max(300, min(max_speed, base_speed - smoothed_pid))
        motors.set_speeds(left, right)

        # If it has definitely cleared the last intersection and reads there is a new one or jewel
        if ignore_intersection_timer == 0 and (line[0] > 500 or line[4] > 500):
            # Slow down to verify
            motors.set_speeds(400, 400)
            time.sleep(0.1)
            if line[0] > 500 or line[4] > 500:
                intersections_passed += 1
                #debugging to get line threshold
                display.fill(0)
                display.text(f"0: {line[0]}",0,20)
                display.text(f"4: {line[4]}",0,30)
                display.text(f"2: {line[2]}",0,40)
                display.show()
            # Check if it is a gray line (jewel)
            if line[2]<200:
                motors.set_speeds(0, 0)
                update_location()
                uart.write(f"line:{x}/{y}")
                #debugging to get line threshold
                display.fill(0)
                display.text(f"0: {line[0]}",0,20)
                display.text(f"4: {line[4]}",0,30)
                display.text(f"2: {line[2]}",0,40)
                display.show()
                ignore_intersection_timer = time.time()
                return

            # Reset timer to make sure it doesn't read the same intersection
            ignore_intersection_timer = time.time()
            
            # Return motors to normal speeds
            motors.set_speeds(base_speed, base_speed)

        if stop_pending or intersections_passed >= movement_target:
            motors.set_speeds(0, 0)
            update_location()
            uart.write(f"{x}/{y}")
            stop_pending = False  # Reset stop flag
            return


        if ignore_intersection_timer > 0 and (time.time() - ignore_intersection_timer) >= 1:
            ignore_intersection_timer = 0

        bump_sensors.read()
        if bump_sensors.left_is_pressed() or bump_sensors.right_is_pressed():
            motors.set_speeds(0, 0)
            uart.write(f"bingo:{x}/{y}")
            return

while True:
    if pending_command:
        command = pending_command
        pending_command = None

    if uart.any():
        command = uart.read().decode('utf-8').strip()

        if not first_command_received:
            calibrate_sensors()
            first_command_received = True

        if command in possible_distances:
            movement_target = int(command)
            intersections_passed = 0
            command = " "
            ride_the_line()

        elif command == "L":
            if check_line_left():
                command = " "
                motors.set_speeds(-300, 1200)
                time.sleep(.4)
                motors.set_speeds(0, 0)
                index = (index - 1) % 4
                uart.write(f"{x}/{y}")
            else:
                uart.write(f"invalid:{x}/{y}")

        elif command == "R":
            if check_line_right():
                command = " "
                motors.set_speeds(1200, -300)
                time.sleep(.4)
                motors.set_speeds(0, 0)
                index = (index + 1) % 4
                uart.write(f"{x}/{y}")
            else:
                uart.write(f"invalid:{x}/{y}")

        else:
            command = " "
