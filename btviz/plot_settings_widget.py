# plot_settings_widget.py
from PyQt5.QtWidgets import (QWidget,
                             QPushButton,
                             QTextEdit,
                             QLabel,
                             QFormLayout)
from PyQt5.QtCore import pyqtSignal


class PlotSettingsWidget(QWidget):
    """
    A widget for setting plot titles and axis
    """
    gotPlotSetting = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        # UI instances
        self.titleText = QTextEdit()
        self.xAxisText = QTextEdit()
        self.yAxisText = QTextEdit()
        self.windowText = QTextEdit()
        self.saveButton = QPushButton("Save settings")

        # layout instance
        self.layout_ = QFormLayout(self)

        # start UI
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Plot Settings")

        self.titleText.setPlainText("Characteristic Value")
        self.xAxisText.setPlainText("Time (a.u.)")
        self.yAxisText.setPlainText("Value (a.u.)")
        self.windowText.setPlainText("50")
        self.saveButton.clicked.connect(self.onSave)

        self.layout_.addWidget(QLabel("Title Text"))
        self.layout_.addWidget(self.titleText)
        self.layout_.addWidget(QLabel("x Axis Text"))
        self.layout_.addWidget(self.xAxisText)
        self.layout_.addWidget(QLabel("y Axis Text"))
        self.layout_.addWidget(self.yAxisText)
        self.layout_.addWidget(QLabel("Animation Window Length"))
        self.layout_.addWidget(self.windowText)
        self.layout_.addWidget(self.saveButton)

    def onSave(self):
        ret_str = ','.join((self.titleText.toPlainText(),
                            self.xAxisText.toPlainText(),
                            self.yAxisText.toPlainText(),
                            self.windowText.toPlainText()))
        self.gotPlotSetting.emit(ret_str)
        self.close()
