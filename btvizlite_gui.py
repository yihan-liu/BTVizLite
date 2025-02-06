# btvizlite_gui.py

import os
import logging

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

class BTVizLiteGUI(ttk.Window):
    def __init__(self, controller, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.controller = controller
        self.title('BTVizLite')
        self.geometry('800x600')

        # set up logging to file
        log_dir = 'command_log'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        logging.basicConfig(filename=os.path.join(log_dir, 'sent_commands.log'),
                            level=logging.INFO,
                            format='%(asctime)s - %(message)s')
        
        self.create_widgets()
    
    def create_widgets(self):
        # Configure grid layout for the main window.
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=3)  # Plot frame
        self.rowconfigure(1, weight=0)  # Command entry frame
        self.rowconfigure(2, weight=1)  # Logger frame

        # Plot frame.
        self.plot_frame = ttk.Frame(self)
        self.plot_frame.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        self.fig = Figure(figsize=(5, 4))
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title('Data from microcontroller')
        self.line, = self.ax.plot([], [], marker='o')
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=True)

        # Command entry and send button frame.
        self.entry_frame = ttk.Frame(self)
        self.entry_frame.grid(row=1, column=0, sticky='ew', padx=5, pady=5)
        self.entry_frame.columnconfigure(0, weight=1)
        self.command_entry = ttk.Entry(self.entry_frame)
        self.command_entry.grid(row=0, column=0, sticky='ew', padx=(0, 5))
        self.send_button = ttk.Button(self.entry_frame, text='Send', command=self.send)
        self.send_button.grid(row=0, column=1)

        # Logger frame.
        self.log_frame = ttk.Frame(self)
        self.log_frame.grid(row=2, column=0, sticky='nsew', padx=5, pady=5)
        self.log_text = ttk.Text(self.log_frame, height=10)
        self.log_text.pack(side=TOP, fill=BOTH, expand=True)    

    def update_plot(self, data_line):
        '''
        Expect data_line as a *comma delimited string of numeric values*
        '''
        try:
            # convert a comma-separated string into a list of floats
            values = [float(data) for data in data_line.split(',')]
            x = list(range(len(values)))
            self.line.set_data(x, values)
            self.ax.relim()
            self.ax.autoscale_view()
            self.canvas.draw()
        except Exception as e:
            self.log(f'Received non-numeric data: {data_line}: {e}')

    def send(self):
        '''
        Retrieve the command from the entry, log it, and ask the controller to send it.
        '''
        cmd = self.command_entry.get().strip()
        if cmd:
            logging.info(f'Sent command: {cmd}')
            self.log(f'Sent command: {cmd}')
            self.controller.send(cmd)
            self.command_entry.delete(0, 'end')

    def log(self, msg):
        if hasattr(self, 'log_text'):
            self.log_text.insert('end', msg + '\n')
            self.log_text.see('end')
        else:
            print(msg)

    def mainloop(self):
        # periodic check to prevent blocking the GUI
        self.after(100, self.controller.check_serial)
        super().mainloop()