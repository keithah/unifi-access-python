"""
UniFi Access Python SDK Client

Main client class for interacting with the UniFi Access API. Handles authentication,
request/response processing, and provides methods for all API endpoints.
"""

import asyncio
import json
import logging
import ssl
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp

try:
    import urllib3
except ImportError:
    urllib3 = None

from .exceptions import (
    APIError,
    AuthenticationError,
    ConnectionError,
    PermissionError,
    RateLimitError,
    ResourceNotFoundError,
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

# Disable SSL warnings for self-signed certificates
if urllib3 is not None:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


class UniFiAccessClient:
    """
    Client for interacting with the UniFi Access API.

    Handles authentication, request/response processing, and provides
    methods for managing users, visitors, doors, devices, and access policies.
    """

    def __init__(
        self,
        host: str,
        token: str,
        port: int = 12445,
        verify_ssl: bool = False,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        Initialize the UniFi Access client.

        Args:
            host: UniFi Access server hostname or IP address
            token: API token for authentication
            port: API port (default: 12445)
            verify_ssl: Whether to verify SSL certificates (default: False for self-signed)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            retry_delay: Delay between retries in seconds
        """
        self.host = host.rstrip("/")
        self.token = token
        self.port = port
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        self.base_url = f"https://{self.host}:{self.port}/api/v1/developer"
        self.token_expires: Optional[datetime] = None
        self.session: Optional[aiohttp.ClientSession] = None

        # Create SSL context for self-signed certificates
        self.ssl_context = ssl.create_default_context()
        if not verify_ssl:
            self.ssl_context.check_hostname = False
            self.ssl_context.verify_mode = ssl.CERT_NONE

    async def __aenter__(self) -> "UniFiAccessClient":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.disconnect()

    async def connect(self) -> None:
        """Establish connection and set up authentication."""
        connector = aiohttp.TCPConnector(ssl=self.ssl_context)
        timeout = aiohttp.ClientTimeout(total=self.timeout)

        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.token}",
            },
        )

    async def disconnect(self) -> None:
        """Close the connection."""
        if self.session:
            await self.session.close()
            self.session = None

    async def _ensure_authenticated(self) -> None:
        """Ensure we have a valid authentication token."""
        if not self.token:
            raise AuthenticationError("API token not provided")

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Make an authenticated request to the API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without base URL)
            data: Request body data
            params: Query parameters

        Returns:
            Response data as dictionary

        Raises:
            Various UniFiAccessError subclasses based on response status
        """
        await self._ensure_authenticated()

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        for attempt in range(self.max_retries + 1):
            try:
                if self.session is None:
                    raise ConnectionError("Session is None - call connect() first")

                async with self.session.request(
                    method=method, url=url, json=data, params=params
                ) as response:
                    response_text = await response.text()

                    # Try to parse JSON response
                    try:
                        response_data = (
                            json.loads(response_text) if response_text else {}
                        )
                    except json.JSONDecodeError:
                        response_data = {"message": response_text}

                    # Handle different status codes
                    if response.status == 200 or response.status == 201:
                        return response_data
                    elif response.status == 400:
                        raise ValidationError(
                            response_data.get("message", "Validation error"),
                            status_code=response.status,
                            response_data=response_data,
                        )
                    elif response.status == 401:
                        raise AuthenticationError(
                            response_data.get(
                                "message", "Authentication failed - invalid token"
                            ),
                            status_code=response.status,
                            response_data=response_data,
                        )
                    elif response.status == 403:
                        raise PermissionError(
                            response_data.get("message", "Permission denied"),
                            status_code=response.status,
                            response_data=response_data,
                        )
                    elif response.status == 404:
                        raise ResourceNotFoundError(
                            response_data.get("message", "Resource not found"),
                            status_code=response.status,
                            response_data=response_data,
                        )
                    elif response.status == 429:
                        raise RateLimitError(
                            response_data.get("message", "Rate limit exceeded"),
                            status_code=response.status,
                            response_data=response_data,
                        )
                    else:
                        raise APIError(
                            response_data.get(
                                "message", f"API error: {response.status}"
                            ),
                            status_code=response.status,
                            response_data=response_data,
                        )

            except aiohttp.ClientError as e:
                if attempt == self.max_retries:
                    raise ConnectionError(
                        f"Request failed after {self.max_retries + 1} attempts: {e}"
                    )

                # Wait before retrying
                await asyncio.sleep(self.retry_delay * (2**attempt))

        # This shouldn't be reached, but just in case
        raise APIError("Maximum retries exceeded")

    # User Management Methods

    async def get_users(self, limit: int = 100, offset: int = 0) -> List[User]:
        """
        Get list of users.

        Args:
            limit: Maximum number of users to return
            offset: Number of users to skip

        Returns:
            List of User objects
        """
        params = {"limit": limit, "offset": offset}
        response = await self._request("GET", "/users", params=params)

        users = []
        for user_data in response.get("data", []):
            user = self._parse_user(user_data)
            users.append(user)

        return users

    async def get_user(self, user_id: str) -> User:
        """
        Get a specific user by ID.

        Args:
            user_id: User ID

        Returns:
            User object
        """
        response = await self._request("GET", f"/users/{user_id}")
        return self._parse_user(response["data"])

    async def create_user(
        self,
        first_name: str,
        last_name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        role: UserRole = UserRole.USER,
        access_policy_ids: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> User:
        """
        Create a new user.

        Args:
            first_name: User's first name
            last_name: User's last name
            email: User's email address
            phone: User's phone number
            role: User role
            access_policy_ids: List of access policy IDs
            start_date: Access start date
            end_date: Access end date

        Returns:
            Created User object
        """
        data: Dict[str, Any] = {
            "first_name": first_name,
            "last_name": last_name,
            "role": role.value,
            "is_active": True,
        }

        if email:
            data["email"] = email
        if phone:
            data["phone"] = phone
        if access_policy_ids:
            data["access_policy_ids"] = access_policy_ids
        if start_date:
            data["start_date"] = start_date.isoformat()
        if end_date:
            data["end_date"] = end_date.isoformat()

        response = await self._request("POST", "/users", data=data)
        return self._parse_user(response["data"])

    def _parse_user(self, data: Dict[str, Any]) -> User:
        """Parse user data from API response."""
        return User(
            id=data["id"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            email=data.get("email"),
            phone=data.get("phone"),
            role=UserRole(data.get("role", "user")),
            access_policy_ids=data.get("access_policy_ids", []),
            nfc_cards=[
                self._parse_nfc_card(card) for card in data.get("nfc_cards", [])
            ],
            pin_codes=[self._parse_pin_code(pin) for pin in data.get("pin_codes", [])],
            touch_passes=[
                self._parse_touch_pass(tp) for tp in data.get("touch_passes", [])
            ],
            is_active=data.get("is_active", True),
            start_date=self._parse_datetime(data.get("start_date")),
            end_date=self._parse_datetime(data.get("end_date")),
            created_at=self._parse_datetime(data.get("created_at")),
            updated_at=self._parse_datetime(data.get("updated_at")),
        )

    def _parse_nfc_card(self, data: Dict[str, Any]) -> NFCCard:
        """Parse NFC card data from API response."""
        return NFCCard(
            id=data["id"],
            card_number=data["card_number"],
            facility_code=data.get("facility_code"),
            is_active=data.get("is_active", True),
            created_at=self._parse_datetime(data.get("created_at")),
            updated_at=self._parse_datetime(data.get("updated_at")),
        )

    def _parse_pin_code(self, data: Dict[str, Any]) -> PINCode:
        """Parse PIN code data from API response."""
        return PINCode(
            id=data["id"],
            pin=data["pin"],
            is_active=data.get("is_active", True),
            created_at=self._parse_datetime(data.get("created_at")),
            updated_at=self._parse_datetime(data.get("updated_at")),
        )

    def _parse_touch_pass(self, data: Dict[str, Any]) -> TouchPass:
        """Parse Touch Pass data from API response."""
        return TouchPass(
            id=data["id"],
            device_id=data["device_id"],
            is_active=data.get("is_active", True),
            created_at=self._parse_datetime(data.get("created_at")),
            updated_at=self._parse_datetime(data.get("updated_at")),
        )

    def _parse_datetime(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse ISO datetime string to datetime object."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None

    # Visitor Management Methods

    async def get_visitors(self, limit: int = 100, offset: int = 0) -> List[Visitor]:
        """
        Get list of visitors.

        Args:
            limit: Maximum number of visitors to return
            offset: Number of visitors to skip

        Returns:
            List of Visitor objects
        """
        params = {"limit": limit, "offset": offset}
        response = await self._request("GET", "/visitors", params=params)

        visitors = []
        for visitor_data in response.get("data", []):
            visitor = self._parse_visitor(visitor_data)
            visitors.append(visitor)

        return visitors

    async def get_visitor(self, visitor_id: str) -> Visitor:
        """
        Get a specific visitor by ID.

        Args:
            visitor_id: Visitor ID

        Returns:
            Visitor object
        """
        response = await self._request("GET", f"/visitors/{visitor_id}")
        return self._parse_visitor(response["data"])

    async def create_visitor(
        self,
        first_name: str,
        last_name: str,
        start_date: datetime,
        end_date: datetime,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        access_policy_ids: Optional[List[str]] = None,
        sponsor_user_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Visitor:
        """
        Create a new visitor with temporary access.

        Args:
            first_name: Visitor's first name
            last_name: Visitor's last name
            start_date: Access start date and time
            end_date: Access end date and time
            email: Visitor's email address
            phone: Visitor's phone number
            access_policy_ids: List of access policy IDs
            sponsor_user_id: ID of sponsoring user
            notes: Additional notes about the visitor

        Returns:
            Created Visitor object
        """
        data = {
            "first_name": first_name,
            "last_name": last_name,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "is_active": True,
        }

        if email:
            data["email"] = email
        if phone:
            data["phone"] = phone
        if access_policy_ids:
            data["access_policy_ids"] = access_policy_ids
        if sponsor_user_id:
            data["sponsor_user_id"] = sponsor_user_id
        if notes:
            data["notes"] = notes

        response = await self._request("POST", "/visitors", data=data)
        return self._parse_visitor(response["data"])

    async def update_visitor(
        self,
        visitor_id: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        access_policy_ids: Optional[List[str]] = None,
        sponsor_user_id: Optional[str] = None,
        notes: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Visitor:
        """
        Update an existing visitor.

        Args:
            visitor_id: Visitor ID to update
            first_name: Updated first name
            last_name: Updated last name
            email: Updated email address
            phone: Updated phone number
            start_date: Updated access start date
            end_date: Updated access end date
            access_policy_ids: Updated access policy IDs
            sponsor_user_id: Updated sponsor user ID
            notes: Updated notes
            is_active: Updated active status

        Returns:
            Updated Visitor object
        """
        data: Dict[str, Any] = {}

        if first_name is not None:
            data["first_name"] = first_name
        if last_name is not None:
            data["last_name"] = last_name
        if email is not None:
            data["email"] = email
        if phone is not None:
            data["phone"] = phone
        if start_date is not None:
            data["start_date"] = start_date.isoformat()
        if end_date is not None:
            data["end_date"] = end_date.isoformat()
        if access_policy_ids is not None:
            data["access_policy_ids"] = access_policy_ids
        if sponsor_user_id is not None:
            data["sponsor_user_id"] = sponsor_user_id
        if notes is not None:
            data["notes"] = notes
        if is_active is not None:
            data["is_active"] = is_active

        response = await self._request("PUT", f"/visitors/{visitor_id}", data=data)
        return self._parse_visitor(response["data"])

    async def delete_visitor(self, visitor_id: str) -> bool:
        """
        Delete a visitor.

        Args:
            visitor_id: Visitor ID to delete

        Returns:
            True if successful
        """
        await self._request("DELETE", f"/visitors/{visitor_id}")
        return True

    async def add_visitor_pin(self, visitor_id: str, pin: str) -> bool:
        """
        Add/update a PIN code for a visitor.

        Args:
            visitor_id: Visitor ID
            pin: PIN code (4-8 digits)

        Returns:
            True if successful
        """
        data = {"pin_code": pin}
        response = await self._request(
            "PUT", f"/visitors/{visitor_id}/pin_codes", data=data
        )
        return response.get("code") == "SUCCESS"

    async def add_visitor_nfc_card(
        self, visitor_id: str, card_number: str, facility_code: Optional[str] = None
    ) -> NFCCard:
        """
        Add an NFC card to a visitor.

        Args:
            visitor_id: Visitor ID
            card_number: NFC card number
            facility_code: Optional facility code

        Returns:
            Created NFCCard object
        """
        data = {"card_number": card_number}
        if facility_code:
            data["facility_code"] = facility_code

        response = await self._request(
            "POST", f"/visitors/{visitor_id}/nfc-cards", data=data
        )
        return self._parse_nfc_card(response["data"])

    def _parse_visitor(self, data: Dict[str, Any]) -> Visitor:
        """Parse visitor data from API response."""
        # Parse PIN code from the API structure
        pin_codes = []
        if data.get("pin_code") and isinstance(data["pin_code"], dict):
            pin_codes = [
                PINCode(
                    id=data.get("id", ""),
                    pin="****",  # PIN is not returned for security
                    is_active=True,
                    created_at=None,
                    updated_at=None,
                )
            ]

        # Parse NFC cards
        nfc_cards = [self._parse_nfc_card(card) for card in data.get("nfc_cards", [])]

        # Parse timestamps (API uses Unix timestamps)
        start_date = (
            datetime.fromtimestamp(data["start_time"])
            if data.get("start_time")
            else datetime.utcnow()
        )
        end_date = (
            datetime.fromtimestamp(data["end_time"])
            if data.get("end_time")
            else datetime.utcnow()
        )
        created_at = (
            datetime.fromtimestamp(data["create_time"])
            if data.get("create_time")
            else None
        )

        # Extract access policy IDs from resources
        access_policy_ids = []
        for resource in data.get("resources", []):
            if resource.get("type") == "door_group":
                access_policy_ids.append(resource.get("id"))

        return Visitor(
            id=data["id"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            email=data.get("email") or None,
            phone=data.get("mobile_phone") or None,
            access_policy_ids=access_policy_ids,
            nfc_cards=nfc_cards,
            pin_codes=pin_codes,
            start_date=start_date,
            end_date=end_date,
            sponsor_user_id=data.get("inviter_id") or None,
            notes=data.get("remarks") or None,
            is_active=data.get("status") in ["UPCOMING", "VISITING"],
            created_at=created_at,
            updated_at=None,  # Not provided in API
        )

    # Door and Device Management Methods

    async def get_doors(self, limit: int = 100, offset: int = 0) -> List[Door]:
        """
        Get list of doors.

        Args:
            limit: Maximum number of doors to return
            offset: Number of doors to skip

        Returns:
            List of Door objects
        """
        params = {"limit": limit, "offset": offset}
        response = await self._request("GET", "/doors", params=params)

        doors = []
        for door_data in response.get("data", []):
            door = self._parse_door(door_data)
            doors.append(door)

        return doors

    async def get_door(self, door_id: str) -> Door:
        """
        Get a specific door by ID.

        Args:
            door_id: Door ID

        Returns:
            Door object
        """
        response = await self._request("GET", f"/doors/{door_id}")
        return self._parse_door(response["data"])

    async def unlock_door(self, door_id: str, duration: int = 10) -> bool:
        """
        Unlock a door for a specified duration.

        Note: Door unlock/lock functionality is not available in the developer API.
        This method is provided for API compatibility but will raise an exception.

        Args:
            door_id: Door ID to unlock
            duration: Unlock duration in seconds (default: 10)

        Returns:
            True if successful

        Raises:
            ResourceNotFoundError: Door unlock endpoint not available in developer API
        """
        raise ResourceNotFoundError(
            "Door unlock functionality not available in developer API"
        )

    async def lock_door(self, door_id: str) -> bool:
        """
        Lock a door immediately.

        Note: Door unlock/lock functionality is not available in the developer API.
        This method is provided for API compatibility but will raise an exception.

        Args:
            door_id: Door ID to lock

        Returns:
            True if successful

        Raises:
            ResourceNotFoundError: Door lock endpoint not available in developer API
        """
        raise ResourceNotFoundError(
            "Door lock functionality not available in developer API"
        )

    async def get_devices(self, limit: int = 100, offset: int = 0) -> List[Device]:
        """
        Get list of devices.

        Args:
            limit: Maximum number of devices to return
            offset: Number of devices to skip

        Returns:
            List of Device objects
        """
        params = {"limit": limit, "offset": offset}
        response = await self._request("GET", "/devices", params=params)

        devices = []
        # Handle nested array structure: data contains array of arrays
        device_arrays = response.get("data", [])
        for device_array in device_arrays:
            if isinstance(device_array, list):
                for device_data in device_array:
                    device = self._parse_device(device_data)
                    devices.append(device)
            else:
                # In case the structure changes to flat array
                device = self._parse_device(device_array)
                devices.append(device)

        return devices

    async def get_device(self, device_id: str) -> Device:
        """
        Get a specific device by ID.

        Args:
            device_id: Device ID

        Returns:
            Device object
        """
        response = await self._request("GET", f"/devices/{device_id}")
        return self._parse_device(response["data"])

    async def get_door_groups(
        self, limit: int = 100, offset: int = 0
    ) -> List[DoorGroup]:
        """
        Get list of door groups.

        Args:
            limit: Maximum number of door groups to return
            offset: Number of door groups to skip

        Returns:
            List of DoorGroup objects
        """
        params = {"limit": limit, "offset": offset}
        response = await self._request("GET", "/door_groups", params=params)

        door_groups = []
        for group_data in response.get("data", []):
            door_group = self._parse_door_group(group_data)
            door_groups.append(door_group)

        return door_groups

    async def create_door_group(
        self,
        name: str,
        description: Optional[str] = None,
        door_ids: Optional[List[str]] = None,
    ) -> DoorGroup:
        """
        Create a new door group.

        Args:
            name: Door group name
            description: Optional description
            door_ids: List of door IDs to include

        Returns:
            Created DoorGroup object
        """
        data = {"name": name, "is_active": True}

        if description:
            data["description"] = description
        if door_ids:
            data["door_ids"] = door_ids

        response = await self._request("POST", "/door_groups", data=data)
        return self._parse_door_group(response["data"])

    def _parse_door(self, data: Dict[str, Any]) -> Door:
        """Parse door data from API response."""
        return Door(
            id=data["id"],
            name=data["name"],
            description=data.get("full_name"),  # Use full_name as description
            device_id=data.get("floor_id")
            or "",  # floor_id is closest to device_id concept
            is_locked=data.get("door_lock_relay_status") == "lock",
            is_online=data.get("is_bind_hub", True),  # If bound to hub, consider online
            battery_level=None,  # Not provided in API
            signal_strength=None,  # Not provided in API
            firmware_version=None,  # Not provided in API
            location=data.get("full_name"),  # Use full name as location description
            created_at=None,  # Not provided in API
            updated_at=None,  # Not provided in API
        )

    def _parse_device(self, data: Dict[str, Any]) -> Device:
        """Parse device data from API response."""
        # Map API device types to our enum
        device_type = DeviceType.DOOR_READER  # Default
        api_type = data.get("type", "")

        if "UAH" in api_type:
            device_type = DeviceType.ACCESS_HUB
        elif "UA-G2" in api_type:
            device_type = DeviceType.DOOR_READER
        elif "CAMERA" in api_type:
            device_type = DeviceType.CAMERA

        return Device(
            id=data["id"],
            name=data.get("alias") or data["name"],  # Prefer alias over name
            type=device_type,
            mac_address=data.get(
                "id", ""
            ),  # Use device ID as MAC since real MAC not provided
            ip_address=None,  # Not provided in API
            firmware_version=None,  # Not provided in API
            is_online=True,  # Assume online if returned in API
            battery_level=None,  # Not provided in API
            signal_strength=None,  # Not provided in API
            location=data.get("location_id"),  # Use location_id
            door_id=data.get(
                "location_id"
            ),  # For door devices, location_id is the door
            created_at=None,  # Not provided in API
            updated_at=None,  # Not provided in API
        )

    def _parse_door_group(self, data: Dict[str, Any]) -> DoorGroup:
        """Parse door group data from API response."""
        # Extract door IDs from resources
        door_ids = []
        for resource in data.get("resources", []):
            if resource.get("type") == "door":
                door_ids.append(resource.get("id"))

        return DoorGroup(
            id=data["id"],
            name=data["name"],
            description=f"{data.get('type', '')} group".strip(),  # Use type as description
            door_ids=door_ids,
            is_active=True,  # Assume active if returned
            created_at=None,  # Not provided in API
            updated_at=None,  # Not provided in API
        )

    # Access Policy and Schedule Management Methods

    async def get_access_policies(
        self, limit: int = 100, offset: int = 0
    ) -> List[AccessPolicy]:
        """
        Get list of access policies.

        Args:
            limit: Maximum number of policies to return
            offset: Number of policies to skip

        Returns:
            List of AccessPolicy objects
        """
        params = {"limit": limit, "offset": offset}
        response = await self._request("GET", "/access_policies", params=params)

        policies = []
        for policy_data in response.get("data", []):
            policy = self._parse_access_policy(policy_data)
            policies.append(policy)

        return policies

    async def get_access_policy(self, policy_id: str) -> AccessPolicy:
        """
        Get a specific access policy by ID.

        Args:
            policy_id: Access policy ID

        Returns:
            AccessPolicy object
        """
        response = await self._request("GET", f"/access-policies/{policy_id}")
        return self._parse_access_policy(response["data"])

    async def create_access_policy(
        self,
        name: str,
        description: Optional[str] = None,
        schedule_id: Optional[str] = None,
        holiday_group_id: Optional[str] = None,
        door_ids: Optional[List[str]] = None,
        door_group_ids: Optional[List[str]] = None,
    ) -> AccessPolicy:
        """
        Create a new access policy.

        Args:
            name: Policy name
            description: Optional description
            schedule_id: Schedule to apply
            holiday_group_id: Holiday group for exclusions
            door_ids: List of door IDs
            door_group_ids: List of door group IDs

        Returns:
            Created AccessPolicy object
        """
        data = {"name": name, "is_active": True}

        if description:
            data["description"] = description
        if schedule_id:
            data["schedule_id"] = schedule_id
        if holiday_group_id:
            data["holiday_group_id"] = holiday_group_id
        if door_ids:
            data["door_ids"] = door_ids
        if door_group_ids:
            data["door_group_ids"] = door_group_ids

        response = await self._request("POST", "/access_policies", data=data)
        return self._parse_access_policy(response["data"])

    async def get_schedules(self, limit: int = 100, offset: int = 0) -> List[Schedule]:
        """
        Get list of schedules.

        Note: Schedules endpoint is not available in the developer API.
        This method is provided for API compatibility but will raise an exception.

        Args:
            limit: Maximum number of schedules to return
            offset: Number of schedules to skip

        Returns:
            List of Schedule objects

        Raises:
            ResourceNotFoundError: Schedules endpoint not available in developer API
        """
        raise ResourceNotFoundError("Schedules endpoint not available in developer API")

    async def create_schedule(
        self,
        name: str,
        description: Optional[str] = None,
        time_ranges: Optional[List[Dict[str, Any]]] = None,
        days_of_week: Optional[List[int]] = None,
    ) -> Schedule:
        """
        Create a new schedule.

        Note: Schedules endpoint is not available in the developer API.
        This method is provided for API compatibility but will raise an exception.

        Args:
            name: Schedule name
            description: Optional description
            time_ranges: List of time range definitions
            days_of_week: Days of week (0=Sunday, 6=Saturday)

        Returns:
            Created Schedule object

        Raises:
            ResourceNotFoundError: Schedules endpoint not available in developer API
        """
        raise ResourceNotFoundError("Schedules endpoint not available in developer API")

    async def get_holiday_groups(
        self, limit: int = 100, offset: int = 0
    ) -> List[HolidayGroup]:
        """
        Get list of holiday groups.

        Note: Holiday groups endpoint is not available in the developer API.
        This method is provided for API compatibility but will raise an exception.

        Args:
            limit: Maximum number of holiday groups to return
            offset: Number of holiday groups to skip

        Returns:
            List of HolidayGroup objects

        Raises:
            ResourceNotFoundError: Holiday groups endpoint not available in developer API
        """
        raise ResourceNotFoundError(
            "Holiday groups endpoint not available in developer API"
        )

    def _parse_access_policy(self, data: Dict[str, Any]) -> AccessPolicy:
        """Parse access policy data from API response."""
        # Extract door group IDs from resources
        door_group_ids = []
        door_ids = []

        for resource in data.get("resources", []):
            if resource.get("type") == "door_group":
                door_group_ids.append(resource.get("id"))
            elif resource.get("type") == "door":
                door_ids.append(resource.get("id"))

        return AccessPolicy(
            id=data["id"],
            name=data["name"],
            description=None,  # Not provided in API
            schedule_id=data.get("schedule_id"),
            holiday_group_id=None,  # Not provided in API
            door_ids=door_ids,
            door_group_ids=door_group_ids,
            is_active=True,  # Assume active if returned
            created_at=None,  # Not provided in API
            updated_at=None,  # Not provided in API
        )

    def _parse_schedule(self, data: Dict[str, Any]) -> Schedule:
        """Parse schedule data from API response."""
        return Schedule(
            id=data["id"],
            name=data["name"],
            description=data.get("description"),
            time_ranges=data.get("time_ranges", []),
            days_of_week=data.get("days_of_week", []),
            is_active=data.get("is_active", True),
            created_at=self._parse_datetime(data.get("created_at")),
            updated_at=self._parse_datetime(data.get("updated_at")),
        )

    def _parse_holiday_group(self, data: Dict[str, Any]) -> HolidayGroup:
        """Parse holiday group data from API response."""
        return HolidayGroup(
            id=data["id"],
            name=data["name"],
            description=data.get("description"),
            holidays=data.get("holidays", []),
            is_active=data.get("is_active", True),
            created_at=self._parse_datetime(data.get("created_at")),
            updated_at=self._parse_datetime(data.get("updated_at")),
        )

    # System Logs and Access Events Methods

    async def get_access_events(
        self,
        limit: int = 100,
        offset: int = 0,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        door_id: Optional[str] = None,
        user_id: Optional[str] = None,
        visitor_id: Optional[str] = None,
    ) -> List[AccessEvent]:
        """
        Get access events log.

        Note: Access events endpoint is not available in the developer API.
        This method is provided for API compatibility but will raise an exception.

        Args:
            limit: Maximum number of events to return
            offset: Number of events to skip
            start_time: Filter events after this time
            end_time: Filter events before this time
            door_id: Filter by door ID
            user_id: Filter by user ID
            visitor_id: Filter by visitor ID

        Returns:
            List of AccessEvent objects

        Raises:
            ResourceNotFoundError: Access events endpoint not available in developer API
        """
        raise ResourceNotFoundError(
            "Access events endpoint not available in developer API"
        )

    async def get_system_logs(
        self,
        limit: int = 100,
        offset: int = 0,
        level: Optional[str] = None,
        category: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[SystemLog]:
        """
        Get system logs.

        Note: System logs endpoint is not available in the developer API.
        This method is provided for API compatibility but will raise an exception.

        Args:
            limit: Maximum number of logs to return
            offset: Number of logs to skip
            level: Filter by log level (info, warning, error)
            category: Filter by log category
            start_time: Filter logs after this time
            end_time: Filter logs before this time

        Returns:
            List of SystemLog objects

        Raises:
            ResourceNotFoundError: System logs endpoint not available in developer API
        """
        raise ResourceNotFoundError(
            "System logs endpoint not available in developer API"
        )

    def _parse_access_event(self, data: Dict[str, Any]) -> AccessEvent:
        """Parse access event data from API response."""
        credential_type = None
        if data.get("credential_type"):
            try:
                credential_type = CredentialType(data["credential_type"])
            except ValueError:
                pass

        return AccessEvent(
            id=data["id"],
            timestamp=self._parse_datetime(data["timestamp"]) or datetime.utcnow(),
            event_type=data["event_type"],
            user_id=data.get("user_id"),
            visitor_id=data.get("visitor_id"),
            door_id=data["door_id"],
            device_id=data["device_id"],
            credential_type=credential_type,
            credential_id=data.get("credential_id"),
            result=data["result"],
            reason=data.get("reason"),
            ip_address=data.get("ip_address"),
        )

    def _parse_system_log(self, data: Dict[str, Any]) -> SystemLog:
        """Parse system log data from API response."""
        return SystemLog(
            id=data["id"],
            timestamp=self._parse_datetime(data["timestamp"]) or datetime.utcnow(),
            level=data["level"],
            category=data["category"],
            message=data["message"],
            details=data.get("details"),
            device_id=data.get("device_id"),
            user_id=data.get("user_id"),
        )

    # WebSocket Methods

    def create_websocket_client(self) -> UniFiAccessWebSocket:
        """
        Create a WebSocket client for real-time events.

        Note: WebSocket functionality is not available in the developer API.
        This method is provided for API compatibility but will raise an exception.

        Returns:
            UniFiAccessWebSocket instance

        Raises:
            ResourceNotFoundError: WebSocket endpoint not available in developer API
        """
        raise ResourceNotFoundError(
            "WebSocket functionality not available in developer API"
        )
