#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys
import serial
from chip.ch9329 import control

def doport(com):
    print(" - baud_rate:" + str(com.baudrate))  
    print(" - byte_size:" + str(com.bytesize))  
    print(" - break_condition:" + str(com.break_condition))  

    if com.isOpen():
        print(" - status:OK")
    else:
        print(" - status:FAIL")
        return
    c = control.Control(com)  
    c.keyboard_free()
    c.word("hellodskljflasdjflajsd",1)
if __name__ == "__main__":
    try:
        com = serial.Serial("/dev/cu.usbserial-20", 9600, timeout=1)
        print("Open OK")
        doport(com)
    except serial.serialutil.SerialException as e:
        print(" - Error:" + repr(e))
        #return
