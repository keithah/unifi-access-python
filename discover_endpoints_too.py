#!/usr/bin/env python3
"""
Alternate Endpoint Discovery as proof of Concept

"""
import logging
import sys
from datetime import datetime, timedelta
from threefive import reader


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Test configuration
HOST = "https://iodisco.com"
TOKEN = "DPHlUYlFNgVzeZ5gvE34yQ"
PORT = 443

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


def vrfy_endpoint(endpoint):
    """
    vrfy_endpoint verify that a api enpoint exists.
    """
    endpoint = f"{HOST}:{PORT}{endpoint}"
    logger.info((f"trying {endpoint}"))
    try:
        rdr = reader(endpoint, {"Authorization": f"Bearer {TOKEN}"})
        return endpoint
    except:
        return False


def discover_endpoints():
    """Try to discover available API endpoints"""
    logger.info("Discovering UniFi Access API endpoints...")

    found_endpoints = []

    for prefix in PREFIXES:
        # if the prefix is found check for sub directories
        if vrfy_endpoint(prefix):
            found_endpoints.append(prefix)
            for endword in ENDWORDS:
                test_url = f"{prefix}{endword}"
                found_endpoints.append(vrfy_endpoint(test_url))

    found = [endpoint for endpoint in found_endpoints if endpoint]
    logger.info(f"Number of Endpoints found for {HOST}: {len(found)}")
    logger.info(f"Available Endpoints for {HOST} :  {found}")


if __name__ == "__main__":
    discover_endpoints()
