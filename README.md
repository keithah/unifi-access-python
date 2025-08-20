# UniFi Access Python SDK

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A comprehensive Python SDK for the UniFi Access API, providing easy-to-use interfaces for managing visitors, doors, devices, and access policies in your UniFi Access system.

## 🚀 Features

- **Complete API Coverage**: Full support for all available UniFi Access Developer API endpoints
- **Async/Await Support**: Built with modern Python async patterns for high performance
- **Type Hints**: Full type annotations for better IDE support and code reliability
- **Comprehensive Models**: Rich data models for all UniFi Access entities
- **Error Handling**: Detailed exception handling with specific error types
- **Token Authentication**: Secure Bearer token authentication
- **SSL Support**: Built-in support for self-signed certificates
- **Production Ready**: Thoroughly tested and validated against real UniFi Access systems

## 📋 Supported Operations

### ✅ Working Features
- **👥 Visitors**: Complete CRUD operations, PIN management
- **🚪 Doors**: Status retrieval, information queries  
- **📱 Devices**: Discovery, status monitoring (Access Hubs, Door Readers)
- **🔐 Access Policies**: Policy management, door group associations
- **🏢 Door Groups**: Group management, door assignments

### ⚠️ API Limitations
- **Users**: Requires elevated permissions (not available with standard developer tokens)
- **Door Control**: Unlock/lock operations not available in developer API
- **Real-time Events**: WebSocket functionality not available in developer API
- **Schedules & Logs**: Advanced scheduling and logging not available in developer API

## 🛠️ Installation

```bash
pip install unifi-access-python
```

### Development Installation

```bash
git clone https://github.com/keithah/unifi-access-python.git
cd unifi-access-python
pip install -e .
```

## 🔧 Quick Start

### Basic Usage

```python
import asyncio
from unifi_access import UniFiAccessClient

async def main():
    # Initialize the client
    async with UniFiAccessClient(
        host="your-unifi-access-host.local",
        token="your-api-token",
        port=12445,
        verify_ssl=False  # For self-signed certificates
    ) as client:
        
        # Get all visitors
        visitors = await client.get_visitors()
        print(f"Found {len(visitors)} visitors")
        
        # Get all doors
        doors = await client.get_doors()
        for door in doors:
            print(f"Door: {door.name} - Locked: {door.is_locked}")
        
        # Get all devices
        devices = await client.get_devices()
        for device in devices:
            print(f"Device: {device.name} ({device.type.value})")

if __name__ == "__main__":
    asyncio.run(main())
```

### Visitor Management

```python
from datetime import datetime, timedelta

async def manage_visitors():
    async with UniFiAccessClient(host="...", token="...") as client:
        
        # Create a new visitor
        start_date = datetime.now()
        end_date = start_date + timedelta(days=7)
        
        visitor = await client.create_visitor(
            first_name="John",
            last_name="Doe",
            start_date=start_date,
            end_date=end_date,
            phone="555-123-4567",
            email="john.doe@example.com"
        )
        
        print(f"Created visitor: {visitor.id}")
        
        # Assign a PIN code
        success = await client.add_visitor_pin(visitor.id, "1234")
        if success:
            print("PIN assigned successfully")
        
        # Update visitor
        updated_visitor = await client.update_visitor(
            visitor.id,
            notes="VIP guest"
        )
        
        # Delete visitor when done
        await client.delete_visitor(visitor.id)
```

### Access Policy Management

```python
async def manage_access_policies():
    async with UniFiAccessClient(host="...", token="...") as client:
        
        # Get all access policies
        policies = await client.get_access_policies()
        
        # Get door groups
        door_groups = await client.get_door_groups()
        
        # Create new access policy
        policy = await client.create_access_policy(
            name="Visitor Policy",
            door_group_ids=[door_groups[0].id] if door_groups else []
        )
        
        print(f"Created policy: {policy.name}")
```

## 🔑 Authentication

### Getting Your API Token

1. **Access UniFi Access Controller**: Log into your UniFi Access web interface
2. **Navigate to Settings**: Go to System Settings > API
3. **Generate Token**: Create a new API token with appropriate permissions
4. **Copy Token**: Use the generated token in your application

### Token Permissions

The SDK requires a token with the following permissions:
- **Visitors**: Read, Write, Delete
- **Doors**: Read
- **Devices**: Read  
- **Access Policies**: Read, Write

## 📊 Error Handling

The SDK provides specific exception types for different error scenarios:

```python
from unifi_access import (
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

async def handle_errors():
    try:
        async with UniFiAccessClient(host="...", token="...") as client:
            visitors = await client.get_visitors()
            
    except AuthenticationError:
        print("Invalid API token or insufficient permissions")
    except ResourceNotFoundError:
        print("Requested resource not found")
    except ValidationError as e:
        print(f"Invalid data provided: {e}")
    except RateLimitError:
        print("API rate limit exceeded")
    except ConnectionError:
        print("Failed to connect to UniFi Access controller")
    except UniFiAccessError as e:
        print(f"General UniFi Access error: {e}")
```

## 🏗️ Data Models

The SDK provides rich data models for all entities:

```python
# Visitor model
visitor = await client.get_visitor("visitor-id")
print(f"Name: {visitor.first_name} {visitor.last_name}")
print(f"Phone: {visitor.phone}")
print(f"Active: {visitor.is_active}")
print(f"Start: {visitor.start_date}")
print(f"End: {visitor.end_date}")

# Door model  
door = await client.get_door("door-id")
print(f"Name: {door.name}")
print(f"Locked: {door.is_locked}")
print(f"Online: {door.is_online}")

# Device model
devices = await client.get_devices()
for device in devices:
    print(f"Device: {device.name}")
    print(f"Type: {device.type}")  # DeviceType enum
    print(f"Location: {device.location}")
```

## 🧪 Testing

Run the test suite:

```bash
# Install test dependencies
pip install -e ".[test]"

# Run tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=unifi_access
```

## 📚 API Reference

### Client Configuration

```python
UniFiAccessClient(
    host: str,              # UniFi Access controller hostname/IP
    token: str,             # API authentication token
    port: int = 12445,      # API port (default: 12445)
    verify_ssl: bool = False, # SSL verification (False for self-signed)
    timeout: int = 30,      # Request timeout in seconds
    max_retries: int = 3,   # Maximum retry attempts
    retry_delay: float = 1.0 # Delay between retries
)
```

### Available Methods

#### Visitors
- `get_visitors(limit, offset)` - Get list of visitors
- `get_visitor(visitor_id)` - Get specific visitor
- `create_visitor(...)` - Create new visitor
- `update_visitor(visitor_id, ...)` - Update visitor
- `delete_visitor(visitor_id)` - Delete visitor
- `add_visitor_pin(visitor_id, pin)` - Assign PIN to visitor

#### Doors
- `get_doors(limit, offset)` - Get list of doors
- `get_door(door_id)` - Get specific door

#### Devices
- `get_devices(limit, offset)` - Get list of devices
- `get_device(device_id)` - Get specific device

#### Access Policies
- `get_access_policies(limit, offset)` - Get list of access policies
- `get_access_policy(policy_id)` - Get specific access policy
- `create_access_policy(...)` - Create new access policy

#### Door Groups
- `get_door_groups(limit, offset)` - Get list of door groups
- `create_door_group(...)` - Create new door group

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

```bash
git clone https://github.com/keithah/unifi-access-python.git
cd unifi-access-python

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=unifi_access

# Run specific test file
python -m pytest tests/test_client.py
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Ubiquiti**: For creating the UniFi Access system and providing the Developer API
- **[@hjdhjd](https://github.com/hjdhjd/unifi-access)**: TypeScript implementation reference

## 📞 Support

- **Documentation**: [Full API Documentation](https://github.com/keithah/unifi-access-python/wiki)
- **Issues**: [GitHub Issues](https://github.com/keithah/unifi-access-python/issues)
- **Discussions**: [GitHub Discussions](https://github.com/keithah/unifi-access-python/discussions)

## 🗂️ Related Projects

- [unifi-access](https://github.com/hjdhjd/unifi-access) - TypeScript/Node.js implementation

---

**Made with ❤️ for the UniFi Access community**