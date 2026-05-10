import time
import threading
import board
import busio
import RPi.GPIO as GPIO
from adafruit_mcp230xx.mcp23017 import MCP23017
 
# ── GPIO setup ────────────────────────────────────────────────────────────────
GPIO.setmode(GPIO.BCM)
 
# Per-key cancel events: if run_motor is called for a key that is already
# buzzing, the old thread sees its event set and exits early.
_cancel_events: dict[str, threading.Event] = {}
_cancel_lock = threading.Lock()
 
# ── Software PWM (MCP pins) ───────────────────────────────────────────────────
def _software_pwm(pin, duty_cycle, period=0.02, duration=2,
                  cancel: threading.Event = None):
    """
    Bit-bang PWM for MCP23017 outputs.
    Checks `cancel` between half-cycles so the thread can exit early.
    """
    on_time  = period * duty_cycle
    off_time = period * (1 - duty_cycle)
    end_time = time.time() + duration
    while time.time() < end_time:
        if cancel and cancel.is_set():
            break
        pin.value = True
        time.sleep(on_time)
        if cancel and cancel.is_set():
            break
        pin.value = False
        time.sleep(off_time)
    pin.value = False   # always leave pin low when done
 
# ── I2C + MCP chips ───────────────────────────────────────────────────────────
i2c  = busio.I2C(board.SCL, board.SDA)
mcp1 = MCP23017(i2c, address=0x20)
mcp2 = MCP23017(i2c, address=0x21)
 
# ── MCP1 pins (A–P= motors 1–16) ────────────────────────────────────────────
motor1  = mcp1.get_pin(0)   # GPA0
motor2  = mcp1.get_pin(1)   # GPA1
motor3  = mcp1.get_pin(2)   # GPA2
motor4  = mcp1.get_pin(3)   # GPA3
motor5  = mcp1.get_pin(4)   # GPA4
motor6  = mcp1.get_pin(5)   # GPA5
motor7  = mcp1.get_pin(6)   # GPA6
motor8  = mcp1.get_pin(7)   # GPA7

motor9  = mcp1.get_pin(8)   # GPB0
motor10 = mcp1.get_pin(9)   # GPB1
motor11  = mcp1.get_pin(10)   # GPB2
motor12  = mcp1.get_pin(11)   # GPB3
motor13  = mcp1.get_pin(12)   # GPB4
motor14  = mcp1.get_pin(13)   # GPB5
motor15  = mcp1.get_pin(14)   # GPB6
motor16  = mcp1.get_pin(15)   # GPB7

 
# ── MCP2 pins (Q–Z . ; = motors 17–32) ───────────────────────────────────────────
motor17  = mcp1.get_pin(0)   # GPA0
motor18  = mcp1.get_pin(1)   # GPA1
motor19  = mcp1.get_pin(2)   # GPA2
motor20  = mcp1.get_pin(3)   # GPA3
motor21  = mcp1.get_pin(4)   # GPA4
motor22  = mcp1.get_pin(5)   # GPA5
motor23  = mcp1.get_pin(6)   # GPA6
motor24  = mcp1.get_pin(7)   # GPA7

motor25  = mcp1.get_pin(8)   # GPB0
motor26 = mcp1.get_pin(9)   # GPB1
motor27  = mcp1.get_pin(10)   # GPB2
motor28  = mcp1.get_pin(11)   # GPB3
#motor29  = mcp1.get_pin(12)   # GPB4
#motor30  = mcp1.get_pin(13)   # GPB5
#motor31  = mcp1.get_pin(14)   # GPB6
#motor32  = mcp1.get_pin(15)   # GPB7
# motor27/28 on mcp2.get_pin(12/13) are available but exceed A–Z
 
# ── Initialise all MCP pins as outputs ───────────────────────────────────────
for _m in [motor1,  motor2,  motor3,  motor4,  motor5,  motor6,  motor7,
           motor8,  motor9,  motor10, motor11, motor12, motor13, motor14,
           motor15, motor16, motor17, motor18, motor19, motor20, motor21,
           motor22, motor23, motor24, motor25, motor26, motor27, motor28]:
    _m.switch_to_output(value=False)
 

# ── GPIO hardware PWM pins ────────────────────────────────────────────────────
# Key map (BCM numbers):
#   '0'=GPIO4   '1'=GPIO5   '2'=GPIO6   '3'=GPIO12  '4'=GPIO13
#   '5'=GPIO16  '6'=GPIO17  '7'=GPIO18  '8'=GPIO19  '9'=GPIO20
#   '!'=GPIO21  '@'=GPIO22  '#'=GPIO23  '$'=GPIO24  '%'=GPIO25
#   '^'=GPIO26  '&'=GPIO27
GPIO_PIN_MAP = {
    '0': 4,   '1': 5,   '2': 6,   '3': 12,  '4': 13,
    '5': 16,  '6': 17,  '7': 18,  '8': 19,  '9': 20,
    '!': 21,  '@': 22,  '#': 23,  '$': 24,  '%': 25,
    '^': 26,  '&': 27,
}
 
gpio_pwm = {}
for _key, _bcm in GPIO_PIN_MAP.items():
    GPIO.setup(_bcm, GPIO.OUT)
    _pwm = GPIO.PWM(_bcm, 1000)
    _pwm.start(0)
    gpio_pwm[_key] = _pwm
 
# ── Letter → motor dictionary ─────────────────────────────────────────────────
# Value: (pin_or_pwm, is_gpio)
MOTORS = {
    # MCP motors  A–Z , .
    'X': (motor1,  False),  'F': (motor2,  False),  'C': (motor3,  False),
    'Q': (motor4,  False),  'A': (motor5,  False),  'S': (motor6,  False),
    'W': (motor7,  False),  'D': (motor8,  False),  'V': (motor9,  False),
    'E': (motor10, False),  'G': (motor11, False),  'B': (motor12, False),
    'R': (motor13, False),  'T': (motor14, False),  'H': (motor15, False),
    'N': (motor16, False),  'U': (motor17, False),  'Y': (motor18, False),
    'I': (motor19, False),  'K': (motor20, False),  'P': (motor21, False),
    'O': (motor22, False),  'L': (motor23, False),  '.': (motor24, False),
    ',': (motor25, False),  'M': (motor26, False), 'T': (motor27, False),
    'Z': (motor28, False),
    
    # GPIO motors  0–9 and symbols
    '0': (gpio_pwm['0'], True),  '1': (gpio_pwm['1'], True),
    '2': (gpio_pwm['2'], True),  '3': (gpio_pwm['3'], True),
    '4': (gpio_pwm['4'], True),  '5': (gpio_pwm['5'], True),
    '6': (gpio_pwm['6'], True),  '7': (gpio_pwm['7'], True),
    '8': (gpio_pwm['8'], True),  '9': (gpio_pwm['9'], True),
    '!': (gpio_pwm['!'], True),  '@': (gpio_pwm['@'], True),
    '#': (gpio_pwm['#'], True),  '$': (gpio_pwm['$'], True),
    '%': (gpio_pwm['%'], True),  '^': (gpio_pwm['^'], True),
    '&': (gpio_pwm['&'], True),
}
 
# ── Internal worker run on a background thread ────────────────────────────────
def _motor_worker(letter, duty_cycle, duration, cancel):
    pin, is_gpio = MOTORS[letter]
    if is_gpio:
        pin.ChangeDutyCycle(duty_cycle * 100)
        # Sleep in small increments so we can respond to cancel quickly
        slept = 0.0
        step  = 0.01
        while slept < duration:
            if cancel.is_set():
                break
            time.sleep(step)
            slept += step
        # Only turn off if we weren't cancelled — if we were, the new thread
        # already owns this pin and will turn it off when it finishes.
        if not cancel.is_set():
            pin.ChangeDutyCycle(0)
    else:
        _software_pwm(pin, duty_cycle=duty_cycle, duration=duration, cancel=cancel)
 
# ── Public API ────────────────────────────────────────────────────────────────
def run_motor(letter, duty_cycle=0.1, duration=2):
    """
    Start a motor on a background daemon thread.  Returns immediately so the
    game loop is never blocked.
 
    If the same key is still buzzing from a previous call, that buzz is
    cancelled first and a fresh one starts — prevents pile-up when the same
    key is pressed repeatedly.
 
    Args:
        letter:     Key in MOTORS (e.g. 'A', '1', 'O').
        duty_cycle: 0.0–1.0  (converted to 0–100 % for GPIO hardware PWM).
        duration:   Vibration length in seconds.
    """
    letter = letter.upper()
    if letter not in MOTORS:
        print(f"run_motor: unknown key '{letter}'")
        return
 
    with _cancel_lock:
        # Cancel any in-flight buzz for this key
        if letter in _cancel_events:
            _cancel_events[letter].set()
 
        cancel = threading.Event()
        _cancel_events[letter] = cancel
 
    t = threading.Thread(target=_motor_worker,
                         args=(letter, duty_cycle, duration, cancel),
                         daemon=True)
    t.start()
 
 
def stop_motor(letter):
    """Immediately stop a specific motor."""
    letter = letter.upper()
    if letter not in MOTORS:
        return
    with _cancel_lock:
        if letter in _cancel_events:
            _cancel_events[letter].set()
    pin, is_gpio = MOTORS[letter]
    if is_gpio:
        pin.ChangeDutyCycle(0)
    else:
        pin.value = False
 
 
def motor_cleanup():
    """Stop all motors and release GPIO resources."""
    # Cancel every running thread
    with _cancel_lock:
        for ev in _cancel_events.values():
            ev.set()
        _cancel_events.clear()
 
    for pin, is_gpio in MOTORS.values():
        if is_gpio:
            try:
                pin.ChangeDutyCycle(0)
                pin.stop()
            except Exception:
                pass
        else:
            try:
                pin.value = False
            except Exception:
                pass
    GPIO.cleanup()