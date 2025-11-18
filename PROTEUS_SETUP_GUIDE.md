# Proteus Setup Guide for Face Recognition Access Control

This guide explains how to run the face recognition access control system with Proteus VSM simulation.

## Overview

The system consists of two parts:
1. **Python script on your PC** (`recognize_and_control_proteus.py`) - Runs face recognition and sends commands via serial
2. **Proteus VSM program** (`Proteus_program_face_recognition.py`) - Runs inside Proteus, receives commands, and controls LCD + motor

## Prerequisites

1. **Proteus VSM** (with Raspberry Pi 3 model support)
2. **Python 3** with required libraries:
   - `opencv-contrib-python` (for face recognition)
   - `pyserial` (for serial communication)
3. **VSPE (Virtual Serial Port Emulator)** - To create a virtual COM port pair for communication

## Step 1: Install Python Dependencies

```bash
pip install opencv-contrib-python pyserial
```

## Step 2: Set Up Virtual Serial Port (VSPE)

1. **Extract and install VSPE** from `SetupVSPE.zip`
2. **Create a virtual COM port pair:**
   - Open VSPE
   - Click "Create new device" → "Connector"
   - Create two ports (e.g., COM1 ↔ COM2)
   - Note which ports you're using (e.g., COM1 and COM2)

## Step 3: Prepare Face Recognition Model

Before running with Proteus, you need to train the face recognition model:

```bash
# 1. Capture face dataset
python capture_dataset.py --username alice --num-images 80
python capture_dataset.py --username bob --num-images 80

# 2. Train the model
python train_model.py
```

This creates `trainer.yml` and `labels.json` files.

## Step 4: Set Up Proteus Circuit

### Circuit Components Needed:
- **Raspberry Pi 3** (from Proteus library)
- **16x2 LCD** (parallel interface)
- **DC Motor** (or motor symbol)
- **Motor Driver** (L293D or transistor/relay circuit)
- **Resistors** (for pull-ups if needed)

### Pin Connections (BOARD mode):

**LCD Connections:**
- LCD RS → Raspberry Pi GPIO 15 (Physical pin 10)
- LCD E → Raspberry Pi GPIO 16 (Physical pin 36)
- LCD D4 → Raspberry Pi GPIO 7 (Physical pin 26)
- LCD D5 → Raspberry Pi GPIO 11 (Physical pin 23)
- LCD D6 → Raspberry Pi GPIO 12 (Physical pin 32)
- LCD D7 → Raspberry Pi GPIO 13 (Physical pin 33)
- LCD VSS, VDD, V0, A, K → Power/Ground as per LCD datasheet

**Motor Connections:**
- Motor Driver Input 1 → Raspberry Pi GPIO 29 (Physical pin 40)
- Motor Driver Input 2 → Raspberry Pi GPIO 31 (Physical pin 46)
- Motor Driver → DC Motor
- Power supply for motor (separate from Pi 5V)

**Serial/UART:**
- Raspberry Pi UART TX → Connect to virtual serial port (handled by Proteus VSM)

### Example Proteus Circuit Layout:

```
Raspberry Pi 3
    |
    ├─ GPIO 15 → LCD RS
    ├─ GPIO 16 → LCD E
    ├─ GPIO 7  → LCD D4
    ├─ GPIO 11 → LCD D5
    ├─ GPIO 12 → LCD D6
    ├─ GPIO 13 → LCD D7
    ├─ GPIO 29 → Motor Driver IN1
    ├─ GPIO 31 → Motor Driver IN2
    └─ UART    → Virtual Serial Port (COM1/COM2)
```

## Step 5: Configure Proteus VSM

1. **Open your Proteus project** (`Face_detection_simulation.pdsprj`)

2. **Set up Raspberry Pi 3:**
   - Place Raspberry Pi 3 component
   - Right-click → Edit Properties
   - Set **Program File** to: `Proteus_program_face_recognition.py`
   - Set **VSM Python** interpreter path (usually auto-detected)

3. **Configure Serial Port:**
   - In Raspberry Pi properties, set UART to use one of your VSPE ports (e.g., COM1)
   - Make sure the baudrate is 9600

4. **Connect all components** as described in Step 4

## Step 6: Run the System

### Terminal 1: Start Proteus Simulation
1. Open Proteus
2. Load your circuit
3. Click **Play** (▶) to start simulation
4. The Proteus program will start and wait for serial commands

### Terminal 2: Run Face Recognition Script
```bash
# Use the OTHER VSPE port (e.g., if Proteus uses COM1, use COM2)
python recognize_and_control_proteus.py --proteus-port COM2 --camera-index 0
```

**Note:** Make sure to use the **opposite** COM port from what Proteus is using!

## Step 7: Test the System

1. **Camera should open** showing video feed
2. **When a recognized face appears:**
   - LCD in Proteus should show: "Bienvenue" on line 1, username on line 2
   - Motor should activate (rotate) for 5 seconds
   - Green box around face in video

3. **When an unknown face appears:**
   - LCD should show: "Acces refuse"
   - Motor should remain OFF
   - Red box around face in video

## Troubleshooting

### Issue: "Cannot connect to Proteus on COMx"
- **Solution:** Check VSPE is running and ports are connected
- Verify you're using the correct COM port (opposite of Proteus)
- Try different COM port numbers

### Issue: "Model not found: trainer.yml"
- **Solution:** Run `train_model.py` first to create the model

### Issue: LCD not displaying in Proteus
- **Solution:** 
  - Check pin connections match the code (BOARD mode)
  - Verify LCD power connections (VSS, VDD, V0)
  - Check Proteus simulation is running

### Issue: Motor not rotating
- **Solution:**
  - Verify motor driver connections
  - Check motor power supply is connected
  - Verify GPIO 29 and 31 are connected correctly

### Issue: No face detection
- **Solution:**
  - Check camera is working: `python capture_dataset.py --username test`
  - Verify Haar cascade file exists
  - Adjust lighting conditions

## Command Reference

### Serial Commands Sent to Proteus:

| Command | Description |
|---------|-------------|
| `INIT:message` | Initialize LCD with message |
| `LCD:line1\|line2` | Display two lines on LCD |
| `LCD:CLEAR` | Clear LCD display |
| `DOOR:OPEN:5.0` | Open door for 5 seconds |
| `DOOR:CLOSE` | Close door (stop motor) |

### Python Script Options:

```bash
python recognize_and_control_proteus.py \
    --camera-index 0 \
    --proteus-port COM2 \
    --baudrate 9600
```

## Alternative: Using Real Hardware

If you want to use real Raspberry Pi hardware instead of Proteus:

1. Use `recognize_and_control.py` (not the Proteus version)
2. Connect real LCD and motor to Raspberry Pi
3. Run directly on the Pi (no serial communication needed)

## Pin Mapping Reference

### BOARD Mode (Physical Pin Numbers):
- GPIO 7  = Physical Pin 26
- GPIO 11 = Physical Pin 23
- GPIO 12 = Physical Pin 32
- GPIO 13 = Physical Pin 33
- GPIO 15 = Physical Pin 10
- GPIO 16 = Physical Pin 36
- GPIO 29 = Physical Pin 40
- GPIO 31 = Physical Pin 46

### BCM Mode (GPIO Numbers):
- GPIO 7  = BCM GPIO 4
- GPIO 11 = BCM GPIO 17
- GPIO 12 = BCM GPIO 18
- GPIO 13 = BCM GPIO 27
- GPIO 15 = BCM GPIO 22
- GPIO 16 = BCM GPIO 23
- GPIO 29 = BCM GPIO 5
- GPIO 31 = BCM GPIO 6

## Next Steps

1. Test with multiple users
2. Adjust `CONFIDENCE_THRESHOLD` in `recognize_and_control_proteus.py` for better accuracy
3. Modify door open duration as needed
4. Add more users to the dataset

