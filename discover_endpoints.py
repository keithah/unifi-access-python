#!/usr/bin/env python3
"""
Endpoint discovery script for UniFi Access API
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta

from unifi_access import UniFiAccessClient

# Add the package to path for testing
sys.path.insert(0, "/home/keith/src/unifi-access-python")


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Test configuration
import os

HOST = os.getenv("UNIFI_ACCESS_HOST", "localhost")
TOKEN = os.getenv("UNIFI_ACCESS_TOKEN", "")
PORT = int(os.getenv("UNIFI_ACCESS_PORT", "12445"))

PREFIXES = [
    "/",
    "/api/",
]

ENDWORDS = [
    "access-event",
    "access-events",
    "accessevent",
    "accessevents",
    "access-policies",
    "accesspolicies",
    "access-policy",
    "accesspolicy",
    "badge",
    "badges",
    "card",
    "cards",
    "controller",
    "controllers",
    "credential",
    "credentials",
    "device",
    "devices",
    "door",
    "doors",
    "event",
    "events",
    "health",
    "info",
    "log",
    "logs",
    "nfc",
    "pin",
    "pins",
    "schedule",
    "schedules",
    "site",
    "sites",
    "stats",
    "status",
    "system",
    "system-log",
    "system-logs",
    "systemlog",
    "systemlogs",
    "user",
    "users",
    "v1",
    "v2",
    "version",
    "visitor",
    "visitors",
]


class TokenAuthClient(UniFiAccessClient):
    """Custom client that uses token authentication instead of username/password"""

    async def authenticate(self):
        """Override to use token instead of username/password"""
        self.token = self.token or TOKEN
        self.token_expires = datetime.utcnow() + timedelta(hours=24)

        # Update session headers with bearer token
        if self.session:
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})


async def discover_endpoints():
    """Try to discover available API endpoints"""
    logger.info("Discovering UniFi Access API endpoints...")

    found_endpoints = []

    try:
        async with TokenAuthClient(
            host=HOST, port=PORT, token=TOKEN, verify_ssl=False, timeout=10
        ) as client:
            for prefix in PREFIXES:
                endpoints_to_try = [f"{prefix}{endword}" for endword in ENDWORDS]
                for endpoint in endpoints_to_try:
                    try:
                        response = await client._request(
                            "GET", endpoint, params={"limit": 1}
                        )
                        found_endpoints.append((endpoint, "SUCCESS", response))
                        logger.info(f"✓ {endpoint} - SUCCESS")
                        # Log response structure
                        if isinstance(response, dict):
                            keys = list(response.keys())
                            logger.info(f"    Response keys: {keys}")
                            if "data" in response:
                                data = response["data"]
                                if isinstance(data, list) and len(data) > 0:
                                    logger.info(f"    Data count: {len(data)}")
                                    sample = data[0]
                                    if isinstance(sample, dict):
                                        sample_keys = list(sample.keys())[:5]
                                        logger.info(
                                            f"    Sample item keys: {sample_keys}"
                                        )

                    except Exception as e:
                        error_type = type(e).__name__
                        # Only log non-404 errors to reduce noise
                        if (
                            "ResourceNotFoundError" not in error_type
                            and "404" not in str(e)
                        ):
                            logger.info(f"✗ {endpoint} - {error_type}: {e}")

        logger.info(f"\nFound {len(found_endpoints)} accessible endpoints:")
        for endpoint, status, response in found_endpoints:
            logger.info(f"  {endpoint}")

    except Exception as e:
        logger.error(f"Discovery failed: {e}")
        import traceback

        traceback.print_exc()

    return found_endpoints


if __name__ == "__main__":
    if not TOKEN:
        logger.error("Please set UNIFI_ACCESS_TOKEN environment variable")
        logger.error("export UNIFI_ACCESS_TOKEN='your-actual-token'")
        sys.exit(1)

    asyncio.run(discover_endpoints())
