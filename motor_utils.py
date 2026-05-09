import time
import board
import busio
import RPi.GPIO as GPIO
from adafruit_mcp230xx.mcp23017 import MCP23017

def software_pwm(pin, duty_cycle, period=0.02, duration=2):
    on_time = period * duty_cycle
    off_time = period * (1 - duty_cycle)

    end_time = time.time() + duration
    while time.time() < end_time:
        pin.value = True
        time.sleep(on_time)
        pin.value = False
        time.sleep(off_time)

# Setup I2C
i2c = busio.I2C(board.SCL, board.SDA)

# MCP chips
mcp1 = MCP23017(i2c, address=0x20)
mcp2 = MCP23017(i2c, address=0x21)

# MCP 1 pins
motor1 = mcp1.get_pin(0)  # GPA0
motor2 = mcp1.get_pin(1)  # GPA1
motor3 = mcp1.get_pin(2)  # GPA2
motor4 = mcp1.get_pin(3)  # GPA3
motor5 = mcp1.get_pin(4)  # GPA4
motor6 = mcp1.get_pin(5)  # GPA5
motor7 = mcp1.get_pin(6)  # GPA6
motor8 = mcp1.get_pin(7)  # GPB0
motor9 = mcp1.get_pin(8)  # GPB1
motor10 = mcp1.get_pin(9)  # GPB2
motor11 = mcp1.get_pin(10)  # GPB3
motor12 = mcp1.get_pin(11)  # GPB4
motor13 = mcp1.get_pin(12)  # GPB5
motor14 = mcp1.get_pin(13)  # GPB6

#MCP 2 pins
motor15 = mcp2.get_pin(0)  # GPA0
motor16 = mcp2.get_pin(1)  # GPA1
motor17 = mcp2.get_pin(2)  # GPA2
motor18 = mcp2.get_pin(3)  # GPA3
motor19 = mcp2.get_pin(4)  # GPA4
motor20 = mcp2.get_pin(5)  # GPA5
motor21 = mcp2.get_pin(6)  # GPA6
motor22 = mcp2.get_pin(7)  # GPB0
motor23 = mcp2.get_pin(8)  # GPB1
motor24 = mcp2.get_pin(9)  # GPB2
motor25 = mcp2.get_pin(10)  # GPB3
motor26 = mcp2.get_pin(11)  # GPB4
motor27 = mcp2.get_pin(12)  # GPB5
motor28 = mcp2.get_pin(13)  # GPB6

motor1.switch_to_output(value=False)
motor2.switch_to_output(value=False)
motor3.switch_to_output(value=False)
motor4.switch_to_output(value=False)
motor5.switch_to_output(value=False)
motor6.switch_to_output(value=False)
motor7.switch_to_output(value=False)
motor8.switch_to_output(value=False)
motor9.switch_to_output(value=False)
motor10.switch_to_output(value=False)
motor11.switch_to_output(value=False)
motor12.switch_to_output(value=False)
motor13.switch_to_output(value=False)
motor14.switch_to_output(value=False)
motor16.switch_to_output(value=False)
motor17.switch_to_output(value=False)
motor18.switch_to_output(value=False)
motor19.switch_to_output(value=False)
motor20.switch_to_output(value=False)
motor21.switch_to_output(value=False)
motor22.switch_to_output(value=False)
motor23.switch_to_output(value=False)
motor24.switch_to_output(value=False)
motor25.switch_to_output(value=False)
motor26.switch_to_output(value=False)
motor27.switch_to_output(value=False)
motor28.switch_to_output(value=False)


# Raspberry Pi GPIO pin (BCM 18 = physical pin 12)
led3 = 12
GPIO.setup(led3, GPIO.OUT)
pwm3 = GPIO.PWM(led3, 1000)  # 1 kHz frequency
pwm3.start(0)  # start at 0% duty cycle

try:
    while True:
        print("ON")
        software_pwm(motor1, duty_cycle=0.1)  # 30% strength
        software_pwm(motor15, duty_cycle=0.1)  # 30% strength
        pwm3.ChangeDutyCycle(10)
        time.sleep(1)

        print("OFF")
        motor1.value = False
        motor15.value = False
        pwm3.ChangeDutyCycle(0)
        time.sleep(1)

except KeyboardInterrupt:
    pass

def motor_cleanup():
    GPIO.cleanup()
    motor1.value = False
    motor2.value = False
    motor3.value = False
    motor4.value = False
    motor5.value = False
    motor6.value = False
    motor7.value = False
    motor8.value = False
    motor9.value = False
    motor10.value = False
    motor11.value = False
    motor12.value = False
    motor13.value = False
    motor14.value = False
    motor15.value = False
    motor16.value = False
    motor17.value = False
    motor18.value = False
    motor19.value = False
    motor20.value = False
    motor21.value = False
    motor22.value = False
    motor23.value = False
    motor24.value = False
    motor25.value = False
    motor26.value = False
    motor27.value = False
    motor28.value = False

