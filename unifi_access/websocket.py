"""
UniFi Access WebSocket Client

Provides real-time event streaming from the UniFi Access API using WebSockets.
Supports notifications for access events, door status changes, and system alerts.
"""

import json
import asyncio
import logging
from typing import Optional, Dict, Any, Callable, Awaitable
import aiohttp
import ssl

from .exceptions import UniFiAccessError, ConnectionError, AuthenticationError

logger = logging.getLogger(__name__)


class UniFiAccessWebSocket:
    """
    WebSocket client for real-time UniFi Access events.
    
    Connects to the UniFi Access WebSocket endpoint to receive real-time
    notifications about access events, door status changes, and system alerts.
    """
    
    def __init__(
        self,
        host: str,
        token: str,
        port: int = 12445,
        verify_ssl: bool = False,
        reconnect_delay: float = 5.0,
        max_reconnect_attempts: int = 10
    ):
        """
        Initialize WebSocket client.
        
        Args:
            host: UniFi Access server hostname or IP
            token: Authentication token from main client
            port: WebSocket port (default: 12445)
            verify_ssl: Whether to verify SSL certificates
            reconnect_delay: Delay between reconnection attempts
            max_reconnect_attempts: Maximum reconnection attempts
        """
        self.host = host.rstrip('/')
        self.token = token
        self.port = port
        self.verify_ssl = verify_ssl
        self.reconnect_delay = reconnect_delay
        self.max_reconnect_attempts = max_reconnect_attempts
        
        self.ws_url = f"wss://{self.host}:{self.port}/api/v1/events/ws"
        self.session: Optional[aiohttp.ClientSession] = None
        self.websocket: Optional[aiohttp.ClientWebSocketResponse] = None
        self._running = False
        self._reconnect_attempts = 0
        
        # Event handlers
        self.on_access_event: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None
        self.on_door_status: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None
        self.on_device_status: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None
        self.on_system_alert: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None
        self.on_connect: Optional[Callable[[], Awaitable[None]]] = None
        self.on_disconnect: Optional[Callable[[], Awaitable[None]]] = None
        self.on_error: Optional[Callable[[Exception], Awaitable[None]]] = None
        
        # Create SSL context
        self.ssl_context = ssl.create_default_context()
        if not verify_ssl:
            self.ssl_context.check_hostname = False
            self.ssl_context.verify_mode = ssl.CERT_NONE
    
    async def connect(self):
        """Establish WebSocket connection."""
        if self._running:
            logger.warning("WebSocket is already running")
            return
        
        self._running = True
        self._reconnect_attempts = 0
        
        connector = aiohttp.TCPConnector(ssl=self.ssl_context)
        self.session = aiohttp.ClientSession(connector=connector)
        
        headers = {
            'Authorization': f'Bearer {self.token}'
        }
        
        try:
            self.websocket = await self.session.ws_connect(
                self.ws_url,
                headers=headers
            )
            
            logger.info("WebSocket connected to UniFi Access")
            self._reconnect_attempts = 0
            
            if self.on_connect:
                await self.on_connect()
            
            # Start message handling loop
            asyncio.create_task(self._message_handler())
            
        except Exception as e:
            logger.error(f"Failed to connect WebSocket: {e}")
            await self._handle_error(e)
            raise ConnectionError(f"WebSocket connection failed: {e}")
    
    async def disconnect(self):
        """Close WebSocket connection."""
        self._running = False
        
        if self.websocket and not self.websocket.closed:
            await self.websocket.close()
        
        if self.session and not self.session.closed:
            await self.session.close()
        
        logger.info("WebSocket disconnected")
        
        if self.on_disconnect:
            await self.on_disconnect()
    
    async def _message_handler(self):
        """Handle incoming WebSocket messages."""
        try:
            async for msg in self.websocket:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        await self._handle_message(data)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse WebSocket message: {e}")
                        
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {self.websocket.exception()}")
                    await self._handle_error(self.websocket.exception())
                    
                elif msg.type == aiohttp.WSMsgType.CLOSE:
                    logger.info("WebSocket connection closed by server")
                    break
                    
        except Exception as e:
            logger.error(f"WebSocket message handler error: {e}")
            await self._handle_error(e)
        
        # Connection was closed, attempt reconnection if still running
        if self._running:
            await self._attempt_reconnect()
    
    async def _handle_message(self, data: Dict[str, Any]):
        """Handle parsed WebSocket message."""
        message_type = data.get('type')
        payload = data.get('data', {})
        
        try:
            if message_type == 'access_event' and self.on_access_event:
                await self.on_access_event(payload)
                
            elif message_type == 'door_status' and self.on_door_status:
                await self.on_door_status(payload)
                
            elif message_type == 'device_status' and self.on_device_status:
                await self.on_device_status(payload)
                
            elif message_type == 'system_alert' and self.on_system_alert:
                await self.on_system_alert(payload)
                
            else:
                logger.debug(f"Unhandled message type: {message_type}")
                
        except Exception as e:
            logger.error(f"Error handling message type {message_type}: {e}")
            await self._handle_error(e)
    
    async def _attempt_reconnect(self):
        """Attempt to reconnect WebSocket."""
        if self._reconnect_attempts >= self.max_reconnect_attempts:
            logger.error(f"Max reconnection attempts ({self.max_reconnect_attempts}) reached")
            self._running = False
            return
        
        self._reconnect_attempts += 1
        logger.info(f"Attempting reconnection {self._reconnect_attempts}/{self.max_reconnect_attempts}")
        
        await asyncio.sleep(self.reconnect_delay)
        
        try:
            # Close existing connections
            if self.websocket and not self.websocket.closed:
                await self.websocket.close()
            if self.session and not self.session.closed:
                await self.session.close()
            
            # Recreate session and connect
            connector = aiohttp.TCPConnector(ssl=self.ssl_context)
            self.session = aiohttp.ClientSession(connector=connector)
            
            headers = {
                'Authorization': f'Bearer {self.token}'
            }
            
            self.websocket = await self.session.ws_connect(
                self.ws_url,
                headers=headers
            )
            
            logger.info("WebSocket reconnected successfully")
            self._reconnect_attempts = 0
            
            if self.on_connect:
                await self.on_connect()
            
            # Restart message handling
            asyncio.create_task(self._message_handler())
            
        except Exception as e:
            logger.error(f"Reconnection attempt failed: {e}")
            await self._handle_error(e)
            await self._attempt_reconnect()
    
    async def _handle_error(self, error: Exception):
        """Handle WebSocket errors."""
        if self.on_error:
            try:
                await self.on_error(error)
            except Exception as e:
                logger.error(f"Error in error handler: {e}")
    
    def set_access_event_handler(self, handler: Callable[[Dict[str, Any]], Awaitable[None]]):
        """Set handler for access events (door access attempts)."""
        self.on_access_event = handler
    
    def set_door_status_handler(self, handler: Callable[[Dict[str, Any]], Awaitable[None]]):
        """Set handler for door status changes (locked/unlocked)."""
        self.on_door_status = handler
    
    def set_device_status_handler(self, handler: Callable[[Dict[str, Any]], Awaitable[None]]):
        """Set handler for device status changes (online/offline)."""
        self.on_device_status = handler
    
    def set_system_alert_handler(self, handler: Callable[[Dict[str, Any]], Awaitable[None]]):
        """Set handler for system alerts and notifications."""
        self.on_system_alert = handler
    
    def set_connect_handler(self, handler: Callable[[], Awaitable[None]]):
        """Set handler for connection events."""
        self.on_connect = handler
    
    def set_disconnect_handler(self, handler: Callable[[], Awaitable[None]]):
        """Set handler for disconnection events."""
        self.on_disconnect = handler
    
    def set_error_handler(self, handler: Callable[[Exception], Awaitable[None]]):
        """Set handler for error events."""
        self.on_error = handler
    
    @property
    def is_connected(self) -> bool:
        """Check if WebSocket is connected."""
        return (
            self._running and 
            self.websocket is not None and 
            not self.websocket.closed
        )