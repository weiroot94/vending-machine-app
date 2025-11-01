import serial
import time
import hashlib
from src.globals import *

VERIFY = 'verify'
ALLOW = 'Allow'
DISALLOW = 'Not Allow'

def start_client(port, baud_rate):
    try:
        # Open the serial port
        ser = serial.Serial(port, baud_rate, timeout=1)
        print(f"Client connected to {port} at {baud_rate} baud")

        # Send a message to the server
        message = VERIFY
        ser.write(message.encode())
        print(f"Sent to server: {message}")

        while(True):
            response = ser.readline().decode().strip()

            if response == ALLOW:
                # Read the response from the server
                # Add any function here
                print(f"Received from server: {response}")
                set_verification_success()
                break

            if response == DISALLOW:
                # Read the response from the server
                # Add any function here
                print(f"Received from server: {response}")
                set_verification_failed()
                break

    except serial.SerialException as e:
        print(f"Error: {e}")

    finally:
        # Close the serial port
        if ser.is_open:
            ser.close()