#!/usr/bin/env python3
"""
Visitor management example for UniFi Access Python SDK

This example demonstrates how to create, manage, and delete visitors,
including PIN code assignment and access policy management.
"""

import asyncio
import os
from datetime import datetime, timedelta
from unifi_access import UniFiAccessClient, ValidationError

# Configuration - replace with your actual values
HOST = os.getenv("UNIFI_ACCESS_HOST", "192.168.1.100")
TOKEN = os.getenv("UNIFI_ACCESS_TOKEN", "your-api-token-here")
PORT = int(os.getenv("UNIFI_ACCESS_PORT", "12445"))

async def create_temporary_visitor(client):
    """Create a temporary visitor with 24-hour access"""
    
    print("📝 Creating temporary visitor...")
    
    # Set visitor access period (24 hours from now)
    start_date = datetime.now()
    end_date = start_date + timedelta(hours=24)
    
    try:
        visitor = await client.create_visitor(
            first_name="Demo",
            last_name="Visitor",
            start_date=start_date,
            end_date=end_date,
            phone="555-123-4567",
            email="demo.visitor@example.com",
            notes="Created by SDK example"
        )
        
        print(f"✅ Created visitor: {visitor.first_name} {visitor.last_name}")
        print(f"   ID: {visitor.id}")
        print(f"   Access period: {start_date.strftime('%Y-%m-%d %H:%M')} to {end_date.strftime('%Y-%m-%d %H:%M')}")
        
        return visitor
        
    except ValidationError as e:
        print(f"❌ Validation error: {e}")
        return None
    except Exception as e:
        print(f"❌ Error creating visitor: {e}")
        return None

async def assign_pin_to_visitor(client, visitor_id):
    """Assign a PIN code to a visitor"""
    
    print(f"🔢 Assigning PIN to visitor {visitor_id[:8]}...")
    
    try:
        # Generate a simple PIN (in production, use a secure random generator)
        pin = "1234"
        
        success = await client.add_visitor_pin(visitor_id, pin)
        
        if success:
            print(f"✅ PIN assigned successfully")
            print(f"   PIN: {pin} (Note: PIN is not returned by API for security)")
        else:
            print("❌ Failed to assign PIN")
            
        return success
        
    except Exception as e:
        print(f"❌ Error assigning PIN: {e}")
        return False

async def update_visitor_info(client, visitor_id):
    """Update visitor information"""
    
    print(f"📝 Updating visitor {visitor_id[:8]}...")
    
    try:
        updated_visitor = await client.update_visitor(
            visitor_id,
            notes="Updated by SDK example - VIP guest",
            email="updated.email@example.com"
        )
        
        print(f"✅ Visitor updated successfully")
        print(f"   New notes: {updated_visitor.notes}")
        
        return updated_visitor
        
    except Exception as e:
        print(f"❌ Error updating visitor: {e}")
        return None

async def list_all_visitors(client):
    """List all visitors and their status"""
    
    print("👥 Listing all visitors...")
    
    try:
        visitors = await client.get_visitors()
        
        print(f"   Found {len(visitors)} total visitors")
        print()
        
        # Group by status
        active_visitors = [v for v in visitors if v.is_active]
        inactive_visitors = [v for v in visitors if not v.is_active]
        
        print(f"   📊 Active visitors: {len(active_visitors)}")
        print(f"   📊 Inactive visitors: {len(inactive_visitors)}")
        print()
        
        # Show recent active visitors
        print("   🟢 Recent active visitors:")
        for visitor in active_visitors[:5]:
            status = "ACTIVE" if visitor.is_active else "INACTIVE"
            print(f"      • {visitor.first_name} {visitor.last_name} [{status}]")
            print(f"        📱 Phone: {visitor.phone or 'N/A'}")
            print(f"        📅 Access: {visitor.start_date.strftime('%m/%d')} - {visitor.end_date.strftime('%m/%d')}")
            print()
        
        return visitors
        
    except Exception as e:
        print(f"❌ Error listing visitors: {e}")
        return []

async def cleanup_visitor(client, visitor_id):
    """Clean up by deleting the test visitor"""
    
    print(f"🧹 Cleaning up visitor {visitor_id[:8]}...")
    
    try:
        await client.delete_visitor(visitor_id)
        print(f"✅ Visitor deleted successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error deleting visitor: {e}")
        return False

async def main():
    """Main visitor management demonstration"""
    
    async with UniFiAccessClient(
        host=HOST,
        token=TOKEN,
        port=PORT,
        verify_ssl=False
    ) as client:
        
        print("🔌 Connected to UniFi Access controller")
        print()
        
        # Step 1: List existing visitors
        await list_all_visitors(client)
        
        # Step 2: Create a new temporary visitor
        visitor = await create_temporary_visitor(client)
        
        if visitor:
            # Step 3: Assign PIN to the visitor
            await assign_pin_to_visitor(client, visitor.id)
            
            # Step 4: Update visitor information
            await update_visitor_info(client, visitor.id)
            
            # Step 5: Get the updated visitor details
            print(f"📋 Getting updated visitor details...")
            updated_visitor = await client.get_visitor(visitor.id)
            
            if updated_visitor:
                print(f"✅ Visitor details retrieved:")
                print(f"   Name: {updated_visitor.first_name} {updated_visitor.last_name}")
                print(f"   Email: {updated_visitor.email}")
                print(f"   Phone: {updated_visitor.phone}")
                print(f"   Notes: {updated_visitor.notes}")
                print(f"   Active: {updated_visitor.is_active}")
                print()
            
            # Step 6: Clean up (optional - uncomment to delete the test visitor)
            # print("⚠️  Cleaning up test visitor in 5 seconds...")
            # await asyncio.sleep(5)
            # await cleanup_visitor(client, visitor.id)
            
            print("✨ Example completed successfully!")
            print(f"   Test visitor ID: {visitor.id}")
            print("   Note: Test visitor was left in system for inspection")
        
        else:
            print("❌ Failed to create visitor - example aborted")

if __name__ == "__main__":
    print("UniFi Access Python SDK - Visitor Management Example")
    print("=" * 60)
    
    # Check if required environment variables are set
    if TOKEN == "your-api-token-here":
        print("❌ Please set your UNIFI_ACCESS_TOKEN environment variable")
        print("   export UNIFI_ACCESS_TOKEN='your-actual-token'")
        exit(1)
    
    asyncio.run(main())