#!/usr/bin/env python3
"""
Endpoint discovery script for UniFi Access API
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta

# Add the package to path for testing
sys.path.insert(0, '/home/keith/src/unifi-access-python')

from unifi_access import UniFiAccessClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test configuration
HOST = "192.168.42.73"
TOKEN = "DPHlUYlFNgVzeZ5gvE34yQ"
PORT = 12445


class TokenAuthClient(UniFiAccessClient):
    """Custom client that uses token authentication instead of username/password"""
    
    async def authenticate(self):
        """Override to use token instead of username/password"""
        self.token = TOKEN
        self.token_expires = datetime.utcnow() + timedelta(hours=24)
        
        # Update session headers with bearer token
        if self.session:
            self.session.headers.update({
                'Authorization': f'Bearer {self.token}'
            })


async def discover_endpoints():
    """Try to discover available API endpoints"""
    logger.info("Discovering UniFi Access API endpoints...")
    
    try:
        async with TokenAuthClient(
            host=HOST,
            username="dummy",
            password="dummy",
            port=PORT,
            verify_ssl=False,
            timeout=10
        ) as client:
            
            # Common endpoint patterns to try
            endpoints_to_try = [
                # Root endpoints
                "/",
                "/api",
                "/api/v1",
                "/api/v2",
                
                # Common resource patterns
                "/user",
                "/users", 
                "/door",
                "/doors",
                "/device", 
                "/devices",
                "/visitor",
                "/visitors",
                "/access-policy",
                "/access-policies",
                "/accesspolicy",
                "/accesspolicies",
                "/schedule",
                "/schedules",
                "/event",
                "/events",
                "/access-event",
                "/access-events",
                "/accessevent",
                "/accessevents",
                "/log",
                "/logs",
                "/system-log",
                "/system-logs",
                "/systemlog",
                "/systemlogs",
                "/site",
                "/sites",
                "/controller",
                "/controllers",
                "/credential",
                "/credentials",
                "/card",
                "/cards",
                "/pin",
                "/pins",
                "/nfc",
                "/badge",
                "/badges",
                
                # Alternative patterns
                "/api/user",
                "/api/users",
                "/api/door", 
                "/api/doors",
                "/api/device",
                "/api/devices",
                "/api/visitor",
                "/api/visitors",
                "/api/access-policy",
                "/api/access-policies",
                "/api/schedule",
                "/api/schedules",
                "/api/event",
                "/api/events",
                "/api/log",
                "/api/logs",
                
                # System/status endpoints
                "/status",
                "/health",
                "/info",
                "/version",
                "/system",
                "/stats",
                "/api/status",
                "/api/health",
                "/api/info",
                "/api/version",
                "/api/system"
            ]
            
            found_endpoints = []
            
            for endpoint in endpoints_to_try:
                try:
                    response = await client._request("GET", endpoint, params={"limit": 1})
                    found_endpoints.append((endpoint, "SUCCESS", response))
                    logger.info(f"✓ {endpoint} - SUCCESS")
                    
                    # Log response structure
                    if isinstance(response, dict):
                        keys = list(response.keys())
                        logger.info(f"    Response keys: {keys}")
                        if 'data' in response:
                            data = response['data']
                            if isinstance(data, list) and len(data) > 0:
                                logger.info(f"    Data count: {len(data)}")
                                sample = data[0]
                                if isinstance(sample, dict):
                                    sample_keys = list(sample.keys())[:5]
                                    logger.info(f"    Sample item keys: {sample_keys}")
                    
                except Exception as e:
                    error_type = type(e).__name__
                    # Only log non-404 errors to reduce noise
                    if "ResourceNotFoundError" not in error_type and "404" not in str(e):
                        logger.info(f"✗ {endpoint} - {error_type}: {e}")
            
            logger.info(f"\nFound {len(found_endpoints)} accessible endpoints:")
            for endpoint, status, response in found_endpoints:
                logger.info(f"  {endpoint}")
            
            return found_endpoints
            
    except Exception as e:
        logger.error(f"Discovery failed: {e}")
        import traceback
        traceback.print_exc()
        return []


if __name__ == "__main__":
    asyncio.run(discover_endpoints())