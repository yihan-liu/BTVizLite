# btvizlite_serial_manager.py

import time
from multiprocessing import Process, Queue, Event

import serial


class BTVizLiteSerialManager:
    def __init__(self, port, baudrate=9600, timeout=1.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.log_queue = Queue()
        self.command_queue = Queue()
        self.stop_event = Event()
        self.process = Process(target=self.worker)

    def worker(self):
        try:
            ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
        except Exception as e:
            self.log_queue.put(f'Error opening serial port: {e}')
            return
        
        while not self.stop_event.is_set():
            # check if there is any command to send
            while not self.command_queue.empty():
                cmd = self.command_queue.get()
                try:
                    ser.write((cmd + '\n').encode('utf-8'))
                except Exception as e:
                    self.log_queue.put(f'Send error: {e}')

            # read incoming data (if available)
            if ser.in_waiting:
                try:
                    line = ser.readline().decode('utf-8').strip()
                    if line:
                        self.log_queue.put(line)
                except Exception as e:
                    self.log_queue.put(f'Read error: {e}')

            time.sleep(0.01)
        
        ser.close()

    def start(self):
        self.process.start()

    def stop(self):
        self.stop_event.set()
        self.process.join()

    def retrieve(self):
        '''
        Nonblocking data retrieval from serial process
        '''
        data = []
        while not self.log_queue.empty():
            data.append(self.log_queue.get())
        return data
    
    def send(self, cmd):
        '''
        Place a command into the queue to let the worker send it
        '''
        self.command_queue.put(cmd)