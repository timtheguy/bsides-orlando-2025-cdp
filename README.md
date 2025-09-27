### BSides Orlando 2025: Security Research with the Chrome DevTools Protocol
[🔗 Check out the slides!](https://github.com/timtheguy/bsides-orlando-2025-cdp/blob/main/BSides%20Orlando%202025%20Security%20Research%20with%20the%20Chrome%20DevTools%20Protocol.pdf)

#### Or, try out the mini-CTF...
Up for a challenge? [🔗 Check it out](https://timtheguy.github.io/ctf)
> Our competitor's data analytics service, 'InsightIQ', is running on our site. We've noticed a strange performance issue: every time a log message is displayed and removed from the screen, our browser's memory usage spikes momentarily. An anonymous source claims their script is attaching a 'tracking payload' to these temporary log elements just before they're destroyed. Your mission: use the Chrome DevTools Protocol to pause the browser at the exact moment an element is being removed, inspect its in-memory properties, and find the hidden payload. That payload is the flag.

### SecureShop 
Welcome to SecureShop, a "very secure" checkout page for demonstrating the techniques in the slides above.

#### Build 
We use an advanced bundling technique for our software. To install dependencies:
```
npm install webpack webpack-cli axios
```

Then, run `npx webpack` to build our `app.js` bundle.

#### Deploy
To deploy the site quickly, from `/dist`:
```
python3 -m http.server .
```

#### Project Structure
```
bsides-orlando-talk-2025/
├── README.md                           # Project documentation
├── package.json                        # Node.js dependencies and scripts
├── webpack.config.js                   # Webpack bundling configuration
├── 
├── src/
│   └── index.js                        # Main application entry point
├── 
├── dist/
│   ├── test-page.html                  # SecureShop checkout page
│   ├── app.js                          # Webpack-bundled application (built from src/)
│   └── jquery-migrate-3.4.1.min.js     # Looks like jquery-3.4.1.min.js
```

#### Demo Structure
```
├── common.py                           # Shared CDP utilities and browser automation
├── phase1.py                           # Runtime integrity & data flow analysis demo
├── phase2.py                           # Function attribution & source mapping demo  
└── phase3_c2.py                        # Covert C2 channel detection demo
```

#### Phase 1
Phase 1 performs runtime integrity checking and source-to-sink data flow tracking. It first examines the window.fetch function signature to detect monkey-patching by checking if it still contains '`[native code]`' or has been replaced with custom implementation. Then it injects a unique tracking marker into the credit card form field, triggers form submission, and monitors all outbound network requests to detect if the tracked data appears in POST payloads or URLs. This demonstrates how attackers can intercept and exfiltrate sensitive form data, and how security teams can trace data flow from user input to network transmission.

#### Phase 2
Phase 2 focuses on attributing malicious behavior back to specific source files through Chrome DevTools Protocol introspection. After collecting all loaded scripts during page navigation, it obtains a runtime handle to the window.fetch function and examines its internal `[[FunctionLocation]]` property to determine which script file and exact line/column coordinates contain the monkey-patching code. This technique allows security analysts to pinpoint the exact location of malicious modifications within loaded JavaScript, even in complex applications with multiple script dependencies.

#### Phase 3
Phase 3 specializes in detecting covert command-and-control infrastructure through WebSocket monitoring. It navigates to the target page while listening for WebSocket connection establishment and intercepting outbound WebSocket frames. When C2 traffic is detected, it parses JSON payloads to extract victim identification, message types (like 'check-in'), and source identifiers. This phase demonstrates how modern malware establishes persistent backdoors through legitimate web protocols and how security teams can identify and analyze these covert communication channels in real-time.
