import RPi.GPIO as GPIO
import time
import subprocess
import sys
import signal

HOOK_PIN = 17             # GPIO pin connected to OUT (or whichever pin you used)
AUDIO_FILE = "/home/baps/FamilyUnity.mp3"
PRESSED_STATE = 1         # Set to 1 if GPIO reads HIGH when the handset is lifted.
                          # Set to 0 if GPIO reads LOW when the handset is lifted.

DEBOUNCE_SEC = 0.05       # debounce interval

GPIO.setmode(GPIO.BCM)
# Use internal pull-down by default (change if you used pull-up wiring)
GPIO.setup(HOOK_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

player = None
last_time = 0
state = GPIO.input(HOOK_PIN)  # initial reading

def play_audio():
    global player
    if player is None:
        print("▶️ Playing audio...")
        player = subprocess.Popen(["mpg123", "-q", AUDIO_FILE])

def stop_audio():
    global player
    if player:
        print("⏹️ Stopping audio...")
        try:
            player.terminate()
            player.wait(timeout=1)
        except Exception:
            try:
                player.kill()
            except Exception:
                pass
        player = None

def cleanup_and_exit(signum=None, frame=None):
    stop_audio()
    GPIO.cleanup()
    print("Exiting.")
    sys.exit(0)

# Graceful exit on Ctrl+C
signal.signal(signal.SIGINT, cleanup_and_exit)
signal.signal(signal.SIGTERM, cleanup_and_exit)

print("Monitoring telephone hook switch on GPIO", HOOK_PIN)
print("PRESSED_STATE =", PRESSED_STATE)
print("Initial GPIO value:", state)
print("Flip PRESSED_STATE to invert behavior if needed.")

try:
    while True:
        new_state = GPIO.input(HOOK_PIN)
        now = time.time()

        # show raw value for quick debugging (only on change)
        if new_state != state:
            print("Raw GPIO changed ->", new_state)

        # Debounce: require some time since last change
        if new_state != state and (now - last_time) > DEBOUNCE_SEC:
            last_time = now
            state = new_state

            if state == PRESSED_STATE:
                # Handset considered "pressed/lifted"
                print("Detected: HANDSET LIFTED (pressed)")
                play_audio()
            else:
                # Handset considered "released/down"
                print("Detected: HANDSET DOWN (released)")
                stop_audio()

        time.sleep(0.02)

except KeyboardInterrupt:
    cleanup_and_exit()
