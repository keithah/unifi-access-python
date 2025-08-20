"""
UniFi Access Python SDK

A comprehensive Python library for interacting with Ubiquiti's UniFi Access API.
Provides complete access control management for doors, users, visitors, and devices.
"""

from .client import UniFiAccessClient
from .exceptions import (
    APIError,
    AuthenticationError,
    ConnectionError,
    PermissionError,
    RateLimitError,
    ResourceNotFoundError,
    TimeoutError,
    UniFiAccessError,
    ValidationError,
)
from .models import (
    AccessEvent,
    AccessPolicy,
    CredentialType,
    Device,
    DeviceType,
    Door,
    DoorGroup,
    HolidayGroup,
    NFCCard,
    PINCode,
    Schedule,
    SystemLog,
    TouchPass,
    User,
    UserRole,
    Visitor,
)
from .websocket import UniFiAccessWebSocket

__version__ = "0.1.0"
__author__ = "Keith Hadley"
__email__ = "keith@hadm.net"

__all__ = [
    "UniFiAccessClient",
    "UniFiAccessWebSocket",
    "UniFiAccessError",
    "AuthenticationError",
    "ResourceNotFoundError",
    "ValidationError",
    "APIError",
    "RateLimitError",
    "PermissionError",
    "ConnectionError",
    "TimeoutError",
    "User",
    "Visitor",
    "AccessPolicy",
    "Schedule",
    "HolidayGroup",
    "NFCCard",
    "PINCode",
    "TouchPass",
    "Door",
    "DoorGroup",
    "Device",
    "AccessEvent",
    "SystemLog",
    "CredentialType",
    "UserRole",
    "DeviceType",
]
