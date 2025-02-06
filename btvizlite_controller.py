# btvizlite_controller.py

import ttkbootstrap as ttk

from btvizlite_serial_manager import BTVizLiteSerialManager
from btvizlite_gui import BTVizLiteGUI

class BTVizLiteController:
    def __init__(self, port, baudrate=9600, timeout=1.0):
        self.serial_manager = BTVizLiteSerialManager(port, baudrate, timeout)
        self.serial_manager.start()

        self.front_end = BTVizLiteGUI(controller=self)

    def check_serial(self):
        '''periodically check for new serial data and update the plot'''
        data_list = self.serial_manager.retrieve()
        for data in data_list:
            self.front_end.update_plot(data)

        # periodic check to prevent blocking the GUI
        self.front_end.after(100, self.check_serial)

    def send(self, cmd):
        '''Forward to serial manager'''
        self.serial_manager.send(cmd)

    def run(self):
        try:
            self.front_end.mainloop()
        finally:
            self.serial_manager.stop()