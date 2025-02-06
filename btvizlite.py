# btvizlite.py

from btvizlite_controller import BTVizLiteController

def main():
    port = 'COM27'
    baudrate = 9600
    controller = BTVizLiteController(port, baudrate)
    controller.run()

if __name__ == '__main__':
    main()