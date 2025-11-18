# Troubleshooting: LCD Stuck at "Systeme Pret"

If your LCD display is stuck showing "Systeme Pret" and not responding to face recognition commands, follow these steps:

## Quick Checks

### 1. Verify Serial Communication is Working

**Check Python Script Output:**
- When you run `recognize_and_control_proteus.py`, you should see:
  ```
  [INFO] Connected to Proteus on COMx @ 115200 baud
  [DEBUG] Sending initialization command...
  [DEBUG] Initialization command sent
  ```
- If you see connection errors, the serial port is not working.

**Check Proteus Console:**
- In Proteus, look at the console output (usually at the bottom)
- You should see:
  ```
  [INFO] Proteus face recognition program started. Waiting for commands...
  [DEBUG] UART initialized, ready to receive data...
  ```
- If you see `[DEBUG] Received:` messages, data is being received.

### 2. Verify Baudrate Settings Match

**All three must be 115200:**
1. **Python script:** Default is now 115200 (or use `--baudrate 115200`)
2. **Raspberry Pi UART in Proteus:** Right-click Raspberry Pi → Properties → UART Baudrate = 115200
3. **COMPIM component (if used):** Right-click COMPIM → Properties → Baudrate = 115200

**To verify:**
```bash
# Check Python script is using 115200
python recognize_and_control_proteus.py --proteus-port COM2 --baudrate 115200
```

### 3. Verify COM Port Configuration

**VSPE Setup:**
- Make sure VSPE is running
- Verify the virtual port pair is connected (e.g., COM1 ↔ COM2)
- Proteus should use one port (e.g., COM1)
- Python script should use the OTHER port (e.g., COM2)

**Common Mistake:** Using the same COM port for both Proteus and Python script!

### 4. Test Serial Communication

**Simple Test:**
1. Start Proteus simulation
2. In Proteus console, you should see the program started message
3. Run Python script - you should see connection message
4. Check if Proteus console shows `[DEBUG] Received:` messages

**If no data is received:**
- Check VSPE ports are actually connected
- Try swapping COM ports (if Proteus uses COM1, try COM2 in Python script)
- Restart VSPE and Proteus

### 5. Check Command Format

The Python script sends commands like:
- `I:Systeme Pret` (initialization)
- `L:Bienvenue|username` (LCD display)
- `D:O:5.0` (door open)

The Proteus program should parse these. Check Proteus console for:
- `[DEBUG] Received:` - shows raw data received
- `[DEBUG] Processing command:` - shows parsed command

### 6. Common Issues and Solutions

| Problem | Solution |
|---------|----------|
| "Cannot connect to Proteus" | Check VSPE is running, verify COM port |
| No debug messages in Proteus | UART not configured correctly in Proteus |
| Python connects but no data received | Baudrate mismatch - verify all are 115200 |
| Proteus receives but LCD doesn't update | Check LCD pin connections in Proteus |
| LCD shows "Systeme Pret" but nothing else | Commands not being sent or received properly |

### 7. Debug Steps

**Step 1: Verify Python Script Can Send**
```bash
python recognize_and_control_proteus.py --proteus-port COM2 --baudrate 115200
```
- Should show connection successful
- Should show debug messages about sending commands

**Step 2: Check Proteus Console**
- Look for `[DEBUG] Received:` messages
- If you see these, data is arriving
- If not, serial communication is broken

**Step 3: Test with Simple Command**
You can manually test by sending a command. The Proteus program should respond to:
- `I:Test Message` - Should update LCD to "Test Message"
- `L:Line1|Line2` - Should show two lines on LCD

**Step 4: Verify Face Recognition is Working**
- Check if camera opens
- Check if faces are detected (green/red boxes)
- Check console for `[ACCESS]` messages
- If faces are detected but LCD doesn't update, it's a serial communication issue

### 8. Reset and Restart

If nothing works:
1. **Stop Proteus simulation**
2. **Close Python script**
3. **Restart VSPE** (disconnect and reconnect ports)
4. **Restart Proteus simulation**
5. **Run Python script again**

### 9. Check Proteus UART Configuration

In Proteus:
1. Right-click **Raspberry Pi 3** component
2. Edit Properties
3. Verify:
   - **UART Port:** COM1 (or your VSPE port)
   - **UART Baudrate:** 115200
   - **Program File:** Points to `Proteus_program_face_recognition.py`

### 10. Verify Proteus Program is Running

Check Proteus console for:
```
[INFO] Proteus face recognition program started. Waiting for commands...
[DEBUG] UART initialized, ready to receive data...
```

If you don't see these messages:
- Program file path might be wrong
- Python interpreter might not be configured
- Check Proteus simulation is actually running (Play button is active)

## Still Stuck?

1. **Check all baudrates are 115200** (most common issue)
2. **Verify VSPE ports are connected**
3. **Check Proteus console for error messages**
4. **Try a different COM port pair**
5. **Restart everything** (VSPE, Proteus, Python script)

The debug messages added to both scripts should help identify where the communication is breaking down.

