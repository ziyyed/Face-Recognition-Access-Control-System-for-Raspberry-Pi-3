# 🎯 Action Plan: Getting Started with Face Recognition on Proteus

## Current Status
✅ All Python scripts are ready  
❌ Face dataset not captured yet  
❌ Model not trained yet  
❌ Proteus setup pending  

---

## 📋 Step-by-Step Action Plan

### **STEP 1: Test Your Camera** (2 minutes)
First, make sure your camera works:

```bash
python capture_dataset.py --username test --num-images 5
```

**Expected:** Camera window opens, captures 5 face images, saves to `dataset/test/`

**If it fails:** Check camera permissions or try `--camera-index 1` instead of 0

---

### **STEP 2: Capture Face Dataset** (10-15 minutes per person)

For each person you want to recognize:

```bash
# Example: Capture 80 images for user "alice"
python capture_dataset.py --username alice --num-images 80

# Then for another user
python capture_dataset.py --username bob --num-images 80
```

**Tips:**
- Move your face around (left, right, up, down)
- Vary lighting if possible
- Keep face clearly visible
- Press 'q' to stop early if needed

**Result:** Creates `dataset/alice/`, `dataset/bob/`, etc. with face images

---

### **STEP 3: Train the Recognition Model** (1-2 minutes)

Once you have at least one user's dataset:

```bash
python train_model.py
```

**Expected Output:**
- Scans all folders in `dataset/`
- Trains LBPH recognizer
- Creates `trainer.yml` (model file)
- Creates `labels.json` (ID → username mapping)
- Shows: "Training complete. Model saved to trainer.yml"

---

### **STEP 4: Test Recognition (Without Proteus)** (Optional - 5 minutes)

Test if recognition works before setting up Proteus:

```bash
python recognize_and_control.py --mock-hardware
```

**Expected:**
- Camera opens
- Shows video with face detection
- Recognized faces show green box with name
- Unknown faces show red box
- Console shows "[LCD] Bienvenue alice" or "[LCD] Acces refuse"

Press 'q' to quit.

---

### **STEP 5: Set Up VSPE (Virtual Serial Port)** (5 minutes)

1. **Extract VSPE:**
   - Extract `SetupVSPE.zip`
   - Install VSPE

2. **Create Virtual Port Pair:**
   - Open VSPE application
   - Click "Create new device"
   - Select "Connector"
   - Set Port 1: **COM1**
   - Set Port 2: **COM2**
   - Click "Add"
   - Keep VSPE running (minimize it)

**Result:** COM1 and COM2 are now connected (data sent to one appears on the other)

---

### **STEP 6: Set Up Proteus Circuit** (15-20 minutes)

1. **Open Proteus:**
   - Open `Face_detection_simulation.pdsprj`

2. **Configure Raspberry Pi 3:**
   - Right-click Raspberry Pi 3 component
   - Edit Properties
   - **Program File:** Browse and select `Proteus_program_face_recognition.py`
   - **UART/Serial:** Set to **COM1** (or your VSPE port)
   - **Baudrate:** 9600

3. **Connect Components:**
   - Follow `PROTEUS_PIN_CONNECTIONS.txt` for wiring
   - LCD: Connect pins 15, 16, 7, 11, 12, 13
   - Motor: Connect pins 29, 31
   - Power: Connect 5V and GND

4. **Start Simulation:**
   - Click **Play** button (▶) in Proteus
   - LCD should show "Systeme Pret"
   - Simulation is now waiting for serial commands

---

### **STEP 7: Run Full System** (Testing)

1. **Keep Proteus running** (simulation active)

2. **Run Python Script:**
   ```bash
   python recognize_and_control_proteus.py --proteus-port COM2
   ```
   (Use COM2 if Proteus uses COM1, or vice versa)

3. **Test:**
   - Show your face to camera
   - If recognized: LCD shows "Bienvenue [username]", motor rotates
   - If unknown: LCD shows "Acces refuse", motor stays off

4. **Press 'q'** in camera window to stop

---

## 🐛 Troubleshooting Quick Fixes

| Problem | Quick Fix |
|---------|-----------|
| "Cannot open camera" | Try `--camera-index 1` |
| "Model not found" | Run `train_model.py` first |
| "Cannot connect to Proteus" | Check VSPE is running, use opposite COM port |
| "No face detected" | Improve lighting, move closer to camera |
| LCD not working in Proteus | Check pin connections, verify program file path |
| Motor not rotating | Check motor driver connections and power supply |

---

## ✅ Success Checklist

- [ ] Camera works (`capture_dataset.py` runs)
- [ ] At least one user dataset captured
- [ ] Model trained (`trainer.yml` exists)
- [ ] Recognition works in mock mode
- [ ] VSPE virtual ports created
- [ ] Proteus circuit configured
- [ ] Proteus simulation running
- [ ] Full system working (Python + Proteus)

---

## 🎓 Next Steps After Basic Setup

1. **Add more users** to improve system
2. **Adjust confidence threshold** in `recognize_and_control_proteus.py` (line 30)
3. **Modify door open duration** (line 32)
4. **Test with different lighting conditions**
5. **Add more training images** for better accuracy

---

## 📚 Reference Files

- `QUICK_START_PROTEUS.md` - Quick reference
- `PROTEUS_SETUP_GUIDE.md` - Detailed guide
- `PROTEUS_PIN_CONNECTIONS.txt` - Pin wiring reference

---

**Ready to start? Begin with STEP 1!** 🚀

