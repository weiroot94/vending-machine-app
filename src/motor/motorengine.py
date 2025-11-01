from __future__ import division
import time
import platform
import os
from dotenv import load_dotenv

# Import the PCA9685 module.
import Adafruit_PCA9685

load_dotenv()
debug_mode = os.getenv('DEBUG', 'False').lower() in ['true']

os_name = platform.system()
pwm = 0

if os_name == "Windows":
    print("Running on Windows.")
elif os_name == "Linux":
    if debug_mode  == False:
        pwm = Adafruit_PCA9685.PCA9685()
    servo_min = 150  # Min pulse length out of 4096
    servo_max = 600  # 600  # Max pulse length out of 4096
    if debug_mode  == False:
        pwm.set_pwm_freq(60)


def set_servo_pulse(channel, pulse):
    pulse_length = 1000000    # 1,000,000 us per second
    pulse_length //= 60       # 60 Hz
    print('{0}us per period'.format(pulse_length))
    pulse_length //= 4096     # 12 bits of resolution
    print('{0}us per bit'.format(pulse_length))
    pulse *= 1000
    pulse //= pulse_length
    pwm.set_pwm(channel, 0, pulse)

def item_out(boxindex):
    if os_name == "Windows":
        result = int(boxindex) - 1
        print(str(result))
    elif os_name == "Linux":
        pwm.set_pwm((int(boxindex) - 1), 0, servo_min)
        time.sleep(1)
        pwm.set_pwm((int(boxindex) - 1), 0, servo_max)
        time.sleep(1)

