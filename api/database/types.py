from typing import TypedDict, NewType
from datetime import datetime
from decimal import Decimal

DeviceId = NewType("DeviceId", int)
ReadingId = NewType("ReadingId", int)

class DeviceCreate(TypedDict):
    name: str
    api_key: str

class Device(DeviceCreate):
    id: DeviceId
    created_at: datetime

class ReadingCreate(TypedDict):
    device_id: DeviceId
    temp: Decimal
    humidity: Decimal
    pm10: Decimal
    gas: Decimal

class Reading(ReadingCreate):
    id: ReadingId
    created_at: datetime
