# display_widget.py
from collections import deque

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QPlainTextEdit, QMessageBox
import qasync
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from btviz.ui_utils import calculate_window
from .plot_settings_widget import PlotSettingsWidget


class DisplayWidget(QWidget):
    """A widget for displaying BLE characteristic data and plotting it in real-time."""

    def __init__(self, characteristic):
        """Initializes the display widget.

        :param characteristic: The characteristic to monitor and display.
        """
        super().__init__()

        self.bt_manager = None

        # BLE instances
        self.characteristic = characteristic

        # connection & display flags
        self.isNotif = False
        self.isRead = False
        self.isFirstTransactions = True
        self.isFirstPlot = True
        self.isPlotting = False

        # data container
        self.data_queues = []

        # raw data
        self.notifButton = None
        self.textfield = None

        # save data
        # self.saveButton = None  # TODO

        # display instances
        self.plotButton = None

        self.canvas = None
        self.fig = None
        self.axes = None
        self.lines = None
        self.title = None
        self.xlabel = None
        self.ylabel = None
        self.animate_interval = None
        self.animation = None

        # plot setting
        self.settingsButton = None
        self.plot_setting_window = None

        # layout instance
        self.layout_ = QVBoxLayout(self)

        # start UI
        self.initUI()

    def initUI(self):
        """Initializes the user interface for the display widget."""
        # init the display window
        self.setWindowTitle('Characteristic Reader')
        window_width, window_height, x_pos, y_pos = calculate_window(scale_width=0.5, scale_height=0.7)
        self.setGeometry(x_pos, y_pos, window_width, window_height)

        # enable notification
        self.notifButton = QPushButton('Enable Notifications')
        self.notifButton.clicked.connect(self.enableNotif)

        # initialize plotting
        self.plotButton = QPushButton('Plot')
        self.plotButton.clicked.connect(self.plotInit)
        self.plotButton.setEnabled(False)

        # display decoded data
        self.textfield = QPlainTextEdit()
        self.textfield.setReadOnly(True)

        # plot settings
        self.settingsButton = QPushButton("Plot Settings")
        self.settingsButton.clicked.connect(self.onSettings)

        self.layout_.addWidget(self.notifButton)
        self.layout_.addWidget(self.textfield)
        self.layout_.addWidget(self.plotButton)
        self.layout_.addWidget(self.settingsButton)

    @qasync.asyncSlot()
    async def onSettings(self):
        """Reveal plot settings window"""
        self.plot_setting_window = PlotSettingsWidget()
        self.plot_setting_window.gotPlotSetting.connect(self.onGotSettings)
        self.plot_setting_window.show()

    def onGotSettings(self, settings_str):
        """Update plot settings"""
        str_list = settings_str.split(",")
        self.title = str_list[0]
        self.xlabel = str_list[1]
        self.ylabel = str_list[2]
        self.ax.set_title(self.title)
        self.ax.set_xlabel(self.xlabel)
        self.ax.set_ylabel(self.ylabel)

    @qasync.asyncSlot()
    async def enableNotif(self):
        """Enables notifications for the BLE characteristic."""
        self.notifButton.setEnabled(False)
        try:
            await self.bt_manager.start_notify(self.characteristic, self.decodeRoutine)
            self.isNotif = True
        except Exception as e:
            QMessageBox.information(self, "Info", f"Unable to start notification: {e}")

    def decodeRoutine(self, characteristic, value):
        """
        Routine that Handles decoding of the BLE characteristic.

        :param characteristic: The characteristic that sent the notification.
        :param value: The value of the notification.
        """
        decoded_str = ''
        decoded_list = []
        try:
            decoded_str = value.decode("UTF-8")  # decode the data to string
            decoded_list = decoded_str.split(",")  # split the data with delimiter
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Unable to decode: {e}")
            self.close()

        # Wrap the text to display to the textfield window
        display_text = str(decoded_str) + '\n' + self.textfield.toPlainText()
        self.textfield.setPlainText(display_text)

        # Initialize the container of data dequeue
        if self.isFirstTransactions:
            self.data_queues = []  # container for data in the text panel
            self.lines = []  # container for lines in the plot panel

            # for every datapoint in the list, create one deque
            # TODO: let user to define the number of datapoints
            for _ in decoded_list:
                self.data_queues.append(deque(maxlen=100))

            self.isFirstTransactions = False
            self.plotButton.setEnabled(True)
            # self.saveButton.setEnabled(True)

        for idx, decoded_item in enumerate(decoded_list):
            try:
                decoded_item_float = float(decoded_item.replace('\x00', ''))
                self.data_queues[idx].append(decoded_item_float)
            except Exception as e:
                QMessageBox.warning(self, "Warning", f"Unable to decode: {e}")

    def plotUpdate(self, frame):
        """
        Updates the plot with new data.

        :param frame: The current frame of the animation (unused).
        """
        if self.isPlotting:
            for data_queue, ax, line in zip(self.data_queues, self.axes, self.lines):
                # Update plot data
                line.set_xdata(np.arange(len(data_queue)))
                line.set_ydata(data_queue)
                ax.relim()
                ax.autoscale_view()

                # Set line color
                line.set_color('r')
        return self.lines

    def plotInit(self):
        """
        Starts plotting the BLE characteristic data in real-time.
        """
        # Initialize plot panel
        if self.isFirstPlot:
            self.fig, self.axes = plt.subplots(nrows=len(self.data_queues),
                                               ncols=1)
            self.canvas = FigureCanvas(self.fig)
            self.title = "ADC"
            self.xlabel = "Sample"
            self.ylabel = "Value"
            self.axes[-1].set(xlabel=self.xlabel)
            for ax, data_queue in zip(self.axes, self.data_queues):
                line, = ax.plot(data_queue)
                self.lines.append(line)
                ax.set(ylabel=self.ylabel)

            self.layout_.addWidget(self.canvas)
            self.isFirstPlot = False

        self.plotButton.setEnabled(False)
        self.animation = FuncAnimation(self.fig, self.plotUpdate, interval=1, cache_frame_data=False)
        self.isPlotting = True
        self.canvas.draw_idle()

    @qasync.asyncSlot()
    async def timeoutHandler(self):
        """
        Handles characteristic reading timer timeouts
        """
        value = await self.bt_manager.read_characteristic(self.characteristic)
        self.decodeRoutine(self.characteristic, value)

    @qasync.asyncClose
    async def closeEvent(self, event):
        """
        Routine that terminates characteristic operations prior to scanServicesWindow closure
        """
        if self.isNotif:
            await self.bt_manager.stop_notify(self.characteristic)
