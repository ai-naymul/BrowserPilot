# backend/vnc_proxy.py
import asyncio
import websockets
import socket
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class VNCWebSocketProxy:
    def __init__(self, vnc_host: str = "localhost", vnc_port: int = 5901):
        self.vnc_host = vnc_host
        self.vnc_port = vnc_port
        self.server = None
        
    async def start_proxy(self, websocket_port: int):
        """Start the WebSocket to VNC proxy server"""
        try:
            self.server = await websockets.serve(
                self.handle_websocket,
                "localhost",
                websocket_port
            )
            logger.info(f"VNC WebSocket proxy started on port {websocket_port}")
            return True
        except Exception as e:
            logger.error(f"Failed to start VNC proxy: {e}")
            return False
    
    async def stop_proxy(self):
        """Stop the proxy server"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            
    async def handle_websocket(self, websocket, path):
        """Handle WebSocket connections and proxy to VNC"""
        vnc_socket = None
        try:
            # Connect to VNC server
            vnc_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            vnc_socket.connect((self.vnc_host, self.vnc_port))
            vnc_socket.setblocking(False)
            
            logger.info(f"Connected to VNC server at {self.vnc_host}:{self.vnc_port}")
            
            # Create tasks for bidirectional communication
            ws_to_vnc_task = asyncio.create_task(
                self.websocket_to_vnc(websocket, vnc_socket)
            )
            vnc_to_ws_task = asyncio.create_task(
                self.vnc_to_websocket(vnc_socket, websocket)
            )
            
            # Wait for either task to complete (indicating disconnection)
            await asyncio.gather(ws_to_vnc_task, vnc_to_ws_task, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"Error in VNC proxy: {e}")
        finally:
            if vnc_socket:
                vnc_socket.close()
                
    async def websocket_to_vnc(self, websocket, vnc_socket):
        """Forward WebSocket messages to VNC"""
        try:
            async for message in websocket:
                if isinstance(message, bytes):
                    await asyncio.get_event_loop().sock_sendall(vnc_socket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            logger.error(f"Error forwarding WebSocket to VNC: {e}")
            
    async def vnc_to_websocket(self, vnc_socket, websocket):
        """Forward VNC messages to WebSocket"""
        try:
            while True:
                data = await asyncio.get_event_loop().sock_recv(vnc_socket, 4096)
                if not data:
                    break
                await websocket.send(data)
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            logger.error(f"Error forwarding VNC to WebSocket: {e}")

# Global proxy manager
vnc_proxies = {}

async def start_vnc_proxy(vnc_port: int) -> Optional[int]:
    """Start a VNC WebSocket proxy for the given VNC port"""
    websocket_port = vnc_port + 1000  # Offset for WebSocket port
    
    if websocket_port in vnc_proxies:
        return websocket_port
        
    proxy = VNCWebSocketProxy("localhost", vnc_port)
    success = await proxy.start_proxy(websocket_port)
    
    if success:
        vnc_proxies[websocket_port] = proxy
        return websocket_port
    return None

async def stop_vnc_proxy(websocket_port: int):
    """Stop a VNC WebSocket proxy"""
    if websocket_port in vnc_proxies:
        await vnc_proxies[websocket_port].stop_proxy()
        del vnc_proxies[websocket_port]