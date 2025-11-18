# Face Recognition Access Control System

A Raspberry Pi 3-based face recognition access control system with LCD display and door motor control. The system uses OpenCV's LBPH face recognizer to identify authorized users and controls hardware via GPIO.

## Features

- **Face Recognition**: Uses LBPH (Local Binary Patterns Histograms) face recognizer
- **Access Control**: Grants or denies access based on face recognition
- **LCD Display**: Shows welcome messages or access denied on 16x2 LCD
- **Motor Control**: Controls door motor for authorized users
- **Proteus Simulation**: Full hardware simulation support via Proteus VSM

## Hardware Requirements

- Raspberry Pi 3
- USB Camera or Pi Camera
- 16x2 LCD (parallel interface)
- DC Motor with driver (L293D or transistor/relay)
- Motor driver circuit

## Software Requirements

- Python 3.9+
- OpenCV (opencv-contrib-python)
- RPi.GPIO (for real hardware)
- pyserial (for Proteus communication)

## Installation

```bash
# Install dependencies
pip install opencv-contrib-python pyserial

# For Raspberry Pi hardware
pip install RPi.GPIO RPLCD
```

## Usage

### 1. Capture Face Dataset

```bash
python capture_dataset.py --username alice --num-images 80
```

### 2. Train the Model

```bash
python train_model.py
```

This creates `trainer.yml` and `labels.json`.

### 3. Run Recognition System

**For real hardware:**
```bash
python recognize_and_control.py
```

**For Proteus simulation:**
```bash
python recognize_and_control_proteus.py --proteus-port COM2
```

**For testing without hardware:**
```bash
python recognize_and_control.py --mock-hardware
```

## Project Structure

```
Face_Detection_System/
├── capture_dataset.py          # Capture face images for training
├── train_model.py              # Train LBPH face recognizer
├── recognize_and_control.py    # Main recognition script (real hardware)
├── recognize_and_control_proteus.py  # Recognition script (Proteus)
├── Proteus_program_face_recognition.py  # Proteus VSM program
├── lcd_display.py              # LCD control module
├── door_control.py             # Motor/door control module
├── dataset/                    # Face image dataset
│   ├── user1/
│   └── user2/
├── trainer.yml                 # Trained model
├── labels.json                 # User ID to name mapping
└── README.md
```

## Pin Configuration (BOARD Mode)

- **LCD**: RS=7, E=11, D4=12, D5=13, D6=15, D7=16
- **Motor**: Motor_1=29, Motor_2=31

## Proteus Setup

See `PROTEUS_SETUP_GUIDE.md` for detailed Proteus VSM setup instructions.

## License

This project is for educational purposes.

## Author

Face Recognition Access Control System - Raspberry Pi 3 Project

