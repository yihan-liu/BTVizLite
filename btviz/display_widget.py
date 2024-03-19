# display_widget.py
from collections import deque

from PyQt5.QtWidgets import (QWidget,
                             QVBoxLayout,
                             QPushButton,
                             QPlainTextEdit,
                             QMessageBox,
                             QSpinBox)
import qasync
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import animation
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from btviz.core import BTManager
from btviz.ui_utils import calculate_window
from .plot_settings_widget import PlotSettingsWidget


class DisplayWidget(QWidget):
    """A widget for displaying BLE characteristic data and plotting it in real-time."""

    def __init__(self, characteristic):
        """Initializes the display widget.

        :param characteristic: The characteristic to monitor and display.
        """
        super().__init__()

        self.bt_manager = BTManager.instance()

        # BLE instances
        self.characteristic = characteristic

        # connection & display flags
        self.isNotif = False
        self.isRead = False
        # self.isFirstTransactions = True
        self.isFirstPlot = True
        self.isPlotting = False

        # data container
        self.data_queues = []
        self.num_values_input = None
        self.confirm_values_button = None

        # raw data
        self.start_notification_button = None
        self.textfield = None

        # save data
        # self.save_button = None  # TODO

        # display instances
        self.start_plot_button = None

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
        self.settings_button = None
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
        self.start_notification_button = QPushButton('Enable Notifications')
        self.start_notification_button.clicked.connect(self.enableNotification)

        # set number of values
        self.num_values_input = QSpinBox()
        self.num_values_input.setMinimum(1)
        self.num_values_input.setValue(1)

        self.confirm_values_button = QPushButton("Confirm number of values")
        self.confirm_values_button.clicked.connect(self.confirmValues)

        # initialize plotting
        self.start_plot_button = QPushButton('Plot')
        self.start_plot_button.clicked.connect(self.onStartPlotting)
        self.start_plot_button.setEnabled(False)

        # display decoded data
        self.textfield = QPlainTextEdit()
        self.textfield.setReadOnly(True)

        # plot settings
        self.settings_button = QPushButton("Plot Settings")
        self.settings_button.clicked.connect(self.onSettings)

        self.layout_.addWidget(self.start_notification_button)
        self.layout_.addWidget(self.num_values_input)
        self.layout_.addWidget(self.confirm_values_button)
        self.layout_.addWidget(self.textfield)
        self.layout_.addWidget(self.start_plot_button)
        self.layout_.addWidget(self.settings_button)

    @qasync.asyncSlot()
    async def onSettings(self):
        """Reveal plot settings window"""
        self.plot_setting_window = PlotSettingsWidget()
        self.plot_setting_window.gotPlotSetting.connect(self.onGetSettings)
        self.plot_setting_window.show()

    def onGetSettings(self, settings_str):
        """Update plot settings"""
        str_list = settings_str.split(",")
        self.title = str_list[0]
        self.xlabel = str_list[1]
        self.ylabel = str_list[2]
        self.ax.set_title(self.title)
        self.ax.set_xlabel(self.xlabel)
        self.ax.set_ylabel(self.ylabel)

    def onStartPlotting(self):
        self.start_plot_button.setEnabled(True)
        self.animation = FuncAnimation(self.fig, self.plotUpdate, interval=self.animate_interval,
                                       cache_frame_data=False, blit=True)
        self.canvas.draw_idle()

    @qasync.asyncSlot()
    async def enableNotification(self):
        """Enables notifications for the BLE characteristic."""
        self.start_notification_button.setEnabled(False)
        try:
            await self.bt_manager.start_notify(self.characteristic, self.decodeRoutine)
            self.isNotif = True
        except Exception as e:
            QMessageBox.information(self, "Info", f"Unable to start notification: {str(e)}")

    def decodeRoutine(self, characteristic, value):
        """
        Routine that Handles decoding of the BLE characteristic.

        :param characteristic: The characteristic that sent the notification.
        :param value: The value of the notification.
        """
        decoded_str = ""
        decoded_list = []
        try:
            decoded_str = value.decode("UTF-8")  # decode the data to string
            decoded_list = decoded_str.split(",")  # split the data with delimiter
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Unable to decode: {str(e)}")
            self.close()

        # Wrap the text to display to the textfield window
        display_text = str(decoded_str) + '\n' + self.textfield.toPlainText()
        self.textfield.setPlainText(display_text)

        if len(decoded_list) != len(self.data_queues):
            QMessageBox.warning(self, "Warning",
                                f"Length of received data ({len(decoded_list)}) \
                                does not match the expected number of values: {len(self.data_queues)}")
            return

        for idx, decoded_item in enumerate(decoded_list):
            try:
                decoded_item_float = float(decoded_item.replace('\x00', ''))
                self.data_queues[idx].append(decoded_item_float)
            except Exception as e:
                QMessageBox.warning(self, "Warning", f"Unable to decode: {e}")

    def confirmValues(self):
        num_values = self.num_values_input.value()

        self.data_queues = [deque([0] * 100, maxlen=100) for _ in range(num_values)]

        # Initialize plot panel
        if self.isFirstPlot:
            self.fig, self.axes = plt.subplots(nrows=len(self.data_queues),
                                               ncols=1)
            self.canvas = FigureCanvas(self.fig)
            self.title = "ADC"
            self.xlabel = "Sample"
            self.ylabel = "Value"
            self.axes[-1].set(xlabel=self.xlabel)

            self.lines = []
            for ax, data_queue in zip(self.axes, self.data_queues):
                line, = ax.plot(data_queue)
                self.lines.append(line)
                ax.set(ylabel=self.ylabel)

            self.layout_.addWidget(self.canvas)
            self.isFirstPlot = False

        else:
            for line, data_queue in zip(self.lines, self.data_queues):
                line.set_ydata(data_queue)

        self.start_plot_button.setEnabled(False)
        self.animation = FuncAnimation(self.fig, self.plotUpdate, interval=1, cache_frame_data=False)
        self.isPlotting = True

        self.start_plot_button.setEnabled(True)
        self.canvas.draw_idle()

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
