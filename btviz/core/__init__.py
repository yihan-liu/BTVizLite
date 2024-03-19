# btviz/core/__init__.py
from typing import Awaitable, Callable, List, Union

from bleak import BleakScanner, BLEDevice, BleakClient
from bleak.backends.service import BleakGATTService, BleakGATTServiceCollection
from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.exc import BleakError


# noinspection PyAttributeOutsideInit
class BTManager:
    _instance = None  # Class variable to store the singleton instance

    def __new__(cls):
        """Override the __new__ method to create a singleton instance"""
        if cls._instance is None:
            # If no instance exists, create a new one
            cls._instance = super().__new__(cls)
            # Initialize the scanner and client variables
            cls._instance.scanner = BleakScanner()
            cls._instance.client = None
        return cls._instance  # return the singleton instance

    @classmethod
    def instance(cls):
        """Class method to provide access to the singleton instance"""
        if cls._instance is None:
            # If no instance exists, create a new one
            cls._instance = cls()
        return cls._instance  # Return the singleton instance

    async def scan_devices(self) -> List[BLEDevice]:
        devices = await self.scanner.discover()
        return devices

    async def connect_to_device(self, device: BLEDevice):
        self.client = BleakClient(device)
        try:
            await self.client.connect()
        except Exception as e:
            raise Exception(f"Could not connect to BLE device {device}: {str(e)}")

    async def disconnect_from_device(self):
        if self.client:
            await self.client.disconnect()
            self.client = None

    async def get_services(self) -> BleakGATTServiceCollection:
        if self.client:
            try:
                return self.client.services
            except BleakError as e:
                raise Exception(f"Service discovery has not been performed: {str(e)}")
        else:
            raise Exception("No device connected")

    async def get_characteristics(self, service: BleakGATTService) -> List[BleakGATTCharacteristic]:
        if self.client:
            return service.characteristics
        else:
            raise Exception("No device connected")

    async def start_notify(self, characteristic: BleakGATTCharacteristic,
                           callback: Callable[
                               [BleakGATTCharacteristic, bytearray], Union[None, Awaitable[None]]
                           ]):
        if self.client:
            await self.client.start_notify(characteristic, callback)
        else:
            raise Exception("No device connected")

    async def stop_notify(self, characteristic: BleakGATTCharacteristic):
        if self.client:
            await self.client.stop_notify(characteristic)
        else:
            raise Exception("No device connected")

    async def read_characteristic(self, characteristic: BleakGATTCharacteristic) -> bytearray:
        if self.client:
            return await self.client.read_gatt_char(characteristic)
        else:
            raise Exception("No device connected")
        