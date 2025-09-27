import asyncio
from common import launch_browser_and_connect, TARGET_URL, TRACKING_MARKER

async def main():
    browser_process, cdp = await launch_browser_and_connect()
    if not browser_process:
        return

    try:
        print("\n[PHASE 1] Runtime & Data Flow Analysis")
        print("=" * 50)
        await cdp.send_cdp("Page.enable")
        await cdp.send_cdp("Runtime.enable")
        await cdp.send_cdp("Network.enable")

        # Navigate to the target page
        print(f"\n  Initiating page navigation to: {TARGET_URL}")
        await cdp.send_cdp("Page.navigate", {"url": TARGET_URL})
        
        # Wait for page to load
        print("  Waiting for DOM load event...")
        while True:
            event = await cdp.get_event(timeout=5)
            if not event:
                print("  ERROR: Timeout waiting for page load event")
                break
            if event.get("method") == "Page.loadEventFired":
                print("  Page load event fired - DOM ready")
                break
        
        # Give time for scripts to execute
        # In a real-world automated tool, you could use CDP to wait for a 
        # specific element to be visible or for network activity to idle
        await asyncio.sleep(2)

        # --- CHECK 1: Runtime Integrity (Monkey-Patching Detection) ---
        print("\n  [CHECK 1] Testing runtime integrity...")
        print("     -> Examining window.fetch function signature...")
        
        response = await cdp.send_cdp("Runtime.evaluate", {"expression": "window.fetch.toString()"})
        fetch_sig = response['result']['result']['value']
        
        print(f"     -> Function signature: {fetch_sig[:100]}...")
        
        if "native code" in fetch_sig:
            print("     -> RESULT: Function contains '[native code]' - integrity preserved")
            print("     -> Assessment: No monkey-patching detected")
        else:
            print("     -> RESULT: Function does NOT contain '[native code]'")
            print("     -> Assessment: Runtime modification detected (monkey-patching)")
            print("     -> Evidence: Custom implementation overrides native browser API")
            print("  SECURITY ALERT: window.fetch has been compromised")

        # --- CHECK 2: Data Flow Analysis (Source-to-Sink Tracking) ---
        print("\n  [CHECK 2] Setting up data flow analysis...")
        
        # Verify form elements exist
        print("     -> Checking form elements...")
        field_check = await cdp.send_cdp("Runtime.evaluate", {
            "expression": """(() => {
                return {
                    creditCardField: !!document.getElementById('credit-card'),
                    paymentForm: !!document.getElementById('paymentForm'),
                    submitButton: !!document.querySelector('button[type=submit]')
                };
            })()""",
            "returnByValue": True
        })
        
        field_info = field_check['result']['result']['value']
                
        if not field_info['creditCardField']:
            print("  ERROR: Cannot proceed without credit card field!")
            return

        # Inject tracking marker into the source
        print(f"\n     -> Injecting tracking marker: '{TRACKING_MARKER}'")
        await cdp.send_cdp("Runtime.evaluate", {
            "expression": f"""(() => {{
                const field = document.getElementById('credit-card');
                field.value = '{TRACKING_MARKER}';
                field.dispatchEvent(new Event('input', {{ bubbles: true }}));
            }})()""",
            "returnByValue": True
        })
        
        # Verify marker injection
        verify_result = await cdp.send_cdp("Runtime.evaluate", {
            "expression": "document.getElementById('credit-card').value",
            "returnByValue": True
        })
        verified_value = verify_result['result']['result']['value']
        
        if verified_value == TRACKING_MARKER:
            print("     -> Marker injection: SUCCESS")
            print(f"     -> Field now contains: '{verified_value}'")
        else:
            print("     -> Marker injection: FAILED")
            print(f"     -> Expected: '{TRACKING_MARKER}'")
            print(f"     -> Got: '{verified_value}'")
            return

        # Trigger form submission
        print("\n     -> Triggering form submission...")
        submit_result = await cdp.send_cdp("Runtime.evaluate", {
            "expression": """(() => {
                const button = document.querySelector('button[type=submit]');
                if (button) {
                    button.click();
                    return 'FORM_SUBMITTED';
                } else {
                    return 'BUTTON_NOT_FOUND';
                }
            })()""",
            "returnByValue": True
        })
        
        submit_status = submit_result['result']['result']['value']
        if 'SUBMITTED' in submit_status:
            print("     -> Form submission: SUCCESS")
        else:
            print(f"     -> Form submission: FAILED ({submit_status})")

        # Monitor network traffic for tracked data
        print("\n     -> Monitoring network traffic for tracked data...")
        print("     -> Listening for outbound requests...")
        
        marker_found = False
        timeout_count = 0
        max_timeouts = 5
        
        while not marker_found and timeout_count < max_timeouts:
            event = await cdp.get_event(timeout=2)
            if not event:
                timeout_count += 1
                print(f"     -> Waiting... ({timeout_count}/{max_timeouts})")
                continue
                
            method = event.get("method")
            if method == "Network.requestWillBeSent":
                req = event['params']['request']
                url = req['url']
                method_type = req['method']
                
                print(f"     -> Captured: {method_type} {url}")
                
                # Check for tracking marker in POST data
                if req.get('postData') and TRACKING_MARKER in req.get('postData'):
                    print("\n  === EXFILTRATION DETECTED ===")
                    print(f"  > Method: {method_type}")
                    print(f"  > Destination: {url}")
                    print("  > Tracked payload found in POST data!")
                    print(f"  > Data: {req['postData']}")
                    marker_found = True
                    break
                    
                # Check for tracking marker in URL
                elif TRACKING_MARKER in url:
                    print("\n  === EXFILTRATION DETECTED ===")
                    print(f"  > Method: {method_type}")
                    print("  > Tracked data found in URL!")
                    print(f"  > URL: {url}")
                    marker_found = True
                    break
                    
            elif method == "Runtime.consoleAPICalled":
                # Show console messages for transparency
                args = event['params'].get('args', [])
                if args:
                    console_msg = ' '.join(str(arg.get('value', '')) for arg in args)
                    print(f"     -> Console: {console_msg}")

        # Final result
        if marker_found:
            print("\n  INVESTIGATION RESULT: MALICIOUS ACTIVITY CONFIRMED")
            print("  > Tracked data successfully followed from source to sink")
            print("  > Data exfiltration attempt detected and logged")
        else:
            print("\n  INVESTIGATION RESULT: NO EXFILTRATION DETECTED")
            print("  > Either the attack failed or uses a different vector")
            print("  > Manual verification recommended")

    finally:
        await cdp.close()
        browser_process.terminate()
        browser_process.wait()
        print("\n--- Investigation Complete ---")

if __name__ == "__main__":
    asyncio.run(main())