import asyncio
from pathlib import Path
from common import launch_browser_and_connect, TARGET_URL

async def main():
    browser_process, cdp = await launch_browser_and_connect()
    if not browser_process:
        return

    try:
        print("\n[PHASE 2] Function Attribution & Source Mapping")
        print("=" * 50)
        await cdp.send_cdp("Page.enable")
        await cdp.send_cdp("Debugger.enable")
        await cdp.send_cdp("Runtime.enable")

        script_map = {}
        
        # Navigate and wait for page to load to trigger script parsing
        print(f"\n  Initiating page navigation to: {TARGET_URL}")
        await cdp.send_cdp("Page.navigate", {"url": TARGET_URL})
        
        print("  Waiting for script parsing events...")
        page_loaded = False
        
        # Collect all scriptParsed events until page loads
        while True:
            event = await cdp.get_event(timeout=3)
            if not event:
                break
                
            if event.get("method") == "Debugger.scriptParsed":
                p = event['params']
                script_map[p['scriptId']] = p.get('url', 'inline-script')
                print(f"  > Script registered: ID={p['scriptId']}, URL={p.get('url', 'inline-script')}")
            elif event.get("method") == "Page.loadEventFired":
                print("  > Page load complete - script discovery phase finished")
                page_loaded = True
                break

        # Give a moment for any remaining scripts
        if page_loaded:
            await asyncio.sleep(1)
            # Check for any remaining script events
            while True:
                event = await cdp.get_event(timeout=0.5)
                if not event:
                    break
                if event.get("method") == "Debugger.scriptParsed":
                    p = event['params']
                    script_map[p['scriptId']] = p.get('url', 'inline-script')
                    print(f"  > Late script registered: ID={p['scriptId']}, URL={p.get('url', 'inline-script')}")

        print(f"\n  Script mapping complete: {len(script_map)} scripts discovered")
        print("  Beginning function attribution analysis...")
        print("  Target: window.fetch (suspected of monkey-patching)")

        # 1. Get a handle to the current (monkey-patched) fetch function
        response = await cdp.send_cdp(
            "Runtime.evaluate", 
            {"expression": "window.fetch", "returnByValue": False}
        )
        function_object_id = response['result']['result'].get('objectId')

        if not function_object_id:
            print("  ERROR: Could not get a handle to window.fetch.")
            return

        # 2. Get the internal properties of the function handle
        response = await cdp.send_cdp(
            "Runtime.getProperties", 
            {"objectId": function_object_id, "ownProperties": True}
        )
        
        # 3. Find the [[FunctionLocation]] to get the source scriptId
        location = None
        for prop in response['result'].get('internalProperties', []):
            if prop['name'] == '[[FunctionLocation]]':
                location = prop['value']['value']
                break
        
        print("\n  === SUSPECT IDENTIFIED ===")
        if location:
            script_id = location.get('scriptId')
            compromised_url = script_map.get(script_id, f"Unknown Script ID {script_id}")
            print("  > The monkey-patching of 'window.fetch' was traced back to:")
            print(f"  > {compromised_url}")
            print(f"  > Location: Line {location.get('lineNumber')}, Column {location.get('columnNumber')}")
        else:
            print("  > Could not find [[FunctionLocation]] for window.fetch.")
            print("  > This implies it is still the native function (no monkey-patching found).")

    finally:
        await cdp.close()
        browser_process.terminate()
        browser_process.wait()
        print("\n--- Investigation Complete ---")

if __name__ == "__main__":
    asyncio.run(main())