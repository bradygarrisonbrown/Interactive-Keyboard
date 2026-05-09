import time
import board
import busio
import RPi.GPIO as GPIO
from adafruit_mcp230xx.mcp23017 import MCP23017

# ── GPIO setup ────────────────────────────────────────────────────────────────
GPIO.setmode(GPIO.BCM)

def software_pwm(pin, duty_cycle, period=0.02, duration=2):
    """Software PWM for MCP23017 pins (they don't support hardware PWM)."""
    on_time = period * duty_cycle
    off_time = period * (1 - duty_cycle)
    end_time = time.time() + duration
    while time.time() < end_time:
        pin.value = True
        time.sleep(on_time)
        pin.value = False
        time.sleep(off_time)

# ── I2C + MCP chips ───────────────────────────────────────────────────────────
i2c = busio.I2C(board.SCL, board.SDA)
mcp1 = MCP23017(i2c, address=0x20)
mcp2 = MCP23017(i2c, address=0x21)

# ── MCP1 pins (A–N = motors 1–14) ────────────────────────────────────────────
motor1  = mcp1.get_pin(0)   # GPA0
motor2  = mcp1.get_pin(1)   # GPA1
motor3  = mcp1.get_pin(2)   # GPA2
motor4  = mcp1.get_pin(3)   # GPA3
motor5  = mcp1.get_pin(4)   # GPA4
motor6  = mcp1.get_pin(5)   # GPA5
motor7  = mcp1.get_pin(6)   # GPA6
motor8  = mcp1.get_pin(7)   # GPB0
motor9  = mcp1.get_pin(8)   # GPB1
motor10 = mcp1.get_pin(9)   # GPB2
motor11 = mcp1.get_pin(10)  # GPB3
motor12 = mcp1.get_pin(11)  # GPB4
motor13 = mcp1.get_pin(12)  # GPB5
motor14 = mcp1.get_pin(13)  # GPB6

# ── MCP2 pins (O–Z = motors 15–26, skipping 27/28 which exceed A–Z) ──────────
motor15 = mcp2.get_pin(0)   # GPA0
motor16 = mcp2.get_pin(1)   # GPA1
motor17 = mcp2.get_pin(2)   # GPA2
motor18 = mcp2.get_pin(3)   # GPA3
motor19 = mcp2.get_pin(4)   # GPA4
motor20 = mcp2.get_pin(5)   # GPA5
motor21 = mcp2.get_pin(6)   # GPA6
motor22 = mcp2.get_pin(7)   # GPB0
motor23 = mcp2.get_pin(8)   # GPB1
motor24 = mcp2.get_pin(9)   # GPB2
motor25 = mcp2.get_pin(10)  # GPB3
motor26 = mcp2.get_pin(11)  # GPB4
# motor27/28 available on mcp2.get_pin(12/13) but exceed A–Z; add to extras if needed

# ── Set all MCP pins as outputs ───────────────────────────────────────────────
for m in [motor1, motor2, motor3, motor4, motor5, motor6, motor7,
          motor8, motor9, motor10, motor11, motor12, motor13, motor14,
          motor15, motor16, motor17, motor18, motor19, motor20, motor21,
          motor22, motor23, motor24, motor25, motor26]:
    m.switch_to_output(value=False)

# ── GPIO hardware PWM pins ────────────────────────────────────────────────────
# Usable GPIO pins (BCM), excluding SDA=2, SCL=3, and common reserved pins.
# Mapped to: digits 0–9, then symbols for remaining pins.
#
#   Explicitly requested: 18, 23, 24, 25, 12, 16, 20, 21
#   Additional usable GPIO (BCM): 4, 5, 6, 13, 17, 19, 22, 26, 27
#
# Key map:
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

# Setup GPIO pins as outputs and create PWM objects (1 kHz)
gpio_pwm = {}
for key, bcm_pin in GPIO_PIN_MAP.items():
    GPIO.setup(bcm_pin, GPIO.OUT)
    pwm = GPIO.PWM(bcm_pin, 1000)
    pwm.start(0)
    gpio_pwm[key] = pwm

# ── Letter → motor dictionary ─────────────────────────────────────────────────
# Value: (pin_object_or_pwm_key, is_gpio)
#   is_gpio=False → MCP pin, use software_pwm()
#   is_gpio=True  → GPIO PWM object, use ChangeDutyCycle()

MOTORS = {
    # MCP motors A–Z
    'A': (motor1,  False),  'B': (motor2,  False),  'C': (motor3,  False),
    'D': (motor4,  False),  'E': (motor5,  False),  'F': (motor6,  False),
    'G': (motor7,  False),  'H': (motor8,  False),  'I': (motor9,  False),
    'J': (motor10, False),  'K': (motor11, False),  'L': (motor12, False),
    'M': (motor13, False),  'N': (motor14, False),  'O': (motor15, False),
    'P': (motor16, False),  'Q': (motor17, False),  'R': (motor18, False),
    'S': (motor19, False),  'T': (motor20, False),  'U': (motor21, False),
    'V': (motor22, False),  'W': (motor23, False),  'X': (motor24, False),
    'Y': (motor25, False),  'Z': (motor26, False),

    # GPIO motors: digits + symbols
    '0': (gpio_pwm['0'], True),   # GPIO 4
    '1': (gpio_pwm['1'], True),   # GPIO 5
    '2': (gpio_pwm['2'], True),   # GPIO 6
    '3': (gpio_pwm['3'], True),   # GPIO 12
    '4': (gpio_pwm['4'], True),   # GPIO 13
    '5': (gpio_pwm['5'], True),   # GPIO 16
    '6': (gpio_pwm['6'], True),   # GPIO 17
    '7': (gpio_pwm['7'], True),   # GPIO 18
    '8': (gpio_pwm['8'], True),   # GPIO 19
    '9': (gpio_pwm['9'], True),   # GPIO 20
    '!': (gpio_pwm['!'], True),   # GPIO 21
    '@': (gpio_pwm['@'], True),   # GPIO 22
    '#': (gpio_pwm['#'], True),   # GPIO 23
    '$': (gpio_pwm['$'], True),   # GPIO 24
    '%': (gpio_pwm['%'], True),   # GPIO 25
    '^': (gpio_pwm['^'], True),   # GPIO 26
    '&': (gpio_pwm['&'], True),   # GPIO 27
}

# ── run_motor ─────────────────────────────────────────────────────────────────
def run_motor(letter, duty_cycle=0.1, duration=3):
    """
    Run a motor by its letter/symbol key.

    Args:
        letter:     Key from MOTORS dict (e.g. 'A', '7', '#').
        duty_cycle: 0.0–1.0 for MCP software PWM;
                    converted to 0–100 for GPIO hardware PWM.
        duration:   How long to run the motor (seconds). Only applies to MCP.
                    GPIO motors run until explicitly stopped.
    """
    if letter not in MOTORS:
        print(f"Unknown motor key: '{letter}'")
        return

    pin, is_gpio = MOTORS[letter]

    if is_gpio:
        # Hardware PWM: duty_cycle 0.0–1.0 → 0–100%
        pin.ChangeDutyCycle(duty_cycle * 100)
        time.sleep(duration)
        pin.ChangeDutyCycle(0)
    else:
        # MCP software PWM
        software_pwm(pin, duty_cycle=duty_cycle, duration=duration)
        pin.value = False

def stop_motor(letter):
    """Immediately stop a motor."""
    if letter not in MOTORS:
        return
    pin, is_gpio = MOTORS[letter]
    if is_gpio:
        pin.ChangeDutyCycle(0)
    else:
        pin.value = False

# ── Cleanup ───────────────────────────────────────────────────────────────────
def motor_cleanup():
    """Stop all motors and release GPIO resources."""
    for key, (pin, is_gpio) in MOTORS.items():
        if is_gpio:
            pin.ChangeDutyCycle(0)
            pin.stop()
        else:
            pin.value = False
    GPIO.cleanup()

# ── Example usage ─────────────────────────────────────────────────────────────
try:
    while True:
        print("ON")
        run_motor('A', duty_cycle=0.1, duration=2)   # MCP motor 1
        run_motor('O', duty_cycle=0.1, duration=2)   # MCP motor 15
        run_motor('7', duty_cycle=0.1, duration=2)   # GPIO 18 (was led3)
        time.sleep(1)

        print("OFF")
        # Motors auto-stop after duration, but explicit stop is safe too
        stop_motor('A')
        stop_motor('O')
        stop_motor('7')
        time.sleep(1)

except KeyboardInterrupt:
    pass
finally:
    motor_cleanup()