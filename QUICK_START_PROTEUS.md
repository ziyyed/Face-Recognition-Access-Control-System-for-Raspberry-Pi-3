# Quick Start: Running Face Recognition on Proteus

## 🚀 Fast Setup (5 Steps)

### Step 1: Install Dependencies
```bash
pip install opencv-contrib-python pyserial
```

### Step 2: Train Face Model
```bash
# Capture faces for each user
python capture_dataset.py --username alice --num-images 80
python train_model.py
```

### Step 3: Set Up VSPE
1. Extract and run `SetupVSPE.zip`
2. Create a **Connector** device
3. Connect COM1 ↔ COM2 (or any two ports)
4. Keep VSPE running

### Step 4: Configure Proteus
1. Open `Face_detection_simulation.pdsprj`
2. Set Raspberry Pi 3 **Program File** to: `Proteus_program_face_recognition.py`
3. Set Raspberry Pi **UART** to: COM1 (or your VSPE port)
4. Connect LCD and Motor as per `PROTEUS_PIN_CONNECTIONS.txt`
5. Click **Play** (▶) to start simulation

### Step 5: Run Python Script
```bash
# Use the OTHER VSPE port (if Proteus uses COM1, use COM2)
python recognize_and_control_proteus.py --proteus-port COM2
```

## ✅ Expected Behavior

- **Recognized Face:** LCD shows "Bienvenue" + username, motor rotates for 5 seconds
- **Unknown Face:** LCD shows "Acces refuse", motor stays OFF

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| "Cannot connect to Proteus" | Check VSPE ports are connected, use opposite port |
| "Model not found" | Run `train_model.py` first |
| LCD not working | Check pin connections in Proteus |
| Motor not rotating | Verify motor driver connections and power |

## 📁 Files Overview

- `recognize_and_control_proteus.py` - Main script (runs on PC, sends commands to Proteus)
- `Proteus_program_face_recognition.py` - Proteus VSM program (runs inside Proteus)
- `PROTEUS_SETUP_GUIDE.md` - Detailed setup instructions
- `PROTEUS_PIN_CONNECTIONS.txt` - Pin wiring reference

## 💡 Tips

- Use **BOARD mode** pin numbers (physical pins) in Proteus
- Make sure VSPE is running before starting Proteus
- Test camera first: `python capture_dataset.py --username test`
- Adjust `CONFIDENCE_THRESHOLD` in script if recognition is too strict/loose

