import requests
import json
from datetime import datetime, timezone
import time

API_URL = 'http://127.0.0.1:8000'
API_KEY = 'your-secret-api-key-here'

# Test scam detection
payload = {
    'sessionId': f'quick-test-{int(time.time())}',
    'message': {
        'sender': 'scammer',
        'text': 'Your bank account blocked! Send OTP to +919876543210',
        'timestamp': datetime.now(timezone.utc).isoformat()
    },
    'conversationHistory': [],
    'metadata': {'channel': 'SMS', 'language': 'English', 'locale': 'IN'}
}

try:
    response = requests.post(
        f'{API_URL}/api/message',
        json=payload,
        headers={'X-API-Key': API_KEY},
        timeout=60
    )
    print(f'Status: {response.status_code}')
    if response.status_code == 200:
        data = response.json()
        print(f'scamDetected: {data.get("scamDetected")}')
        print(f'reply: {data.get("reply", "NONE")}')
        print(f'status: {data.get("status")}')
        intel = data.get('extractedIntelligence', {})
        print(f'phones: {intel.get("phoneNumbers", [])}')
        print(f'upi: {intel.get("upiIds", [])}')
    else:
        print(f'Error: {response.text[:300]}')
except Exception as e:
    print(f'Exception: {e}')
