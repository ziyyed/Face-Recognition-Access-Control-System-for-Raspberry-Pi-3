#!/usr/bin/python
"""
Proteus VSM program for face recognition access control.

This script runs inside Proteus VSM and receives commands via serial
from the Python face recognition script running on your PC.

Commands received:
  - "INIT:message" - Initialize LCD with message
  - "LCD:line1|line2" - Display text on LCD (2 lines)
  - "LCD:CLEAR" - Clear LCD
  - "DOOR:OPEN:duration" - Open door for specified seconds
  - "DOOR:CLOSE" - Close door

Hardware pins (BOARD mode):
  - LCD: RS=7, E=11, D4=12, D5=13, D6=15, D7=16
  - Motor: Motor_1=29, Motor_2=31
"""

import time
import RPi.GPIO as GPIO
import pio
import Ports

# Initialize serial communication
pio.uart = Ports.UART()

# GPIO setup (BOARD mode for Proteus compatibility)
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

# LCD pin definitions (BOARD mode) - Updated to match your circuit
LCD_RS = 7
LCD_E = 11
LCD_D4 = 12
LCD_D5 = 13
LCD_D6 = 15
LCD_D7 = 16

# Motor pin definitions (BOARD mode)
Motor_1 = 29
Motor_2 = 31

# Timing constants
E_PULSE = 0.0005
E_DELAY = 0.0005

# LCD constants
LCD_WIDTH = 16
LCD_CHR = True
LCD_CMD = False
LCD_LINE_1 = 0x80
LCD_LINE_2 = 0xC0

# Setup GPIO pins
GPIO.setup(LCD_E, GPIO.OUT)
GPIO.setup(LCD_RS, GPIO.OUT)
GPIO.setup(LCD_D4, GPIO.OUT)
GPIO.setup(LCD_D5, GPIO.OUT)
GPIO.setup(LCD_D6, GPIO.OUT)
GPIO.setup(LCD_D7, GPIO.OUT)
GPIO.setup(Motor_1, GPIO.OUT)
GPIO.setup(Motor_2, GPIO.OUT)

# Initialize motor to OFF
GPIO.output(Motor_1, False)
GPIO.output(Motor_2, False)

# Motor state machine (non-blocking)
motor_state = "STOPPED"  # STOPPED, RUNNING
motor_start_time = 0.0
motor_duration = 0.0


def lcd_init():
    """Initialize the LCD display."""
    lcd_byte(0x33, LCD_CMD)  # Initialize
    lcd_byte(0x32, LCD_CMD)  # Initialize
    lcd_byte(0x06, LCD_CMD)  # Cursor move direction
    lcd_byte(0x0C, LCD_CMD)  # Display On, Cursor Off, Blink Off
    lcd_byte(0x28, LCD_CMD)  # Data length, number of lines, font size
    lcd_byte(0x01, LCD_CMD)  # Clear display
    time.sleep(E_DELAY)


def lcd_byte(bits, mode):
    """Send byte to LCD data pins."""
    GPIO.output(LCD_RS, mode)
    
    # High bits
    GPIO.output(LCD_D4, False)
    GPIO.output(LCD_D5, False)
    GPIO.output(LCD_D6, False)
    GPIO.output(LCD_D7, False)
    if bits & 0x10 == 0x10:
        GPIO.output(LCD_D4, True)
    if bits & 0x20 == 0x20:
        GPIO.output(LCD_D5, True)
    if bits & 0x40 == 0x40:
        GPIO.output(LCD_D6, True)
    if bits & 0x80 == 0x80:
        GPIO.output(LCD_D7, True)
    
    lcd_toggle_enable()
    
    # Low bits
    GPIO.output(LCD_D4, False)
    GPIO.output(LCD_D5, False)
    GPIO.output(LCD_D6, False)
    GPIO.output(LCD_D7, False)
    if bits & 0x01 == 0x01:
        GPIO.output(LCD_D4, True)
    if bits & 0x02 == 0x02:
        GPIO.output(LCD_D5, True)
    if bits & 0x04 == 0x04:
        GPIO.output(LCD_D6, True)
    if bits & 0x08 == 0x08:
        GPIO.output(LCD_D7, True)
    
    lcd_toggle_enable()


def lcd_toggle_enable():
    """Toggle the Enable pin."""
    time.sleep(E_DELAY)
    GPIO.output(LCD_E, True)
    time.sleep(E_PULSE)
    GPIO.output(LCD_E, False)
    time.sleep(E_DELAY)


def lcd_string(message, line):
    """Display string on LCD at specified line."""
    message = message.ljust(LCD_WIDTH, " ")
    lcd_byte(line, LCD_CMD)
    for i in range(LCD_WIDTH):
        lcd_byte(ord(message[i]), LCD_CHR)


def lcd_clear():
    """Clear the LCD display."""
    lcd_byte(0x01, LCD_CMD)
    time.sleep(E_DELAY)


def lcd_display(line1, line2=""):
    """Display two lines on LCD."""
    lcd_clear()
    lcd_string(line1[:LCD_WIDTH], LCD_LINE_1)
    if line2:
        lcd_string(line2[:LCD_WIDTH], LCD_LINE_2)


def door_open(duration_seconds=5.0):
    """Start door opening (non-blocking). Motor runs in one direction for specified duration."""
    global motor_state, motor_start_time, motor_duration
    motor_duration = duration_seconds
    motor_start_time = time.time()
    motor_state = "RUNNING"
    # Start motor (L293D: IN1=HIGH, IN2=LOW)
    GPIO.output(Motor_1, True)
    GPIO.output(Motor_2, False)
    print(f"[MOTOR] Door opening for {duration_seconds} seconds")


def door_close():
    """Close door (stop motor immediately)."""
    global motor_state
    motor_state = "STOPPED"
    GPIO.output(Motor_1, False)
    GPIO.output(Motor_2, False)
    print("[MOTOR] Door closed (motor stopped)")


def update_motor_state():
    """Update motor state machine (non-blocking, called from main loop)."""
    global motor_state, motor_start_time, motor_duration
    
    if motor_state == "STOPPED":
        return
    
    if motor_duration <= 0:
        motor_state = "STOPPED"
        GPIO.output(Motor_1, False)
        GPIO.output(Motor_2, False)
        return
    
    current_time = time.time()
    elapsed = current_time - motor_start_time
    
    if motor_state == "RUNNING":
        if elapsed >= motor_duration:
            # Stop motor after duration
            motor_state = "STOPPED"
            GPIO.output(Motor_1, False)
            GPIO.output(Motor_2, False)
            print(f"[MOTOR] Motor stopped after {motor_duration} seconds")


def parse_command(data):
    """Parse command received from serial and execute it."""
    # Handle bytes or string
    if isinstance(data, bytes):
        try:
            data = data.decode('utf-8')
        except:
            data = str(data)
    
    data = data.strip()
    if not data:
        return
    
    # Print received command for debugging
    pio.uart.print(f"Received: {data}")
    
    # Parse commands
    if data.startswith("INIT:"):
        # Initialize message
        message = data[5:].strip()
        lcd_display(message, "")
        
    elif data.startswith("LCD:"):
        # LCD display command: "LCD:line1|line2" or "LCD:CLEAR"
        lcd_cmd = data[4:].strip()
        if lcd_cmd == "CLEAR":
            lcd_clear()
        else:
            # Split by | to get line1 and line2
            parts = lcd_cmd.split("|", 1)
            line1 = parts[0] if parts else ""
            line2 = parts[1] if len(parts) > 1 else ""
            lcd_display(line1, line2)
    
    elif data.startswith("DOOR:"):
        # Door control: "DOOR:OPEN:duration" or "DOOR:CLOSE"
        door_cmd = data[5:].strip()
        if door_cmd == "CLOSE":
            door_close()
        elif door_cmd.startswith("OPEN:"):
            try:
                duration = float(door_cmd[5:])
                door_open(duration)
            except ValueError:
                pio.uart.print(f"Invalid duration: {door_cmd[5:]}")
                door_open()  # Use default duration
    else:
        pio.uart.print(f"Unknown command: {data}")


# Initialize LCD
lcd_init()
lcd_display("Systeme Pret", "")

# Main loop: receive commands from serial
print("[INFO] Proteus face recognition program started. Waiting for commands...")
pio.uart.print("System ready, waiting for commands...")

# Buffer for incomplete messages
buffer = ""

while True:
    try:
        # Update motor state machine (non-blocking)
        update_motor_state()
        
        # Receive data from serial (from Python script on PC)
        data = pio.uart.recv()
        if data:
            # Convert to string if needed
            if isinstance(data, bytes):
                try:
                    data_str = data.decode('utf-8')
                except:
                    data_str = str(data)
            else:
                data_str = str(data)
            
            # Accumulate data in buffer (handle partial messages)
            buffer += data_str
            
            # Process complete lines (ending with \n)
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if line:
                    parse_command(line)
    except Exception as e:
        pio.uart.print(f"Error: {e}")
        import traceback
        pio.uart.print(traceback.format_exc())
    time.sleep(0.01)  # Small delay

