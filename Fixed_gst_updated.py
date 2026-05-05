import pygame  # Reads the gamepad
import serial  # Talks to the XBee radio
import time    # Handles delays and timing
import logging # Writes timestamped events to a log file

# --- SETTINGS ---
SERIAL_PORT    = 'COM8'  # USB port of the XBee radio
BAUD_RATE      = 115200          # Must match the rover's radio speed
DEADZONE       = 0.15            # Ignore stick movements below 15% (prevents drift)
UPDATE_RATE    = 0.05            # Loop runs 20 times per second
MAX_BASE_STEPS = 400             # Max arm base rotation per command

# Speed limiters — FULL=100%, MID=60%, LOW=30% of stick input
THROTTLE_SCALE = {"FULL": 1.0, "MID": 0.6, "LOW": 0.3}
THROTTLE_CYCLE = ["FULL", "MID", "LOW"]  # Y button cycles in this order

# Names used to recognise a supported gamepad
GAMEPAD_KEYWORDS = ["Xbox", "Controller", "SHANWAN", "Gamepad", "Microsoft"]

LOG_FILE = "gcs_events.log"   # Log file written next to the script


# --- LOGGING SETUP ---
# Writes timestamped connection/disconnection events to a log file.
# Format: 2025-06-01 14:32:05 | INFO | XBee connected on /dev/ttyUSB0
logging.basicConfig(
    filename=LOG_FILE,
    filemode='a',                          # Append so logs survive restarts
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO
)
log = logging.getLogger("GCS")
log.info("=" * 60)
log.info("Ground Station started")
print(f"📝 Logging events to: {LOG_FILE}")


# --- FUNCTIONS ---

def clean(v):
    # Return the value if above deadzone, else return 0 (no movement)
    val = float(v)
    return round(val, 2) if abs(val) > DEADZONE else 0.0


def find_joystick():
    # Re-scan USB devices and return the first matching gamepad, or None
    pygame.joystick.quit()
    pygame.joystick.init()
    for i in range(pygame.joystick.get_count()):
        j = pygame.joystick.Joystick(i)
        j.init()
        if any(k in j.get_name() for k in GAMEPAD_KEYWORDS):
            print(f"\n🎮 Controller Identified: {j.get_name()}")
            log.info(f"Controller connected: {j.get_name()}")
            return j
    return None  # Not found


def open_serial(port, baud):
    # Try to open the XBee serial port; return Serial object or None on failure
    try:
        s = serial.Serial(port, baud, timeout=0.01)
        s.reset_input_buffer()
        print(f"\n✅ XBee Serial Established on {port}")
        log.info(f"XBee connected on {port}")
        return s
    except Exception as e:
        return None   # Caller will retry in the main loop


def safe_serial_read(s):
    # Read incoming bytes from serial; returns "" if nothing to read,
    # None if the port suddenly died (so caller knows to reconnect)
    if s is None:
        return ""
    try:
        if s.in_waiting > 0:
            return s.read(s.in_waiting).decode('utf-8', errors='ignore')
        return ""
    except (serial.SerialException, OSError):
        return None  # Port was physically removed


def safe_serial_write(s, data):
    # Send bytes to serial; returns False if the port is gone (triggers reconnect)
    if s is None:
        return False
    try:
        s.write(data)
        return True
    except (serial.SerialException, OSError):
        return False  # Port was physically removed


# --- START-UP ---

pygame.init()
pygame.joystick.init()

# Try to open XBee at startup — unlike before, failure no longer exits.
# The main loop will keep retrying until the XBee is plugged in.
ser = open_serial(SERIAL_PORT, BAUD_RATE)
if not ser:
    print(f"⚠️  XBee not found on {SERIAL_PORT}. Waiting for connection...")

# Find gamepad at start (will keep retrying in the loop if not found)
joy = find_joystick()
if not joy:
    print("⚠️  Controller not found. Waiting for connection...")

# State variables
active_mode    = "DRIVE"  # DRIVE or ARM
throttle_mode  = "FULL"   # FULL, MID, or LOW
last_btn_a     = 0         # Previous A button state (for press detection)
last_btn_y     = 0         # Previous Y button state (for press detection)
last_heartbeat = 0         # Last time rover sent a heartbeat signal
connection_status = "🔴 DISCONNECTED"  # Rover RF link (heartbeat $H)
xbee_status    = "🔴 DISCONNECTED"    # Physical XBee USB port status
joy_status     = "🔴 DISCONNECTED"    # Physical controller USB status

print(f"\n📡 Rover-71 Ground Station | Status: READY")
print(f"   A = Drive/Arm toggle  |  Y = Cycle throttle (FULL→MID→LOW)")
print("-" * 90)


# --- MAIN LOOP (runs 20x per second until Ctrl+C) ---

try:
    while True:
        pygame.event.pump()  # Required every loop to process USB events

        # 1. XBEE USB CHECK
        # Try to (re)open the port every tick when it is absent.
        # xbee_status is updated here so the HUD always reflects reality.
        if ser is None:
            ser = open_serial(SERIAL_PORT, BAUD_RATE)
        xbee_status = "🟢 CONNECTED" if ser is not None else "🔴 DISCONNECTED"

        # 2. GAMEPAD USB CHECK
        # Try to (re)find the controller every tick when it is absent.
        if joy is None:
            joy = find_joystick()
        else:
            # If gamepad was unplugged mid-session, catch the error and reset
            try:
                _ = joy.get_axis(0)
            except pygame.error:
                log.warning("Controller disconnected (pygame error)")
                joy = None
        joy_status = "🟢 CONNECTED" if joy is not None else "🔴 DISCONNECTED"

        # 3. ROVER HEARTBEAT CHECK
        # Rover sends "$H" every second — if silent for 2s, mark RF link as down.
        # Only attempt read/write when XBee USB is actually present.
        payload = ""   # Empty payload shown in HUD when XBee is absent
        if ser is not None:
            incoming = safe_serial_read(ser)
            if incoming is None:
                # Port died mid-read — drop it; next tick will try to reopen
                log.warning(f"XBee disconnected (read error) on {SERIAL_PORT}")
                ser = None
                xbee_status = "🔴 DISCONNECTED"
            else:
                if "$H" in incoming:
                    last_heartbeat = time.time()

        new_status = "🟢 CONNECTED" if time.time() - last_heartbeat < 2.0 else "🔴 DISCONNECTED"
        # Log only when the rover RF link status actually changes (not every tick)
        if new_status != connection_status:
            if "CONNECTED" in new_status:
                log.info("Rover heartbeat link: CONNECTED")
            else:
                log.warning("Rover heartbeat link: DISCONNECTED (no $H for 2s)")
        connection_status = new_status

        # 4. BUTTON PRESSES  (skip if controller absent)
        if joy is not None:
            # A button — toggle Drive / Arm mode (triggers only on first press, not hold)
            btn_a = joy.get_button(0)
            if btn_a and not last_btn_a:
                active_mode = "ARM" if active_mode == "DRIVE" else "DRIVE"
                print(f"\n🔄 MODE CHANGE → {active_mode}")
            last_btn_a = btn_a

            # Y button — cycle throttle: FULL → MID → LOW → FULL ...
            btn_y = joy.get_button(3)
            if btn_y and not last_btn_y:
                throttle_mode = THROTTLE_CYCLE[(THROTTLE_CYCLE.index(throttle_mode) + 1) % 3]
                print(f"\n⚡ THROTTLE → {throttle_mode} ({int(THROTTLE_SCALE[throttle_mode]*100)}%)")
            last_btn_y = btn_y

            # 5. READ STICKS AND TRIGGERS
            # Left stick up/down → forward/reverse speed (scaled by throttle mode)
            lx = round(clean(-joy.get_axis(1)) * THROTTLE_SCALE[throttle_mode], 2)

            # Left stick left/right → steering (DRIVE) or arm base rotation (ARM)
            az = clean(joy.get_axis(0))

            # Right stick → arm shoulder (up/down) and elbow (left/right)
            rs_vert = clean(-joy.get_axis(4))
            rs_horz = clean( joy.get_axis(3))

            # Triggers → linear actuator (RT = extend, LT = retract)
            raw_lt = joy.get_axis(2)
            raw_rt = joy.get_axis(5)
            lt = (raw_lt + 1) / 2 if raw_lt != 0.0 else 0.0
            rt = (raw_rt + 1) / 2 if raw_rt != 0.0 else 0.0
            act2_val = clean(rt - lt)

            # Bumpers → gripper open (LB) / close (RB)
            btn_lb = joy.get_button(4)
            btn_rb = joy.get_button(5)

            # 6. ARM BASE ROTATION
            # Proportional to stick tilt; minus sign so left stick = rotate left
            base_step = int(-az * MAX_BASE_STEPS) if active_mode == "ARM" else 0

            # 7. BUILD AND SEND PAYLOAD  (only when both XBee and controller present)
            if ser is not None:
                if active_mode == "DRIVE":
                    payload = f"$D,{lx},{az},0.0,0.0,0.0,0,0,0\n"
                else:
                    payload = f"$A,0.0,0.0,{rs_vert},{act2_val},{rs_horz},{btn_lb},{btn_rb},{base_step}\n"

                # If write fails, port died mid-send — drop it; next tick reconnects
                if not safe_serial_write(ser, payload.encode()):
                    log.warning(f"XBee disconnected (write error) on {SERIAL_PORT}")
                    ser = None
                    xbee_status = "🔴 DISCONNECTED"
                    payload = ""

        # 8. HUD DISPLAY — always printed every tick so status is always visible
        grn  = "\033[92m"
        red  = "\033[91m"
        reset = "\033[0m"
        mode_clr  = "\033[96m" if active_mode == "DRIVE" else "\033[95m"
        thr_clr   = {"FULL": grn, "MID": "\033[93m", "LOW": red}[throttle_mode]
        xbee_clr  = grn if "CONNECTED" in xbee_status  else red
        joy_clr   = grn if "CONNECTED" in joy_status   else red
        rover_clr = grn if "CONNECTED" in connection_status else red

        hud = (f"XBEE: {xbee_clr}{xbee_status:13}{reset} | "
               f"PAD: {joy_clr}{joy_status:13}{reset} | "
               f"ROVER: {rover_clr}{connection_status:13}{reset} | "
               f"MODE: {mode_clr}{active_mode:5}{reset} | "
               f"THR: {thr_clr}{throttle_mode:4}{reset} ({int(THROTTLE_SCALE[throttle_mode]*100):3}%) | "
               f"PKT: {payload.strip()}")
        print(hud, end='\r')

        time.sleep(UPDATE_RATE)

except KeyboardInterrupt:
    print("\n🛑 Closing Ground Station...")
    log.info("Ground Station shut down by user (Ctrl+C)")
finally:
    if ser: ser.close()
    pygame.quit()