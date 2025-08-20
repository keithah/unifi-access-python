#!/usr/bin/env python3
"""
Error handling example for UniFi Access Python SDK

This example demonstrates how to properly handle various error conditions
that can occur when working with the UniFi Access API.
"""

import asyncio
import os

from unifi_access import (
    AuthenticationError,
)
from unifi_access import ConnectionError as UniFiConnectionError
from unifi_access import (
    RateLimitError,
    ResourceNotFoundError,
)
from unifi_access import TimeoutError as UniFiTimeoutError
from unifi_access import (
    UniFiAccessClient,
    UniFiAccessError,
    ValidationError,
)

# Configuration
HOST = os.getenv("UNIFI_ACCESS_HOST", "192.168.1.100")
TOKEN = os.getenv("UNIFI_ACCESS_TOKEN", "your-api-token-here")
PORT = int(os.getenv("UNIFI_ACCESS_PORT", "12445"))


async def test_authentication_error():
    """Demonstrate authentication error handling"""

    print("🔐 Testing authentication error...")

    try:
        # Use an invalid token to trigger authentication error
        async with UniFiAccessClient(
            host=HOST,
            token="invalid-token-12345",
            port=PORT,
            verify_ssl=False,
            timeout=5,
        ) as client:

            _ = await client.get_visitors()

    except AuthenticationError as e:
        print(f"✅ Caught expected AuthenticationError: {e}")
        return True
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}: {e}")
        return False

    print("❌ Expected AuthenticationError but none was raised")
    return False


async def test_connection_error():
    """Demonstrate connection error handling"""

    print("🌐 Testing connection error...")

    try:
        # Use an invalid host to trigger connection error
        async with UniFiAccessClient(
            host="192.168.999.999",  # Invalid IP
            token=TOKEN,
            port=PORT,
            verify_ssl=False,
            timeout=2,  # Short timeout
        ) as client:

            _ = await client.get_visitors()

    except (UniFiConnectionError, OSError, asyncio.TimeoutError) as e:
        print(f"✅ Caught expected connection error: {type(e).__name__}: {e}")
        return True
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}: {e}")
        return False

    print("❌ Expected connection error but none was raised")
    return False


async def test_resource_not_found():
    """Demonstrate resource not found error handling"""

    print("🔍 Testing resource not found error...")

    try:
        async with UniFiAccessClient(
            host=HOST, token=TOKEN, port=PORT, verify_ssl=False
        ) as client:

            # Try to get a visitor with invalid ID
            _ = await client.get_visitor("invalid-visitor-id-12345")

    except ResourceNotFoundError as e:
        print(f"✅ Caught expected ResourceNotFoundError: {e}")
        return True
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}: {e}")
        return False

    print("❌ Expected ResourceNotFoundError but none was raised")
    return False


async def test_validation_error():
    """Demonstrate validation error handling"""

    print("📝 Testing validation error...")

    try:
        async with UniFiAccessClient(
            host=HOST, token=TOKEN, port=PORT, verify_ssl=False
        ) as client:

            # Try to create visitor with invalid data
            _ = await client.create_visitor(
                first_name="",  # Empty name should cause validation error
                last_name="",
                start_date=None,  # Invalid date
                end_date=None,
            )

    except ValidationError as e:
        print(f"✅ Caught expected ValidationError: {e}")
        return True
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}: {e}")
        return False

    print("❌ Expected ValidationError but none was raised")
    return False


async def test_api_limitations():
    """Demonstrate handling of API limitations"""

    print("⚠️  Testing API limitations...")

    try:
        async with UniFiAccessClient(
            host=HOST, token=TOKEN, port=PORT, verify_ssl=False
        ) as client:

            # Test door unlock (not available in developer API)
            try:
                doors = await client.get_doors()
                if doors:
                    await client.unlock_door(doors[0].id)
            except ResourceNotFoundError as e:
                print(f"✅ Door unlock limitation handled: {e}")

            # Test WebSocket (not available in developer API)
            try:
                _ = client.create_websocket_client()
            except ResourceNotFoundError as e:
                print(f"✅ WebSocket limitation handled: {e}")

            # Test schedules (not available in developer API)
            try:
                _ = await client.get_schedules()
            except ResourceNotFoundError as e:
                print(f"✅ Schedules limitation handled: {e}")

            return True

    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}: {e}")
        return False


async def robust_operation_example():
    """Example of robust operation with comprehensive error handling"""

    print("🛡️  Demonstrating robust operation...")

    max_retries = 3
    retry_delay = 1.0

    for attempt in range(max_retries):
        try:
            async with UniFiAccessClient(
                host=HOST, token=TOKEN, port=PORT, verify_ssl=False, timeout=10
            ) as client:

                # Perform multiple operations with error handling
                print(f"   Attempt {attempt + 1}/{max_retries}")

                # Get visitors
                visitors = await client.get_visitors(limit=5)
                print(f"   ✅ Retrieved {len(visitors)} visitors")

                # Get doors
                doors = await client.get_doors()
                print(f"   ✅ Retrieved {len(doors)} doors")

                # Get devices
                devices = await client.get_devices()
                print(f"   ✅ Retrieved {len(devices)} devices")

                print("   🎉 All operations completed successfully!")
                return True

        except AuthenticationError:
            print("   ❌ Authentication failed - check your token")
            break  # Don't retry auth errors

        except UniFiConnectionError:
            print(f"   ⚠️  Connection failed (attempt {attempt + 1})")
            if attempt < max_retries - 1:
                print(f"   🔄 Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                print("   ❌ Max retries exceeded")

        except UniFiTimeoutError:
            print(f"   ⚠️  Request timed out (attempt {attempt + 1})")
            if attempt < max_retries - 1:
                print(f"   🔄 Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
            else:
                print("   ❌ Max retries exceeded")

        except RateLimitError:
            print("   ⚠️  Rate limit exceeded - waiting before retry...")
            await asyncio.sleep(60)  # Wait longer for rate limits

        except ResourceNotFoundError as e:
            print(f"   ❌ Resource not found: {e}")
            break  # Don't retry not found errors

        except ValidationError as e:
            print(f"   ❌ Validation error: {e}")
            break  # Don't retry validation errors

        except UniFiAccessError as e:
            print(f"   ❌ UniFi Access API error: {e}")
            break  # Don't retry general API errors

        except Exception as e:
            print(f"   ❌ Unexpected error: {type(e).__name__}: {e}")
            break  # Don't retry unexpected errors

    return False


async def main():
    """Main error handling demonstration"""

    print("🔌 Testing various error scenarios...")
    print()

    # Test different error conditions
    test_results = []

    # Only run authentication test if we have a valid token
    if TOKEN != "your-api-token-here":
        test_results.append(await test_authentication_error())
    else:
        print("⚠️  Skipping authentication test (no token provided)")
        test_results.append(False)

    test_results.append(await test_connection_error())

    # Only run API tests if we have a valid token and host
    if TOKEN != "your-api-token-here":
        test_results.append(await test_resource_not_found())
        test_results.append(await test_validation_error())
        test_results.append(await test_api_limitations())
        test_results.append(await robust_operation_example())
    else:
        print("⚠️  Skipping API tests (no token provided)")
        test_results.extend([False, False, False, False])

    print()
    print("📊 Test Results Summary:")
    print(f"   Authentication Error: {'✅' if test_results[0] else '❌'}")
    print(f"   Connection Error: {'✅' if test_results[1] else '❌'}")
    print(f"   Resource Not Found: {'✅' if test_results[2] else '❌'}")
    print(f"   Validation Error: {'✅' if test_results[3] else '❌'}")
    print(f"   API Limitations: {'✅' if test_results[4] else '❌'}")
    print(f"   Robust Operations: {'✅' if test_results[5] else '❌'}")
    print()

    passed = sum(test_results)
    total = len(test_results)
    print(f"🎯 Overall: {passed}/{total} tests passed")


if __name__ == "__main__":
    print("UniFi Access Python SDK - Error Handling Example")
    print("=" * 55)

    asyncio.run(main())
