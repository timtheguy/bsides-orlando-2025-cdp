import asyncio
import json
import subprocess
import sys
import time
import websockets
import urllib.request
from pathlib import Path

# --- CONFIGURATION ---
TARGET_URL = "http://localhost:8000/test-page.html"
TRACKING_MARKER = "4987 1234 5678 9012"
REMOTE_DEBUGGING_PORT = 9222

# --- BROWSER LAUNCHER CONFIGURATION ---
if sys.platform == "darwin":
    CHROME_EXECUTABLE = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
else:
    CHROME_EXECUTABLE = "/usr/bin/google-chrome"

class CDPHandler:
    def __init__(self, websocket):
        self.ws = websocket
        self.response_queue = asyncio.Queue()
        self.event_queue = asyncio.Queue()
        self.running = True
        self.next_id = 1
        
    async def start(self):
        """Start the message handler task"""
        self.message_task = asyncio.create_task(self._message_handler())
        
    async def close(self):
        """Stop the message handler"""
        self.running = False
        if hasattr(self, 'message_task'):
            self.message_task.cancel()
            try:
                await self.message_task
            except asyncio.CancelledError:
                pass
    
    async def _message_handler(self):
        """Central message handler for all WebSocket messages"""
        try:
            while self.running:
                message = json.loads(await self.ws.recv())
                
                # Handle command responses (have 'id')
                if 'id' in message:
                    await self.response_queue.put(message)
                # Handle events (have 'method' but no 'id')
                elif 'method' in message:
                    await self.event_queue.put(message)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Message handler error: {e}")
    
    async def send_cdp(self, method, params=None):
        """Send CDP command and wait for response"""
        if params is None:
            params = {}
            
        cmd_id = self.next_id
        self.next_id += 1
        
        await self.ws.send(json.dumps({
            "id": cmd_id, 
            "method": method, 
            "params": params
        }))
        
        # Wait for the response with matching ID
        while True:
            message = await self.response_queue.get()
            if message.get("id") == cmd_id:
                return message
    
    async def get_event(self, timeout=None):
        """Get the next event, optionally with timeout"""
        if timeout:
            try:
                return await asyncio.wait_for(self.event_queue.get(), timeout=timeout)
            except asyncio.TimeoutError:
                return None
        else:
            return await self.event_queue.get()

async def launch_browser_and_connect():
    """Launch Chrome and return (browser_process, cdp_handler)"""
    try:
        # 1. LAUNCH BROWSER
        print(f"--- Launching Headless Chrome on port {REMOTE_DEBUGGING_PORT} ---")
        browser_cmd = [
            CHROME_EXECUTABLE,
            "--headless",
            "--no-sandbox",
            f"--remote-debugging-port={REMOTE_DEBUGGING_PORT}",
            "--disable-web-security",
            "--disable-gpu"
        ]
        browser_process = subprocess.Popen(
            browser_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(2)

        # 2. CONNECT TO BROWSER
        targets_json_url = f"http://127.0.0.1:{REMOTE_DEBUGGING_PORT}/json"
        with urllib.request.urlopen(targets_json_url) as response:
            targets = json.load(response)
            page_target = next((t for t in targets if t.get("type") == "page" and t.get("webSocketDebuggerUrl")), None)
            if not page_target:
                raise Exception("No page target found")
            target_ws_url = page_target["webSocketDebuggerUrl"]

        print("Connected to browser tab!")

        # 3. CONNECT TO WEBSOCKET
        websocket = await websockets.connect(target_ws_url, max_size=None)
        cdp = CDPHandler(websocket)
        await cdp.start()
        
        return browser_process, cdp

    except Exception as e:
        print(f"Failed to launch browser: {e}")
        return None, None