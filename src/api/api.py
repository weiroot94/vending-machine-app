import sys
from src.motor.motorengine import item_out
from src.serial.serial import start_client
from src.globals import *

class Api:
    def __init__(self):
        self.cancel_heavy_stuff_flag = False

    def init(self):
        response = {'message': 'Hello from Python {0}'.format(sys.version)}
        return response

    def motor_working(self, box):
        item_out(box)

    def can_continue(self):
        (amount, price, count) = get_globals()
        if amount >= price * count:
            return {'amount': amount, 'price': price, 'count': count, 'status': True}
        else:
            return {'amount': amount, 'price': price, 'count': count, 'status': False}
        
    def reset_amount(self):
        reset_globals()
        
    def start_verification_client(self):
        serial_port = '/dev/ttyS0'  # Replace with your actual serial port
        baud_rate = 9600
        start_client(serial_port, baud_rate)
        
    def verification_status(self):
        status = get_verification_status()
        if (status == 1):
            return {'status': True}
        else:
            return {'status': False}