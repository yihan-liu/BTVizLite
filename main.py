# main.py
import sys
import asyncio
from PyQt5.QtWidgets import QApplication
import qasync
from btviz.scan_widget import ScanWidget


async def run_app():
    app = QApplication(sys.argv)
    event_loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(event_loop)
    ex = ScanWidget()
    ex.show()
    app_close_event = asyncio.Event()
    app.aboutToQuit.connect(app_close_event.set)
    with event_loop:
        event_loop.run_until_complete(app_close_event.wait())


def main():
    """
    Main function to execute the application.
    """
    asyncio.run(run_app())


if __name__ == '__main__':
    main()
