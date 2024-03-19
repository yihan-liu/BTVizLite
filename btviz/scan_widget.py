# scan_widget.py
from PyQt5.QtWidgets import (QWidget,
                             QVBoxLayout,
                             QPushButton,
                             QListWidget,
                             QLabel,
                             QMessageBox)
import qasync

from btviz.core import BTManager
from btviz.ui_utils import calculate_window
from .connect_widget import ConnectWidget


class ScanWidget(QWidget):
    """
    A widget for scanning BLE devices.
    """
    def __init__(self):
        """
        Initializes the scan widget.
        """
        super().__init__()

        # initialize the bluetooth manager,
        # the other windows will share this instance
        self.bt_manager = BTManager().instance()

        # peripheral devices
        self.devicesDict = {}
        self.isDeviceDiscovered = False

        # UI elements
        self.scanButton = None
        self.connectButton = None
        self.devicesList = None

        # new window to pop up
        self.connectServicesWindow = None

        # layout instance
        self.layout_ = None

        # start UI
        self.initUI()

    def initUI(self):
        """
        Initializes the user interface for the scan widget.
        """
        self.setWindowTitle('BTViz')
        window_width, window_height, x_pos, y_pos = calculate_window(scale_width=0.2, scale_height=0.7)
        self.setGeometry(x_pos, y_pos, window_width, window_height)

        self.scanButton = QPushButton('Scan for Devices', self)
        self.scanButton.clicked.connect(self.scanDevices)

        self.connectButton = QPushButton('Connect to Device', self)
        self.connectButton.clicked.connect(self.scanServices)

        self.devicesList = QListWidget(self)

        self.layout_ = QVBoxLayout(self)
        self.layout_.addWidget(self.scanButton)
        self.layout_.addWidget(QLabel('Device List'))
        self.layout_.addWidget(self.devicesList)
        self.layout_.addWidget(self.connectButton)

    @qasync.asyncSlot()
    async def scanDevices(self):
        """
        Scans for BLE devices and updates the UI with the results.
        """
        self.scanButton.setEnabled(False)
        devices = await self.bt_manager.scan_devices()

        for device in devices:
            self.devicesList.addItem(device.name)
            self.devicesDict[device.name] = device

        self.isDeviceDiscovered = True
        self.scanButton.setText('Clear All')
        self.scanButton.disconnect()
        self.scanButton.clicked.connect(self.clearAll)

        self.scanButton.setEnabled(True)
        self.connectButton.setEnabled(True)

    def scanServices(self):
        if self.devicesList.currentItem().text():
            device = self.devicesDict[self.devicesList.currentItem().text()]
            self.connectServicesWindow = ConnectWidget(device)
            self.connectServicesWindow.show()
        else:
            QMessageBox.warning(self, "Warning", "Select Valid Device")

    def clearAll(self):
        """
        Clears all discovered devices and resets the UI.
        """
        self.devicesList.clear()

        self.devicesDict = {}

        self.scanButton.setText('Scan for Devices')
        self.scanButton.disconnect()
        self.scanButton.clicked.connect(self.scanDevices)

        self.connectButton.setEnabled(False)
