# display_widget.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QPlainTextEdit, QMessageBox
import qasync
import struct
from collections import deque
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

        self.config = None

        self.m_client = client
        self.m_char = char

        self.valueList = []
        self.valueQueue = deque(maxlen=50)

        self.isNotif = False
        self.isRead = False

        self.fig, self.ax = plt.subplots()
        self.line = None
        self.title = None
        self.xlabel = None
        self.ylabel = None
        self.canvas = None
        self.animateInterval = None
        self.animation = None
        self.isPlotting = False

        self.notifButton = None
        self.plotButton = None
        self.decodeMethodDropdown = None
        self.textfield = None
        self.intervalDropdown = None
        self.settingsButton = None
        
        self.window = None

        self.initUI()

    def initUI(self):
        """
        Initializes the user interface for the display widget.
        """
        self.notifButton = QPushButton('Enable Notifications')
        self.notifButton.clicked.connect(self.enableNotif)

        self.plotButton = QPushButton('Plot')
        self.plotButton.clicked.connect(self.plot)
        self.plotButton.setEnabled(False)

        self.setWindowTitle('Characteristic Reader')

        window_width, window_height, x_pos, y_pos = calculate_window(scale_width=0.5, scale_height=0.7)
        self.setGeometry(x_pos, y_pos, window_width, window_height)

        self.textfield = QPlainTextEdit()
        self.textfield.setReadOnly(True)

        layout = QVBoxLayout(self)
        layout.addWidget(self.notifButton)
        layout.addWidget(self.textfield)
        layout.addWidget(self.plotButton)

        self.line, = self.ax.plot(self.valueQueue)
        self.title = "ADC"
        self.xlabel = "Time (a.u.)"
        self.ylabel = "Value (a.u.)"
        self.canvas = FigureCanvas(self.fig)

        self.ax.set_title(self.title)
        self.ax.set_xlabel(self.xlabel)
        self.ax.set_ylabel(self.ylabel)

        layout.addWidget(self.canvas)

        self.settingsButton = QPushButton("Plot Settings")
        self.settingsButton.clicked.connect(self.onSettings)

        layout.addWidget(self.settingsButton)

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
        self.valueQueue = deque(maxlen=int(str_list[3]))
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
            decoded_value = value.decode("UTF-8")
            decoded_list = decoded_value.split(",")
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Unable to decode: {e}")
            self.close()

        text = str(decoded_value) + '\n' + self.textfield.toPlainText()
        self.textfield.setPlainText(text)
        if (self.isFirstTransactions):
            self.dataframe = []
            self._lines = []
            for i in range(len(decoded_list)):
                self.dataframe.append(deque(maxlen=100))

            self.isFirstTransactions = False
            self.plotButton.setEnabled(True)
            self.saveButton.setEnabled(True)

        for i in range(len(decoded_list)):
            try:
                item = float(decoded_list[i].replace('\x00', ''))
            except:
                QMessageBox.warning(self, "Warning", "Unable to decode")
            self.dataframe[i].append(item)

    def plotUpdate(self, frame):
        """
        Updates the plot with new data.

        :param frame: The current frame of the animation (unused).
        """
        if self.isPlotting:
            # Update plot data
            self.line.set_xdata(range(len(self.valueQueue)))  # TODO: this should be related to real-time
            self.line.set_ydata(self.valueQueue)
            self.ax.relim()
            self.ax.autoscale_view()

            # Set line color
            self.line.set_color('r')
            return self.line,

    def plot(self):
        """
        Starts plotting the BLE characteristic data in real-time.
        """
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
