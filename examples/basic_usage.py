#!/usr/bin/env python3
"""
Basic usage example for UniFi Access Python SDK

This example demonstrates how to connect to your UniFi Access controller
and perform basic operations like getting visitors, doors, and devices.
"""

import asyncio
import os
from unifi_access import UniFiAccessClient

# Configuration - replace with your actual values
HOST = os.getenv("UNIFI_ACCESS_HOST", "192.168.1.100")
TOKEN = os.getenv("UNIFI_ACCESS_TOKEN", "your-api-token-here")
PORT = int(os.getenv("UNIFI_ACCESS_PORT", "12445"))

async def main():
    """Basic usage example"""
    
    # Initialize the client
    async with UniFiAccessClient(
        host=HOST,
        token=TOKEN,
        port=PORT,
        verify_ssl=False  # For self-signed certificates
    ) as client:
        
        print("🔌 Connected to UniFi Access controller")
        print(f"   Host: {HOST}:{PORT}")
        print()
        
        # Get all visitors
        print("👥 Getting visitors...")
        visitors = await client.get_visitors(limit=10)
        print(f"   Found {len(visitors)} visitors")
        
        for visitor in visitors[:3]:  # Show first 3
            print(f"   • {visitor.first_name} {visitor.last_name}")
            print(f"     📱 Phone: {visitor.phone or 'N/A'}")
            print(f"     📅 Valid: {visitor.start_date} to {visitor.end_date}")
            print(f"     🔢 Has PIN: {'Yes' if visitor.pin_codes else 'No'}")
            print()
        
        # Get all doors
        print("🚪 Getting doors...")
        doors = await client.get_doors()
        print(f"   Found {len(doors)} doors")
        
        for door in doors:
            print(f"   • {door.name}")
            print(f"     🔒 Status: {'Locked' if door.is_locked else 'Unlocked'}")
            print(f"     🌐 Online: {'Yes' if door.is_online else 'No'}")
            print()
        
        # Get all devices
        print("📱 Getting devices...")
        devices = await client.get_devices()
        print(f"   Found {len(devices)} devices")
        
        for device in devices:
            print(f"   • {device.name}")
            print(f"     🔧 Type: {device.type.value}")
            print(f"     📍 Location: {device.location or 'N/A'}")
            print()
        
        # Get access policies
        print("🔐 Getting access policies...")
        policies = await client.get_access_policies()
        print(f"   Found {len(policies)} access policies")
        
        for policy in policies:
            print(f"   • {policy.name}")
            print(f"     🚪 Door groups: {len(policy.door_group_ids)}")
            print()
        
        # Get door groups
        print("🏢 Getting door groups...")
        door_groups = await client.get_door_groups()
        print(f"   Found {len(door_groups)} door groups")
        
        for group in door_groups:
            print(f"   • {group.name}")
            print(f"     🚪 Doors: {len(group.door_ids)}")
            print()

if __name__ == "__main__":
    print("UniFi Access Python SDK - Basic Usage Example")
    print("=" * 50)
    
    # Check if required environment variables are set
    if TOKEN == "your-api-token-here":
        print("❌ Please set your UNIFI_ACCESS_TOKEN environment variable")
        print("   export UNIFI_ACCESS_TOKEN='your-actual-token'")
        exit(1)
    
    asyncio.run(main())