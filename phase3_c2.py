import asyncio
import json
from common import launch_browser_and_connect, TARGET_URL

async def main():
    browser_process, cdp = await launch_browser_and_connect()
    if not browser_process:
        return

    try:
        print("\n[PHASE 3] Covert C2 Channel Analysis")
        print("=" * 50)
        await cdp.send_cdp("Page.enable")
        await cdp.send_cdp("Network.enable")

        checkout_url = TARGET_URL
        print(f"\n  Initiating page navigation to: {checkout_url}")
        print("  Monitoring for covert command & control communications...")
        await cdp.send_cdp("Page.navigate", {"url": checkout_url})

        # Listen for WebSocket events
        c2_found = False
        websocket_connections = 0
        c2_messages = []
        
        print("  Listening for network events...")
        
        while not c2_found:
            event = await cdp.get_event(timeout=10)
            if not event: 
                break

            method = event.get("method")
            params = event.get("params", {})

            if method == "Network.webSocketCreated":
                websocket_connections += 1
                ws_url = params.get('url', 'Unknown')
                print(f"\n  WebSocket connection established:")
                print(f"  > URL: {ws_url}")
                print(f"  > Connection ID: {params.get('requestId', 'Unknown')}")
            
            if method == "Network.webSocketFrameSent":
                payload = params.get('response', {}).get('payloadData', '')
                c2_messages.append(payload)
                print(f"  > Outbound frame intercepted: {payload}")
                
                # Parse the JSON payload for analysis
                try:
                    message_data = json.loads(payload)
                    if message_data.get('type') == 'check-in':
                        print(f"  > Message type: {message_data.get('type')}")
                        print(f"  > Victim ID: {message_data.get('victimId', 'Unknown')}")
                        print(f"  > Source identifier: {message_data.get('source', 'Unknown')}")
                        c2_found = True
                except json.JSONDecodeError:
                    print(f"  > Non-JSON payload detected")

        print("\n  === COVERT C2 CHANNEL INTERCEPTED ===")
        if c2_found:
            print("  ANALYSIS RESULT: Command & control infrastructure detected")
            print(f"  > WebSocket connections established: {websocket_connections}")
            print(f"  > C2 messages intercepted: {len(c2_messages)}")
            print("  > Evidence: Persistent backdoor with remote command capability")
            print("  > Threat level: CRITICAL - Active C2 beacon identified")
        else:
            print("  ANALYSIS RESULT: No C2 WebSocket activity detected")
            print("  > This may indicate dormant payload or alternative C2 method")

    finally:
        await cdp.close()
        browser_process.terminate()
        browser_process.wait()
        print("\n--- Investigation Complete ---")

if __name__ == "__main__":
    asyncio.run(main())