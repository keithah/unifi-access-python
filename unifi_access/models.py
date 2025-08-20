"""
UniFi Access Python SDK Data Models

Data models representing UniFi Access API entities including users, visitors,
access policies, schedules, credentials, doors, and devices.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class CredentialType(Enum):
    """Types of credentials supported by UniFi Access."""

    NFC_CARD = "nfc_card"
    PIN_CODE = "pin_code"
    TOUCH_PASS = "touch_pass"
    QR_CODE = "qr_code"


class UserRole(Enum):
    """User roles in the UniFi Access system."""

    ADMIN = "admin"
    USER = "user"
    VISITOR = "visitor"


class DeviceType(Enum):
    """Types of UniFi Access devices."""

    DOOR_READER = "door_reader"
    DOOR_LOCK = "door_lock"
    CONTROLLER = "controller"
    ACCESS_HUB = "access_hub"
    CAMERA = "camera"


@dataclass
class NFCCard:
    """NFC card credential."""

    id: str
    card_number: str
    facility_code: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class PINCode:
    """PIN code credential."""

    id: str
    pin: str
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class TouchPass:
    """Touch Pass credential (smartphone-based access)."""

    id: str
    device_id: str
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Schedule:
    """Access schedule definition."""

    id: str
    name: str
    description: Optional[str] = None
    time_ranges: List[Dict[str, Any]] = field(default_factory=list)
    days_of_week: List[int] = field(default_factory=list)  # 0=Sunday, 6=Saturday
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class HolidayGroup:
    """Holiday group for schedule exclusions."""

    id: str
    name: str
    description: Optional[str] = None
    holidays: List[Dict[str, Any]] = field(default_factory=list)
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class AccessPolicy:
    """Access policy defining permissions and schedules."""

    id: str
    name: str
    description: Optional[str] = None
    schedule_id: Optional[str] = None
    holiday_group_id: Optional[str] = None
    door_ids: List[str] = field(default_factory=list)
    door_group_ids: List[str] = field(default_factory=list)
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class User:
    """UniFi Access user."""

    id: str
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    role: UserRole = UserRole.USER
    access_policy_ids: List[str] = field(default_factory=list)
    nfc_cards: List[NFCCard] = field(default_factory=list)
    pin_codes: List[PINCode] = field(default_factory=list)
    touch_passes: List[TouchPass] = field(default_factory=list)
    is_active: bool = True
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"


@dataclass
class Visitor:
    """Temporary visitor with limited access."""

    id: str
    first_name: str
    last_name: str
    start_date: datetime
    end_date: datetime
    email: Optional[str] = None
    phone: Optional[str] = None
    access_policy_ids: List[str] = field(default_factory=list)
    nfc_cards: List[NFCCard] = field(default_factory=list)
    pin_codes: List[PINCode] = field(default_factory=list)
    sponsor_user_id: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def full_name(self) -> str:
        """Get visitor's full name."""
        return f"{self.first_name} {self.last_name}"

    @property
    def is_valid(self) -> bool:
        """Check if visitor access is currently valid."""
        from datetime import timezone

        now = datetime.now(timezone.utc).replace(
            tzinfo=None
        )  # Remove timezone for comparison
        return self.is_active and self.start_date <= now <= self.end_date


@dataclass
class Door:
    """Physical door controlled by UniFi Access."""

    id: str
    name: str
    device_id: str
    description: Optional[str] = None
    is_locked: bool = True
    is_online: bool = True
    battery_level: Optional[int] = None
    signal_strength: Optional[int] = None
    firmware_version: Optional[str] = None
    location: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class DoorGroup:
    """Group of doors for easier management."""

    id: str
    name: str
    description: Optional[str] = None
    door_ids: List[str] = field(default_factory=list)
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Device:
    """UniFi Access device (reader, lock, controller)."""

    id: str
    name: str
    type: DeviceType
    mac_address: str
    ip_address: Optional[str] = None
    firmware_version: Optional[str] = None
    is_online: bool = True
    battery_level: Optional[int] = None
    signal_strength: Optional[int] = None
    location: Optional[str] = None
    door_id: Optional[str] = None  # For door readers/locks
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class AccessEvent:
    """Access event log entry."""

    id: str
    timestamp: datetime
    event_type: str
    door_id: str
    device_id: str
    result: str  # "granted", "denied", etc.
    user_id: Optional[str] = None
    visitor_id: Optional[str] = None
    credential_type: Optional[CredentialType] = None
    credential_id: Optional[str] = None
    reason: Optional[str] = None
    ip_address: Optional[str] = None


@dataclass
class SystemLog:
    """System log entry."""

    id: str
    timestamp: datetime
    level: str  # "info", "warning", "error"
    category: str
    message: str
    details: Optional[Dict[str, Any]] = None
    device_id: Optional[str] = None
    user_id: Optional[str] = None
