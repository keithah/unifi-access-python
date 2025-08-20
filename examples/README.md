# UniFi Access Python SDK Examples

This directory contains practical examples demonstrating how to use the UniFi Access Python SDK effectively.

## 📋 Available Examples

### 1. Basic Usage (`basic_usage.py`)
**What it demonstrates:**
- Connecting to UniFi Access controller
- Retrieving visitors, doors, devices, and access policies
- Basic data inspection and display

**Run with:**
```bash
export UNIFI_ACCESS_HOST="your-controller-ip"
export UNIFI_ACCESS_TOKEN="your-api-token"
python examples/basic_usage.py
```

### 2. Visitor Management (`visitor_management.py`)
**What it demonstrates:**
- Creating new visitors with time-based access
- Assigning PIN codes to visitors
- Updating visitor information
- Listing and filtering visitors by status
- Deleting visitors (cleanup)

**Run with:**
```bash
export UNIFI_ACCESS_HOST="your-controller-ip"
export UNIFI_ACCESS_TOKEN="your-api-token"
python examples/visitor_management.py
```

### 3. Error Handling (`error_handling.py`)
**What it demonstrates:**
- Handling authentication errors
- Dealing with connection issues
- Resource not found scenarios
- Validation error handling
- API limitation awareness
- Robust retry logic with exponential backoff

**Run with:**
```bash
export UNIFI_ACCESS_HOST="your-controller-ip"
export UNIFI_ACCESS_TOKEN="your-api-token"  # Optional for some tests
python examples/error_handling.py
```

## 🔧 Setup Instructions

### Prerequisites
1. **UniFi Access Controller**: You need access to a UniFi Access system
2. **API Token**: Generate an API token in your UniFi Access web interface
3. **Python 3.7+**: Ensure you have Python 3.7 or newer installed

### Environment Variables
Set these environment variables before running the examples:

```bash
# Required
export UNIFI_ACCESS_HOST="192.168.1.100"        # Your controller IP/hostname
export UNIFI_ACCESS_TOKEN="your-actual-token"   # Your API token

# Optional
export UNIFI_ACCESS_PORT="12445"                # Default: 12445
```

### Running Examples
```bash
# Install the SDK first
pip install unifi-access-python

# Or if using the development version
pip install -e .

# Run any example
python examples/basic_usage.py
```

## 🔑 Getting Your API Token

1. **Log into UniFi Access**: Open your UniFi Access web interface
2. **Navigate to Settings**: Go to System Settings → API
3. **Create Token**: Generate a new API token with these permissions:
   - **Visitors**: Read, Write, Delete
   - **Doors**: Read
   - **Devices**: Read
   - **Access Policies**: Read, Write
4. **Copy Token**: Save the generated token securely

## 📊 Example Output

### Basic Usage Example
```
UniFi Access Python SDK - Basic Usage Example
==================================================
🔌 Connected to UniFi Access controller
   Host: 192.168.1.100:12445

👥 Getting visitors...
   Found 27 visitors
   • John Doe
     📱 Phone: 555-123-4567
     📅 Valid: 2025-01-15 09:00:00 to 2025-01-22 17:00:00
     🔢 Has PIN: Yes

🚪 Getting doors...
   Found 1 doors
   • Main Entrance
     🔒 Status: Locked
     🌐 Online: Yes
```

### Visitor Management Example
```
UniFi Access Python SDK - Visitor Management Example
============================================================
🔌 Connected to UniFi Access controller

👥 Listing all visitors...
   Found 28 total visitors
   📊 Active visitors: 15
   📊 Inactive visitors: 13

📝 Creating temporary visitor...
✅ Created visitor: Demo Visitor
   ID: 81f8dd8f-0a02-41e8-b361-b42b3f622839
   Access period: 2025-01-20 14:30 to 2025-01-21 14:30

🔢 Assigning PIN to visitor 81f8dd8f...
✅ PIN assigned successfully
```

## ⚠️ Important Notes

### API Limitations
The examples are designed to work with the UniFi Access Developer API, which has some limitations:

- **Door Control**: Unlock/lock operations are not available
- **WebSocket Events**: Real-time event streaming is not available  
- **Advanced Scheduling**: Complex scheduling features are not available
- **User Management**: Requires elevated permissions

### Error Handling
All examples include comprehensive error handling to demonstrate best practices:

- Authentication errors (invalid tokens)
- Connection issues (network problems)
- Resource not found (invalid IDs)
- Validation errors (invalid data)
- API limitations (unavailable features)

### Security Considerations
- **Never hardcode tokens** in your source code
- **Use environment variables** for sensitive configuration
- **Rotate tokens regularly** for security
- **Use HTTPS only** in production environments

## 🤝 Contributing Examples

Have a useful example to share? We'd love to include it! Please:

1. **Follow the existing pattern**: Use similar structure and error handling
2. **Add comprehensive comments**: Explain what each section does
3. **Include environment variable support**: Don't hardcode configuration
4. **Test thoroughly**: Ensure examples work with real UniFi Access systems
5. **Update this README**: Add your example to the list above

Submit a pull request with your example and we'll review it for inclusion!

## 📞 Need Help?

- **Documentation**: [Full API Documentation](https://github.com/keithah/unifi-access-python/wiki)
- **Issues**: [GitHub Issues](https://github.com/keithah/unifi-access-python/issues)
- **Discussions**: [GitHub Discussions](https://github.com/keithah/unifi-access-python/discussions)