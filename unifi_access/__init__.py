"""
UniFi Access Python SDK

A comprehensive Python library for interacting with Ubiquiti's UniFi Access API.
Provides complete access control management for doors, users, visitors, and devices.
"""

from .client import UniFiAccessClient
from .websocket import UniFiAccessWebSocket
from .exceptions import (
    UniFiAccessError,
    AuthenticationError,
    ResourceNotFoundError,
    ValidationError,
    APIError,
    RateLimitError,
    PermissionError,
    ConnectionError,
    TimeoutError
)
from .models import (
    User,
    Visitor,
    AccessPolicy,
    Schedule,
    HolidayGroup,
    NFCCard,
    PINCode,
    TouchPass,
    Door,
    DoorGroup,
    Device,
    AccessEvent,
    SystemLog,
    CredentialType,
    UserRole,
    DeviceType
)

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
    "DeviceType"
]