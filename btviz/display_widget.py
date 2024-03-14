# display_widget.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QPlainTextEdit, QMessageBox
import qasync
import struct
from collections import deque
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from .utils import calculate_window
from .plot_settings_widget import PlotSettingsWidget


class DisplayWidget(QWidget):
    """
    A widget for displaying BLE characteristic data and plotting it in real-time.
    """

    def __init__(self, client, char):
        """
        Initializes the display widget.

        :param client: A BleakClient connected to the BLE device.
        :param char: The characteristic to monitor and display.
        """
        super().__init__()

        # BLE instances
        self.m_client = client
        self.m_char = char

        # data container
        self.data_queues = []

        # connection & display flags
        self.isNotif = False
        self.isRead = False
        self.isFirstTransactions = True
        self.isFirstPlot = True

        # raw data
        self.notifButton = None
        self.textfield = None
        # self.saveButton = None  # TODO

        # display instances
        self.plotButton = None
        self.isPlotting = False
        self.lines = None
        self.title = None
        self.xlabel = None
        self.ylabel = None
        self.animateInterval = None
        self.animation = None
        
        self.settingsButton = None
        
        self.window = None

        self.initUI()

    def initUI(self):
        """
        Initializes the user interface for the display widget.
        """
        self.setWindowTitle('Characteristic Reader')
        window_width, window_height, x_pos, y_pos = calculate_window(scale_width=0.5, scale_height=0.7)
        self.setGeometry(x_pos, y_pos, window_width, window_height)

        # enable notification
        self.notifButton = QPushButton('Enable Notifications')
        self.notifButton.clicked.connect(self.enableNotif)

        # start plotting
        self.plotButton = QPushButton('Plot')
        self.plotButton.clicked.connect(self.plot)
        self.plotButton.setEnabled(False)

        # display decoded data
        self.textfield = QPlainTextEdit()
        self.textfield.setReadOnly(True)

        # plot settings
        self.settingsButton = QPushButton("Plot Settings")
        self.settingsButton.clicked.connect(self.onSettings)

        self.my_layout = QVBoxLayout(self)
        self.my_layout.addWidget(self.notifButton)
        self.my_layout.addWidget(self.textfield)
        self.my_layout.addWidget(self.plotButton)
        self.my_layout.addWidget(self.settingsButton)

    @qasync.asyncSlot()
    async def onSettings(self):
        """
        Reveal plot settings scanServicesWindow
        """
        self.window = PlotSettingsWidget()
        self.window.gotPlotSetting.connect(self.onGotSettings)
        self.window.show()

    def onGotSettings(self, settings_str):
        """
        Update plot settings
        """
        str_list = settings_str.split(",")
        self.title = str_list[0]
        self.xlabel = str_list[1]
        self.ylabel = str_list[2]
        self.ax.set_title(self.title)
        self.ax.set_xlabel(self.xlabel)
        self.ax.set_ylabel(self.ylabel)

    @qasync.asyncSlot()
    async def enableNotif(self):
        """
        Enables notifications for the BLE characteristic.
        """
        self.notifButton.setEnabled(False)
        try:
            await self.m_client.start_notify(self.m_char, self.decodeRoutine)
            self.isNotif = True
        except Exception as e:
            QMessageBox.information(self, "Info", f"Unable to start notification: {e}")
            # raise NotificationError(f"Unable to start notification {str(e)}")

    def decodeRoutine(self, char, value):
        """
        Routine that Handles decoding of the BLE characteristic.

        :param char: The characteristic that sent the notification.
        :param value: The value of the notification.
        """
        try:
            decoded_str = value.decode("UTF-8")  # decode the data to string
            decoded_list = decoded_str.split(",")  # split the data with delimiter
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Unable to decode: {e}")
            self.close()

        # Wrap the text to display to the textfield window
        display_text = str(decoded_str) + '\n' + self.textfield.toPlainText()
        self.textfield.setPlainText(display_text)

        # Initialize the container of data deques
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
            except Exception as e:
                QMessageBox.warning(self, "Warning", f"Unable to decode: {e}")
            self.data_queues[idx].append(decoded_item_float)

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

    def plot(self):
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

            self.my_layout.addWidget(self.canvas)
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
        value = await self.m_client.read_gatt_char(self.m_char)
        self.decodeRoutine(self.m_char, value)

    @qasync.asyncClose
    async def closeEvent(self, event):
        """
        Routine that terminates characteristic operations prior to scanServicesWindow closure
        """
        if self.isNotif:
            await self.m_client.stop_notify(self.m_char)
