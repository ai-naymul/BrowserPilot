# backend/cdp_streamer.py
import asyncio
import json
import websockets
from playwright.async_api import CDPSession

class CDPBrowserStreamer:
    def __init__(self, page):
        self.page = page
        self.cdp_session = CDPSession()
        self.streaming = False
        
    async def start_streaming(self, websocket_port: int = 8080):
        """Start CDP-based streaming"""
        try:
            # Get CDP session from Playwright page
            self.cdp_session = await self.page.context.new_cdp_session(self.page)
            
            # Enable necessary CDP domains
            await self.cdp_session.send('Runtime.enable')
            await self.cdp_session.send('Page.enable')
            await self.cdp_session.send('Page.startScreencast', {
                'format': 'jpeg',
                'quality': 80,
                'maxWidth': 1280,
                'maxHeight': 800,
                'everyNthFrame': 1  # Stream every frame for real-time
            })
            
            # Start WebSocket server for streaming
            await websockets.serve(self.handle_client, "localhost", websocket_port)
            print(f"🎥 CDP Streaming started on port {websocket_port}")
            
        except Exception as e:
            print(f"❌ Failed to start CDP streaming: {e}")
            
    async def handle_client(self, websocket, path):
        """Handle WebSocket clients for streaming"""
        print("🔗 Client connected to CDP stream")
        
        try:
            # Listen for screencast frames
            self.cdp_session.on('Page.screencastFrame', lambda params: 
                asyncio.create_task(self.send_frame(websocket, params)))
            
            # Keep connection alive and handle client messages
            async for message in websocket:
                data = json.loads(message)
                if data['type'] == 'mouse':
                    await self.handle_mouse_event(data)
                elif data['type'] == 'keyboard':
                    await self.handle_keyboard_event(data)
                    
        except websockets.exceptions.ConnectionClosed:
            print("🔌 Client disconnected from CDP stream")
            
    async def send_frame(self, websocket, params):
        """Send screencast frame to client"""
        try:
            frame_data = {
                'type': 'frame',
                'data': params['data'],  # Base64 encoded JPEG
                'metadata': {
                    'sessionId': params['sessionId'],
                    'timestamp': params.get('timestamp')
                }
            }
            await websocket.send(json.dumps(frame_data))
            
            # Acknowledge frame
            await self.cdp_session.send('Page.screencastFrameAck', {
                'sessionId': params['sessionId']
            })
        except Exception as e:
            print(f"❌ Error sending frame: {e}")
            
    async def handle_mouse_event(self, data):
        """Handle mouse events from client"""
        await self.cdp_session.send('Input.dispatchMouseEvent', {
            'type': data['eventType'],  # 'mousePressed', 'mouseReleased', 'mouseMoved'
            'x': data['x'],
            'y': data['y'],
            'button': data.get('button', 'left'),
            'clickCount': data.get('clickCount', 1)
        })
        
    async def handle_keyboard_event(self, data):
        """Handle keyboard events from client"""
        await self.cdp_session.send('Input.dispatchKeyEvent', {
            'type': data['eventType'],  # 'keyDown', 'keyUp', 'char'
            'text': data.get('text', ''),
            'key': data.get('key', ''),
            'code': data.get('code', '')
        })
