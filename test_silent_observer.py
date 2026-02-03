
import requests
import time
import json
from datetime import datetime

API_URL = "http://127.0.0.1:8000/api/message"
API_KEY = "your-secret-api-key-here"

TEST_CASES = [
    # Benign Messages (Should be IGNORED)
    {"text": "Hey mom, I'll be late for dinner.", "type": "Benign"},
    {"text": "The meeting is rescheduled to 4 PM.", "type": "Benign"},
    {"text": "Happy Birthday! Have a great day.", "type": "Benign"},
    
    # Scam Messages (Should be REPLIED to)
    {"text": "Your SBI account is blocked. Click here to update KYC immediately.", "type": "Scam"},
    {"text": "Congratulations! You won 5 Lakh lottery. Pay 500 registration fee.", "type": "Scam"},
    {"text": "Electricity will be cut tonight completely. Call this officer now.", "type": "Scam"},
]

def run_test():
    print("="*60)
    print("   SILENT OBSERVER & API TRACKING TEST")
    print("="*60)
    
    results = []
    
    for i, case in enumerate(TEST_CASES):
        print(f"\n[Test {i+1}] Sending {case['type']} message...")
        print(f"   Input: \"{case['text']}\"")
        
        payload = {
            "sessionId": f"test-silent-{int(time.time())}",
            "message": {
                "sender": "scammer", # Even if we call it 'scammer', the TEXT content matters
                "text": case['text'],
                "timestamp": datetime.now().isoformat()
            },
            "conversationHistory": [],
            "metadata": {"channel": "SMS", "language": "en", "locale": "IN"}
        }
        
        start_time = time.time()
        try:
            response = requests.post(
                API_URL, 
                json=payload, 
                headers={"X-API-Key": API_KEY},
                timeout=30
            )
            data = response.json()
            latency = (time.time() - start_time) * 1000
            
            is_scam_detected = data.get('scamDetected', False)
            has_reply = data.get('reply') is not None
            
            # API Tracking Logic
            status = "PASS"
            if case['type'] == "Benign":
                # Expect: Scam=False, Reply=False
                if not is_scam_detected and not has_reply:
                    call_status = "Skipped (Correct)"
                else:
                    status = "FAIL"
                    call_status = f"TRIGGERED (Incorrect - Scam:{is_scam_detected})"
            else:
                # Expect: Scam=True, Reply=True
                if is_scam_detected and has_reply:
                    call_status = "Triggered (Correct)"
                elif is_scam_detected and not has_reply:
                     # Could happen if agent fails
                    status = "WARN"
                    call_status = "Triggered but No Reply" 
                else:
                    status = "FAIL"
                    call_status = "Skipped (Incorrect)"

            print(f"   > API Status: {response.status_code}")
            print(f"   > Latency:    {latency:.0f}ms")
            print(f"   > Detection:  {is_scam_detected}")
            print(f"   > LLM Call:   {call_status}")
            if has_reply:
                print(f"   > Agent Replied: \"{data['reply'][:50]}...\"")
            
            results.append({"type": case['type'], "status": status, "latency": latency})
            
        except Exception as e:
            print(f"   > ERROR: {str(e)}")
            results.append({"type": case['type'], "status": "ERROR", "latency": 0})

    print("\n" + "="*60)
    print("   TEST SUMMARY")
    print("="*60)
    print(f"{'Type':<10} | {'Status':<10} | {'Latency':<10}")
    print("-" * 35)
    for r in results:
        print(f"{r['type']:<10} | {r['status']:<10} | {r['latency']:.0f}ms")
    print("-" * 35)

if __name__ == "__main__":
    run_test()
