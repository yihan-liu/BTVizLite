# btviz/core/__init__.py
from bleak import BleakScanner, BLEDevice, BleakClient
from bleak.backends.service import BleakGATTService, BleakGATTServiceCollection
from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.exc import BleakError
from typing import Callable, List, Optional, Union, Awaitable


class BTManager:
    def __init__(self):
        self.scanner: BleakScanner = BleakScanner()
        self.client: Optional[BleakClient] = None

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