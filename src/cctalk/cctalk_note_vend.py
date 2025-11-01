#!/usr/bin/env python3
import os
import threading
import time
import serial
import sys
import os
import keyboard
from src.globals import *
#from pynput.keyboard import Controller, KeyCode, Key

#keyboard = Controller()



# # ----------------------------
# import RPi.GPIO as GPIO
# from gpiozero import Button, LED
# # ---------------------------

# ################################################################################### card rfid

# import board
# import busio

# from adafruit_pn532.adafruit_pn532 import MIFARE_CMD_AUTH_B
# from adafruit_pn532.i2c import PN532_I2C

# i2c = busio.I2C(board.SCL, board.SDA)

# # Non-hardware reset/request with I2C
# pn532 = PN532_I2C(i2c, debug=False)


# ic, ver, rev, support = pn532.firmware_version
# print ("Found PN532 with firmware version: {0}.{1}".format(ver, rev))

# pn532.SAM_configuration()
# print ("Waiting for RFID/NFC card to write to")


# # pin numbers
# switch = 16
# red = 5
# green = 6
# led_red = LED(red)
# led_green = LED(green)
# # -------------------


root_path = os.path.join(os.path.dirname(__file__))
os.chdir(root_path)

##########################################################################################

try:
    ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=0.5)
except Exception:
    print('Unable to open serial port. Things should die gracefully :)\n')
    sys.exit(1)

devices = list()
rotate_places = 12
feed_master = 99;
tap_arr = [7,4,5,3,1,2,3,2,6,1];
bnv_code_len = 6

def addmoney(cash):
    print("money in inserted")
    print(cash)
    set_total_money(int(cash))
    #call continue
        
def logical_shift_right(value, bits):
    """
    Python's >> is an arithmetic right shift, and there is no equivalent to
    C/Java's logical right shift. This is a simple implementation to emulate
    the >>> operator in those languages.
    """
    return (value & 0xFFFFFFFF) >> bits

def bnv_encrypt(code: bytes, data: bytearray):
    initial_xor = ~((code[0] << 4) | code[4])
    
    for i in range(0, len(data)):
        d = data[i]
        d ^= initial_xor
        data[i] = bytes([d % 256])[0]

    for i in range(0, len(data)):
        if (code[3] & (1 << (i & 0x03))) == 0:
            continue
        t = data[i]
        data[i] = bytes([((t & 0x01) << 7) |\
                         ((t & 0x02) << 5) |\
                         ((t & 0x04) << 3) |\
                         ((t & 0x08) << 1) |\
                         ((t & 0x10) >> 1) |\
                         ((t & 0x20) >> 3) |\
                         ((t & 0x40) >> 5) |\
                         ((t & 0x80) >> 7)])[0]

    for i in range(0, rotate_places):
        c1 = 0
        if (data[-1] & 0x01 != 0):
            c1 = 128

        for j in range(0, len(data)):
            if data[j] & (1 << tap_arr[(code[1] + j) % 10]) != 0:
                c1 ^= 128

        for j in range(0, len(data)):
            c = 0
            if (data[j] & 0x01) != 0:
                c = 128
            
            if (code[5] ^ feed_master) & (1 << ((i + j) % 8)) != 0:
                c ^= 128

            d = data[j] & 0xFF
            data[j] = bytes([logical_shift_right(d, 1) + c1])[0]

            c1 = c

    final_xor = (code[2] << 4) | code[2]
    
    for i in range(0, len(data)):
        tf = data[i]
        tf ^= final_xor
        data[i] = bytes([tf])[0]
    return data

def bnv_decrypt(code: bytes, data: bytearray):
    initial_xor = (code[2] << 4) | code[2]
    
    for i in range(0, len(data)):
        d = data[i]
        d ^= initial_xor
        data[i] = bytes([d % 256])[0]

    for i in range(rotate_places-1, -1, -1):
        c1 = 0
        if (data[0] & 0x80) != 0:
            c1 = 1

        for j in range(0, len(data)):
            if data[j] & (1 << (tap_arr[(code[1] + j) % 10] - 1)) != 0:
                c1 ^= 1

        for j in range(len(data)-1, -1, -1):
            c = 0
            if (data[j] & 0x80) != 0:
                c = 1
            
            if (code[5] ^ feed_master) & (1 << ((i + j - 1) % 8)) != 0:
                c ^= 1

            data[j] = bytes([((data[j] << 1) + c1) % 256])[0]
            c1 = c

    for i in range(0, len(data)):
        if (code[3] & (1 << (i & 0x03))) == 0:
            continue
        t = data[i]
        data[i] = bytes([((t & 0x01) << 7) |\
                         ((t & 0x02) << 5) |\
                         ((t & 0x04) << 3) |\
                         ((t & 0x08) << 1) |\
                         ((t & 0x10) >> 1) |\
                         ((t & 0x20) >> 3) |\
                         ((t & 0x40) >> 5) |\
                         ((t & 0x80) >> 7)])[0]


    final_xor = ~((code[0] << 4) | code[4])
    
    for i in range(0, len(data)):
        tf = data[i]
        tf ^= final_xor
        data[i] = bytes([tf % 256])[0]
    return data


def checksum256(msg):
    """
    Calculates the one byte checksum for msg
    """
    total = 0
    for byte in msg:
        total += byte
    return bytes([256 - (total % 256)]) # returns a single byte

def crc16(msg, poly=0x1021):
    """
    Calculates the CRC-CCITT (KERMIT) checksum for msg
    """
    crc = 0
    for b in msg:
        crc ^= (b << 8) & 0xffff
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ poly) & 0xffff
            else:
                crc <<= 1
                crc &= 0xffff
    return bytes([(crc & 0xff00) >> 8, crc & 0x00ff])


def send_cmd(dest, header, data, crclen, code=bytes(6)):
    cmd = None
    if crclen == 8:
        # [dest][length][src][header][data][checksum]
        cmd = bytearray([dest, len(data), 0x01, header]) + data
        print(cmd)
        cmd += checksum256(cmd)
    elif crclen == 16:
        # [dest][length][CRC-16 LSB][Header][Data][CRC-16 MSB]
        cmd = bytearray([dest, len(data), header, data])
        crc = crc16(cmd)
        cmd = bytearray([dest, len(data), crc[1], header, data, crc[0]])

    if code != bytes(6):
        cipher = bnv_encrypt(code, cmd[2:])
        cmd = cmd[:2] + cipher

    ser.write(cmd)
    _ = ser.read(len(cmd))

def fetch_response(code=bytes(6)):
    dest = ser.read(1)
    if dest == b'\x00':
        return b'\x00'

    length = ser.read(1)

    if code == bytes(6):
        source = ser.read(1)
        header = ser.read(1)
        data = ser.read(int.from_bytes(length, byteorder='big'))
        checksum = ser.read(1)
    else:
        cipher = ser.read(3+length)
        plain = bnv_decrypt(code, cipher)
        plain = plain[:-1]
        data = plain[2:]

    return data if data else b'\x00'

def poll_device():
    for routine in devices:
        routine()
    threading.Timer(0.2, poll_device).start() # set recall interval here

class Coin():
    def __init__(self, crc=8, code=bytes(6)):
        self.accept_enable = False
        self.mech_address = 2
        self.event_number = 0
        self.divert = 0 # this will be active when coins go to cashbox
        self.cmd_poll=254
        self.cmd_getcoinid=184
        self.cmd_creditpoll=229
        self.cmd_reset=1
        self.cmd_getroute=209
        self.cmd_setroute=210
        self.cmd_setoverides=222
        self.cmd_modifyinhibits=231
        self.cmd_selfcheck=232
        self.routeinhibits = b'\x7e\x7d\x7b\x77'#just bitmasks for route inhibits
        self.credit_values = [0.00,0.00,0.50,1.00,2.00,10.00,0.00,0.00,0,0,0,0,0,0,0,0,0]
        self.credit = 0
        self.bnv_code = code
        self.crc = crc
        self.cmd_get_encryption = 111 #requires trusted mode to read keys
        self.cmd_111_sig = b'\xAA\x55\x00\x00\x55\xAA' #sent as data with cmd 111 seems pointless for implementation

    def get_credit(self):
        cr = self.credit
        self.credit = 0
        return cr

    def stop_accepting(self):
        self.accept_enable = False

    def connect_mech(self):
        try:
            ser
        except NameError:
            return False

        send_cmd(self.mech_address, self.cmd_reset, bytes(), self.crc, self.bnv_code)
        _ = fetch_response(self.bnv_code)
        send_cmd(self.mech_address, self.cmd_get_encryption, self.cmd_111_sig, self.crc, self.bnv_code) # des check is done 8 bit checksum no encryption
        _ = fetch_response(bytes(6))
        _ = fetch_response(bytes(6))
        #print "des check ",binascii.hexlify(r)
        #bnv = binascii.hexlify(r[6])+binascii.hexlify(r[7])+binascii.hexlify(r[8])
        #print "bnv key is - ",bnv[1]+bnv[0]+bnv[3]+bnv[2]+bnv[5]+bnv[4]
        send_cmd(self.mech_address, self.cmd_poll, bytes(), self.crc, self.bnv_code)
        response = fetch_response(self.bnv_code)

        if not response:
            ser.close()
            return False

        send_cmd(self.mech_address, self.cmd_reset, bytes(), self.crc, self.bnv_code)
        ser.readline()
        send_cmd(self.mech_address, self.cmd_selfcheck, bytes(), self.crc, self.bnv_code)
        faults = fetch_response(self.bnv_code)
        print(f'faults: {faults}')
        if faults:
            print(f'Fault Found - : {self._check_fault(faults)}\n')
            return False

        print('Self test completed no faults found\n')
        # bank 1 only enabled
        send_cmd(self.mech_address, self.cmd_modifyinhibits, bytes([255, 0]), self.crc, self.bnv_code)
        _ = fetch_response(self.bnv_code)

        print('Coinmech Enabled\n')
        self.accept_enable = True
        devices.append(self.poll_mech)
        return True

    def poll_mech(self):
        if not self.accept_enable:
            # TODO: what should we return?
            return None

        if self.divert: # this will check if coins should be diverted
            # 7e 7d 7b 77 i'm just using route 1 for now 
            send_cmd(self.mech_address, self.cmd_setoverides, \
                    self.routeinhibits[0], self.crc, self.bnv_code)
            _ = fetch_response(self.bnv_code)
        else: # TODO: divert check fix me
            send_cmd(self.mech_address, self.cmd_setoverides, \
                    b'\x7f', self.crc, self.bnv_code)
            _ = fetch_response(self.bnv_code)
        
        send_cmd(self.mech_address, self.cmd_creditpoll, bytes(), self.crc, self.bnv_code)
        results = fetch_response(self.bnv_code)

        if not results:
            print("Coin Mech Vanished")
            #self.accept_enable = False

        new_event = results[0]
        results = results[1:]

        for i in range(0, abs(new_event - self.event_number)):
            if i * 2 >= len(results):
                break
            coin = results[i*2]
            route = results[i*2+1]
            print(f'coin, route: {coin}, {route}')

            if coin==3:  # 0.5 euro
                #root_path = os.path.join(os.path.dirname(__file__))
                #os.chdir(root_path)
                #print root_path
                print(" 0.50 euro")
                addmoney('0.5')                
                
            if coin==4:
                #root_path = os.path.join(os.path.dirname(__file__))
                #os.chdir(root_path)
                #print root_path
                print(" 1.00 euro")
                addmoney('1')

            if coin==5:
                #root_path = os.path.join(os.path.dirname(__file__))
                #os.chdir(root_path)
                #print root_path
                print(" 2.00 euro")
                addmoney('2')


            if coin==6:  # 2 euro
                #root_path = os.path.join(os.path.dirname(__file__))
                #os.chdir(root_path)
                #print root_path
                #os.system(root_path + "\\" + "10.exe")
                print(' 211 euro')
                # os.system('start c:\\10.exe ')
            if coin == 0 and route > 0:
                print('Error : ')
            elif coin > 0 and coin < 10:
                print('coin accepted')
                self.credit += self.credit_values[coin-1]
                print(f'credit: {self.credit}')
        self.event_number = new_event

    def _check_error(self, number):
        errors = [(1,"Reject Coin"),
                (2,"Coin Inhibited"),
                    (3,"Multiple Window Error"),
                    (5,"Validation Timeout"),
                    (6,"Coin Accept Over Timeout"),	    
                    (7,"Sorter Opto Timeout"),
                (8,"Second Close Coin"),
                    (9,"Accept Gate Not Ready"),
                (10,"Credit Sensor Not Ready"),	    
                    (11,"Sorter Not Ready"),
                (12,"Reject Coin Not Cleared"),
                    (14,"Credit Sensor Blocked"),
                    (15,"Sorter Opto Blocked"),	 		    
                (17,"Coin Going Backwards"),
                (18,"Accept Sensor Under Timeout"),
                    (19,"Accept Sensor Over Timeout"),
                    (21,"Dce Opto Timeout"),	    
                    (22,"Dce Opto Error"),
                (23,"Coin Accept Under Timeout"),
                    (24,"Reject Coin Repeat"),
                    (25,"Reject Slug"),
                    (128,"Coin 1 Inhibited"),
                    (129,"Coin 2 Inhibited"),
                    (130,"Coin 3 Inhibited"),	    
                    (131,"Coin 4 Inhibited"),
                    (132,"Coin 5 Inhibited"),
                    (133,"Coin 6 Inhibited"),
                (134,"Coin 7 Inhibited"),	    
                    (135,"Coin 8 Inhibited"),
                (136,"Coin 9 Inhibited"),
                    (137,"Coin 10 Inhibited"),
                    (138,"Coin 11 Inhibited"),	 		    
                    (139,"Coin 12 Inhibited"),
                    (140,"Coin 13 Inhibited"),
                    (141,"Coin 14 Inhibited"),
                (142,"Coin 15 Inhibited"),	    
                (143,"Coin 16 Inhibited"),
                    (254,"Flight Deck Open")]

        for i in range(0, len(errors)):
            if errors[i][0] == number:
                return errors[i][1]

    def _check_fault(self, number) :

        faults = [(0,"No Faults Found"),
                (1,"Eeprom Checksum Error"),
                    (2,"Inductive Coils Faulty"),
                    (3,"Credit Sensor Faulty"),
                (4,"Piezo Sensor Faulty"),	    
                (8,"Sorter Exits Faulty"),
                (19,"Reject Flap Sensor Fault"),
                    (21,"Rim Sensor Faulty"),
                    (22,"Thermistor Faulty"),	    
                    (35,"Dce Faulty")]

        for i in range(0, len(faults)):
            if faults[i][0] == number:
                return faults[i][1]	

class Note():
    def __init__(self, crc=8, code=bytes(6)):
        self.request_bill_id=157#Header 157 - Request bill id
        self.cmd_creditpoll=229
        self.cmd_reset=1
        self.cmd_modifyinhibits=231
        self.read_bill_events =159 #Header 159 - Read buffered bill events
        self.accept_enable = False
        self.mech_address = 40
        self.event_number =0
        self.divert = 0 # this will be active when coins go to cashbox
        self.cmd_poll=254
        self.credit_values = [1.00,0.50,0.20,0.10,0,2.00,0.05,0.00,0.00,1.00,0.50,0.20,0.10,0.00,2.00,0.05,0.00]
        self.credit = 0
        self.bnv_code = code
        self.crc = crc
        self.notes_paid = 0 
        self.rfid_cash = 0
        self.uid = None
        #self.data = 0 
        self.data = bytearray(16)
        self.allow_success_flag = False
        self.key = b"\xFF\xFF\xFF\xFF\xFF\xFF"
        
    def show_led(self):
        if self.allow_success_flag:
            #pass
            led_green.on()
            time.sleep(1)
            led_green.off()
        else:
            pass
            led_red.on()
            led_green.off()

    def show_led_off(self):
        if self.allow_success_flag:
            pass
            led_green.off()
            led_red.on()
        else:
            pass
            led_red.off()
            led_green.on()


    def connect_mech(self):
        try:
            ser
        except NameError:
            return False

        send_cmd(self.mech_address, self.cmd_poll, bytes(), self.crc, self.bnv_code)
        response = fetch_response(self.bnv_code)

        if not response:
            ser.close()
            return False

        send_cmd(self.mech_address, self.cmd_reset, bytes(), self.crc, self.bnv_code)
        _ = ser.readline()

        alive = False
        while not alive: # wait after reset command for a response
            send_cmd(self.mech_address, self.cmd_poll, bytes(), self.crc, self.bnv_code)
            alive = fetch_response(self.bnv_code)

        send_cmd(self.mech_address, self.cmd_modifyinhibits, bytes([255, 255]),\
                self.crc, self.bnv_code) # all enabled
        fetch_response(self.bnv_code)

        self.accept_enable = True
        for i in range(1, 17):
            # Header 157 - Request bill id
            send_cmd(self.mech_address, 157, bytes([i]), self.crc, self.bnv_code)
            print((i, fetch_response(self.bnv_code)))

        # Header 228 - Modify master inhibit status
        # TODO: check if ACK is returned
        send_cmd(self.mech_address, 228, bytes([255]), self.crc, self.bnv_code)
        _ = fetch_response(self.bnv_code)

        # Header 32 - Inhibition Pockets
        # TODO: check return, also the original py2 program sent 2 bytes
        # but the command reference says that 0 or 1 bytes are expected
        # bug?
        send_cmd(self.mech_address, 32, bytes([0, 3]), self.crc, self.bnv_code)
        _ = fetch_response(self.bnv_code)

        # TODO: bug? poll_mech isn't being called here, and it returns nothing
        devices.append(self.poll_mech)
        return True

    def poll_mech(self):
        if self.accept_enable:
           

            send_cmd(self.mech_address, self.read_bill_events, bytes(), self.crc, self.bnv_code)
            results = fetch_response(self.bnv_code)
            
            # self.uid = pn532.read_passive_target(timeout=0.5)

            if not results:
                print('Note Mech Vanished')
                self.accept_enable = False
                # TODO: should this return something?
                return None
            else:
                new_event = results[0]
                results = results[1:]

                for i in range(0, abs(new_event - self.event_number)):
                    note = results[i * 2]
                    route = results[i * 2 + 1]
                    if note <= 0:
                        continue

                    if (note>0) and (route == 1):
                        print('NOTE IN ESCROW')
                        # Header 154 - Route bill
                        send_cmd(self.mech_address, 154, bytes([1]), self.crc, self.bnv_code)
                        
                        
                        # Sent to cashbox
                        # TODO: check return
                        _ = fetch_response(self.bnv_code)
                    if (note>0) and (route == 0):
                        # Header 157 - Request bill id
                        send_cmd(self.mech_address, 157, bytes([note]), self.crc, self.bnv_code)
                        print(f'BILL ID {fetch_response(self.bnv_code)} Accepted')
                        if note == 1:
                            print("Note 5")
                            #self.rfid_cash = self.rfid_cash + 5
                            
                            #os.system("c:/nircmd.exe sendkeypress add add 5 enter")
                            addmoney('5')

                            #logging.info(str(self.rfid_cash))
                        if note == 2:
                            print("Note 10")
                            # os.system("c:/nircmd.exe sendkeypress add add 1 0 enter")
                            addmoney('10')


                        if note == 3:
                            print("Note 20")
                            # os.system("c:/nircmd.exe sendkeypress add add 2 0 enter")
                            addmoney('20')

                            #logging.info(str(self.rfid_cash))
                        if note == 4:
                            print("Note 50")
                            
                            # os.system("c:/nircmd.exe sendkeypress add add 5 0 enter")
                            addmoney('50')

                            #logging.info(str(self.rfid_cash))
                        if note == 5:
                            print("Note 100")
                            #os.system("c:/nircmd.exe sendkeypress add add 1 0 0 enter")
                            addmoney('100')
                            
                            #logging.info(str(self.rfid_cash))
                            
                        if note == 6:
                            print("Note 200")
                            #os.system("c:/nircmd.exe sendkeypress add add 1 0 0 enter")
                            addmoney('200')           
                
            self.event_number = new_event

    def pay_note(self):
        self.disable_mech()
        time.sleep(1)
        # Header 27 - Application specific
        send_cmd(self.mech_address, 27, bytes([165]), self.crc, self.bnv_code)
        _ = fetch_response(self.bnv_code)
        # Header 28 - Application specific
        send_cmd(self.mech_address, 28, bytes([0] + [48] * 8 + [1]), self.crc, self.bnv_code)
        data = fetch_response(self.bnv_code)
        # TODO: bug? fetch_response might return nothing on this second call
        _ = fetch_response(self.bnv_code)

        self.enable_mech()
        if not data:
            return False
        notes_paid = int.from_bytes(data[0], byteorder='big')
        return notes_paid != 0

    def pause_1(self):
        print('PAUSED FOR 1 MINUTE')
        self.disable_mech()
        time.sleep(20)
        print('PAUSE IS DONE')
        self.enable_mech()

    def disable_mech(self):
        print('mech disabled')
        self.accept_enable = False
        # Header 228 - Modify master inhibit status
        send_cmd(self.mech_address, 228, bytes([0]), self.crc, self.bnv_code)
        time.sleep(2)
        # TODO: check if ACK is returned
        _ = fetch_response(self.bnv_code)

    def enable_mech(self):
        print('mech enable')
        self.accept_enable = True
        # Header 228 - Modify master inhibit status
        send_cmd(self.mech_address, 228, bytes([255]), self.crc, self.bnv_code)
        # TODO: check if ACK is returned
        _ = fetch_response(self.bnv_code)

    def stop_polling(self):
        print(devices.remove(self.poll_mech))

#poll_device()
