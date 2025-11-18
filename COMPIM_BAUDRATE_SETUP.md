# COMPIM Baudrate Configuration

## Setting COMPIM Baudrate to 115200 in Proteus

To prevent data loss, the COMPIM component in Proteus must be configured to use **115200 baudrate** (instead of the default 9600).

### Steps to Change COMPIM Baudrate:

1. **Open your Proteus project** (`Face_detection_simulation.pdsprj`)

2. **Locate the COMPIM component** in your circuit

3. **Right-click on the COMPIM component** → Select **"Edit Properties"** (or double-click the component)

4. **In the Properties dialog:**
   - Find the **"Baudrate"** field
   - Change it from `9600` to `115200`
   - Make sure the **"Physical Port"** matches your VSPE port (e.g., COM1 or COM2)
   - Click **"OK"** to save

5. **Also configure Raspberry Pi UART:**
   - Right-click on **Raspberry Pi 3** component → Edit Properties
   - Set **UART Baudrate** to `115200`
   - Set **UART Port** to match your VSPE port (e.g., COM1)

6. **Save your Proteus project** (File → Save)

### Verification:

- Both COMPIM and Raspberry Pi UART should be set to **115200**
- The Python script (`recognize_and_control_proteus.py`) now defaults to 115200
- All baudrates must match: COMPIM = Raspberry Pi UART = Python script = **115200**

### Why 115200?

Higher baudrate (115200 vs 9600) allows:
- Faster data transmission
- Reduced data loss during high-frequency communication
- Better performance with real-time face recognition commands

### Troubleshooting:

If you still experience data loss:
- Verify all three components use the same baudrate (115200)
- Check VSPE virtual ports are properly connected
- Ensure you're using the correct COM port (opposite of what Proteus uses)
- Try restarting VSPE and Proteus simulation

