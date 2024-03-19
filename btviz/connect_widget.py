# connect_widget.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QListWidget, QLabel, QMessageBox
import qasync

from btviz.core import BTManager
from btviz.ui_utils import calculate_window
from .display_widget import DisplayWidget


class ConnectWidget(QWidget):
    def __init__(self, device):
        super().__init__()

        self.bt_manager = None

        # containers
        self.device = device
        self.servicesDict = {}
        self.charDict = {}

        # connection flags
        self.isDeviceDiscovered = False
        self.isConnected = False
        self.isServiceDiscovered = False
        self.isCharDiscovered = False

        # UI elements
        self.serviceButton = None
        self.connectButton = None
        self.servicesList = None
        self.charList = None
        self.charDisplayWindow = None

        # layout instance
        self.layout_ = QVBoxLayout(self)

        # start UI
        self.initUI()
        self.scanServices()

    def initUI(self):
        self.setWindowTitle("Device Connect")
        windowWidth, windowHeight, xPos, yPos = calculate_window(scale_width=0.5, scale_height=0.7)
        self.setGeometry(xPos, yPos, windowWidth, windowHeight)

        self.serviceButton = QPushButton('Read Service', self)
        self.serviceButton.clicked.connect(self.scanChar)
        self.serviceButton.setEnabled(False)

        self.connectButton = QPushButton('Disconnect', self)
        self.connectButton.clicked.connect(self.disconnect)
        self.connectButton.setEnabled(True)

        self.servicesList = QListWidget(self)

        self.charList = QListWidget(self)

        self.layout_.addWidget(self.connectButton)
        self.layout_.addWidget(QLabel('Service List'))
        self.layout_.addWidget(self.servicesList)
        self.layout_.addWidget(self.serviceButton)
        self.layout_.addWidget(QLabel('Characteristic List'))
        self.layout_.addWidget(self.charList)

    @qasync.asyncSlot()
    async def disconnect(self):
        """
        Disconnects from the currently connected BLE device.
        """
        self.connectButton.setEnabled(False)
        if self.bt_manager:
            await self.bt_manager.disconnect_from_device()
        self.close()

    @qasync.asyncSlot()
    async def scanServices(self):
        """
        Scans for services of the connected BLE device and updates the UI.
        """
        self.connectButton.setEnabled(False)
        if self.device:
            try:
                await self.bt_manager.connect_to_device(self.device)
                services = await self.bt_manager.get_services()
                for service in services:
                    self.servicesList.addItem(str(service))
                    self.servicesDict[str(service)] = service
                    self.connectButton.setText('Disconnect')
                    self.connectButton.disconnect()
                    self.connectButton.clicked.connect(self.disconnect)
                    self.connectButton.setEnabled(True)

                    self.serviceButton.setEnabled(True)

                    self.charList.doubleClicked.connect(self.charMonitor)
            except Exception as e:
                QMessageBox.warning(self, "Warning", f"Unable to connect: {str(e)}")
                self.close()
        else:
            QMessageBox.warning(self, "Warning", "Unable to connect to the device.")
            self.close()

    @qasync.asyncSlot()
    async def scanChar(self):
        """
        Scans for characteristics of the selected service and updates the UI.
        """
        self.serviceButton.setEnabled(False)
        if self.servicesList.currentItem():
            service = self.servicesDict[self.servicesList.currentItem().text()]
            chars = await self.bt_manager.get_characteristics(service)
            for char in chars:
                self.charList.addItem(str(char.uuid))
                self.charDict[str(char.uuid)] = char
        else:
            QMessageBox.warning(self, "Warning", "Please select a valid characteristic.")

    @qasync.asyncSlot()
    async def charMonitor(self):
        """
        Opens a display widget for the selected characteristic to monitor its data.
        """
        m_char = self.charDict[self.charList.currentItem().text()]
        self.charDisplayWindow = DisplayWidget(m_char)
        self.charDisplayWindow.bt_manager = self.bt_manager  # set the bt_manager instance
        self.charDisplayWindow.show()

    @qasync.asyncClose
    async def closeEvent(self, event):
        if self.bt_manager:
            try:
                await self.bt_manager.disconnect_from_device()
            except Exception as e:
                QMessageBox.warning(self, "Warning", f"Could not disconnect: {str(e)}")
                pass
            self.bt_manager = None
