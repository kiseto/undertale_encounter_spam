import time
import threading
import subprocess
from pynput import keyboard

# controls
TOGGLE_KEY = keyboard.Key.f8
FASTER_KEY = keyboard.Key.f6
SLOWER_KEY = keyboard.Key.f7
QUIT_KEY = keyboard.Key.f10

# movement tuning
HOLD_TIME = 0.045
GAP_TIME = 0.005

MIN_HOLD = 0.015
MAX_HOLD = 0.120

# debug
DEBUG = True
PRINT_EVERY_N_TAPS = 10

running = True
up_down_spam = False
tap_count = 0

undertale_active_window_id = None
undertale_input_window_id = None

lock = threading.Lock()
controller = keyboard.Controller()


def log(msg):
    if DEBUG:
        print(msg, flush=True)


def run_xdotool(args, timeout=0.5):
    return subprocess.run(
        ["xdotool"] + args,
        capture_output=True,
        text=True,
        timeout=timeout
    )


def get_window_name(window_id):
    if not window_id:
        return ""

    try:
        result = run_xdotool(["getwindowname", window_id])
        return result.stdout.strip()
    except Exception:
        return ""


def get_active_window_id():
    try:
        result = run_xdotool(["getactivewindow"])
        return result.stdout.strip()
    except Exception:
        return ""


def get_focus_window_id():
    try:
        result = run_xdotool(["getwindowfocus"])
        return result.stdout.strip()
    except Exception:
        return ""


def looks_like_undertale_window(window_name):
    lowered = window_name.lower()

    if "undertale" not in lowered:
        return False

    blocked_words = [
        "visual studio code",
        "vscode",
        "terminal",
        "bash",
        "python",
        "undertale_enc_spam",
        "repos",
    ]

    return not any(word in lowered for word in blocked_words)


def capture_undertale_windows():
    """
    focus undertale first, then press f8.
    active window = used to know if undertale is currently focused
    focus window = used for xdotool background input
    """
    active_id = get_active_window_id()
    active_name = get_window_name(active_id)

    focus_id = get_focus_window_id()
    focus_name = get_window_name(focus_id)

    log(f"[ACTIVE] {active_name} ({active_id})")
    log(f"[FOCUS] {focus_name} ({focus_id})")

    if not looks_like_undertale_window(active_name):
        log("[ERROR] undertale does not look focused.")
        log("[TIP] click/focus undertale first, then press f8 again.")
        return None, None

    input_id = focus_id if focus_id else active_id

    log(f"[TARGET] active window id: {active_id}")
    log(f"[TARGET] input window id: {input_id}")

    return active_id, input_id


def is_undertale_focused():
    if not undertale_active_window_id:
        return False

    return get_active_window_id() == undertale_active_window_id


def send_key_foreground(key):
    """
    used when undertale is focused.
    normal pynput input works better here.
    """
    opposite = keyboard.Key.down if key == keyboard.Key.up else keyboard.Key.up

    controller.release(opposite)
    controller.press(key)
    time.sleep(HOLD_TIME)
    controller.release(key)
    time.sleep(GAP_TIME)


def send_key_background(window_id, key_name):
    """
    used when undertale is not focused.
    xdotool --window works better in your setup after alt-tab.
    """
    opposite = "Down" if key_name == "Up" else "Up"

    try:
        run_xdotool(["keyup", "--window", window_id, opposite])
        run_xdotool(["keydown", "--window", window_id, key_name])
        time.sleep(HOLD_TIME)
        run_xdotool(["keyup", "--window", window_id, key_name])
        time.sleep(GAP_TIME)
        return True
    except Exception as e:
        log(f"[ERROR] failed sending {key_name}: {e}")
        return False


def release_movement_keys():
    controller.release(keyboard.Key.up)
    controller.release(keyboard.Key.down)

    if undertale_input_window_id:
        try:
            run_xdotool(["keyup", "--window", undertale_input_window_id, "Up"])
            run_xdotool(["keyup", "--window", undertale_input_window_id, "Down"])
        except Exception:
            pass


def on_press(key):
    global up_down_spam, running, HOLD_TIME
    global undertale_active_window_id, undertale_input_window_id

    with lock:
        if key == TOGGLE_KEY:
            if not up_down_spam:
                active_id, input_id = capture_undertale_windows()

                if not active_id or not input_id:
                    up_down_spam = False
                    log("[TOGGLE] hybrid background up/down spam: off")
                    return

                undertale_active_window_id = active_id
                undertale_input_window_id = input_id
                up_down_spam = True

                log("[TOGGLE] hybrid background up/down spam: on")
                log("[INFO] works focused, and should continue after alt-tab.")
            else:
                up_down_spam = False
                release_movement_keys()
                log("[TOGGLE] hybrid background up/down spam: off")

        elif key == FASTER_KEY:
            HOLD_TIME = max(MIN_HOLD, HOLD_TIME - 0.005)
            log(f"[SPEED] faster. HOLD_TIME = {HOLD_TIME:.3f}s")

        elif key == SLOWER_KEY:
            HOLD_TIME = min(MAX_HOLD, HOLD_TIME + 0.005)
            log(f"[SPEED] slower. HOLD_TIME = {HOLD_TIME:.3f}s")

        elif key == QUIT_KEY:
            running = False
            up_down_spam = False
            release_movement_keys()
            log("[QUIT] exiting.")
            return False


def spam_loop():
    global tap_count, up_down_spam

    direction = "Up"

    while running:
        with lock:
            active = up_down_spam
            input_id = undertale_input_window_id

        if active and input_id:
            focused = is_undertale_focused()

            if focused:
                if direction == "Up":
                    send_key_foreground(keyboard.Key.up)
                else:
                    send_key_foreground(keyboard.Key.down)

                mode = "foreground"
                success = True
            else:
                success = send_key_background(input_id, direction)
                mode = "background"

            if not success:
                log("[WARN] could not send input. turning spam off.")
                with lock:
                    up_down_spam = False
                continue

            tap_count += 1

            if tap_count % PRINT_EVERY_N_TAPS == 0:
                log(f"[TAP {tap_count}] sent {direction} via {mode} | HOLD_TIME={HOLD_TIME:.3f}s")

            direction = "Down" if direction == "Up" else "Up"
        else:
            time.sleep(0.01)


print("undertale hybrid background encounter spam helper running.", flush=True)
print("important: focus undertale first, then press f8.", flush=True)
print("f8 = toggle hybrid up/down spam", flush=True)
print("f6 = faster", flush=True)
print("f7 = slower", flush=True)
print("f10 = quit", flush=True)
print(f"starting HOLD_TIME = {HOLD_TIME:.3f}s", flush=True)

threading.Thread(target=spam_loop, daemon=True).start()

with keyboard.Listener(on_press=on_press) as listener:
    listener.join()