import time
import requests
import json
from datetime import datetime, timezone
import sys
import os

# --- CONFIGURATION ---
API_URL = os.getenv("HONEYPOT_API_URL", "http://localhost:8000")
API_KEY = os.getenv("HONEYPOT_API_KEY", "YOUR_SECRET_API_KEY")
DELAY_SECONDS = 0.5 

# Define Test Scenarios - Diverse scam types
TEST_SCENARIOS = [
    {
        "name": "SBI Bank KYC Scam",
        "locale": "IN",
        "language": "English",
        "messages": [
            "Your SBI account has been put on hold due to missing KYC documents.",
            "If you don't update immediately, your account will be permanently closed. Visit http://sbi-kyc-verify-online.com",
            "Why are you ignoring this? This is the bank manager speaking. It is urgent.",
            "To verify your identity, transfer Rs 10 to UPI id: verification.dept@okicici to activate account.",
            "This is your last chance. Police case will be filed if you don't cooperate."
        ]
    },
    {
        "name": "WhatsApp Job Scam (Hinglish)",
        "locale": "IN",
        "language": "Hinglish",
        "messages": [
            "Hello, hum Amazon se bol rahe hain. Aapke liye part-time job vacancy hai.",
            "Daily earning 2000-5000 INR. Just small tasks like liking videos.",
            "Theek hai, abhi training ke liye aapko 500 rupay deposit karne honge jo refund mil jayenge.",
            "Ye hamara manager ka UPI ID hai: amazon.hr@paytm. payment screenshot bhejo."
        ]
    },
    {
        "name": "Tech Support Scam",
        "locale": "US",
        "language": "English",
        "messages": [
            "WARNING: Your Windows computer is infected with a Trojan virus!",
            "Call our certified Microsoft technicians at +1-800-123-4567 immediately.",
            "Do not turn off your computer or your data will be deleted.",
            "Our technician needs remote access to fix the registry. Please download AnyDesk.",
            "To complete the repair, you need to purchase a Lifetime Protection Plan for $299 via Best Buy Gift Cards."
        ]
    },
    {
        "name": "Lottery Winner Scam",
        "locale": "US",
        "language": "English",
        "messages": [
            "CONGRATULATIONS! You have won $5,000,000 in the Google International Lottery!",
            "To claim your prize, reply with your full name and address.",
            "Your claim ID is GL-2026-WIN-8842. Keep this confidential.",
            "Pay processing fee of $500 via Bitcoin to wallet: 1A2b3C4d5E6f7G8h9I0j",
            "Send payment proof to claims@google-lottery-intl.org to release funds."
        ]
    },
    {
        "name": "Romance Scam",
        "locale": "US",
        "language": "English",
        "messages": [
            "Hi dear, I saw your profile and felt an instant connection. I'm Sarah, a nurse from California.",
            "I'm currently deployed with UN peacekeeping mission in Syria. It's so hard here without family.",
            "I want to come meet you but my funds are frozen due to military regulations.",
            "Can you help me with $2000 for a leave permit? I'll pay you back double when I arrive.",
            "Please send via Western Union to Agent: Michael Brown, Lagos, Nigeria. Reference: LOVE2026"
        ]
    },
    {
        "name": "Crypto Investment Scam",
        "locale": "IN",
        "language": "English",
        "messages": [
            "Exclusive opportunity! Join our VIP Crypto Trading Group with 500% guaranteed returns!",
            "Check our platform at http://crypto-wealth-now.io - Already 10,000+ members earning daily!",
            "Minimum investment just 0.1 BTC. Profits credited within 24 hours.",
            "Deposit to wallet: bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
            "Limited slots! After 100 members, entry fee increases to 0.5 BTC."
        ]
    },
    {
        "name": "Aadhaar-PAN Link Scam (India)",
        "locale": "IN", 
        "language": "Hinglish",
        "messages": [
            "URGENT: Aapka PAN card Aadhaar se link nahi hai. Aaj last date hai!",
            "Abhi link karo warna Rs 10,000 fine lagega aur PAN deactivate ho jayega.",
            "Hamare official portal pe jao: http://pan-aadhaar-link-gov.in",
            "Verification ke liye Rs 50 fee hai. Pay karo UPI: govtverify@ybl",
            "Aapka reference number hai: PAN2026LINK. Ye save kar lo."
        ]
    },
    {
        "name": "Electricity Bill Scam",
        "locale": "IN",
        "language": "Hinglish", 
        "messages": [
            "Dear Customer, aapka electricity bill overdue hai. Aaj raat 9 baje connection cut ho jayega.",
            "Outstanding amount: Rs 8,547. Abhi pay karo disconnection se bachne ke liye.",
            "Payment link: http://electricity-pay-now.com/bill",
            "UPI se bhi pay kar sakte ho: electricity.dept@paytm",
            "Agar 2 ghante mein payment nahi hua, Rs 500 reconnection charge lagega."
        ]
    },
    {
        "name": "Delivery Package Scam",
        "locale": "IN",
        "language": "English",
        "messages": [
            "Your Amazon package could not be delivered due to incomplete address.",
            "Tracking ID: AMZ-2026-IND-98765. Package will be returned in 24 hours.",
            "Update your address at: http://amazon-delivery-update.com/track",
            "Pay Rs 49 redelivery charge via UPI: amazondelivery@okaxis",
            "Reply with your Aadhaar number for address verification."
        ]
    },
    {
        "name": "Investment Advisor Scam",
        "locale": "IN",
        "language": "English",
        "messages": [
            "Hello Sir, I am Rajesh from Angel Broking. We have special stock tips for you.",
            "Our premium members made 200% profit last month. Join now at discounted rate.",
            "One-time membership fee: Rs 15,000. Guaranteed profits or money back.",
            "Pay to our company account: A/C No: 1234567890123456, IFSC: HDFC0001234",
            "Call me personally for VIP tips: +91-9876543210. Limited seats available!"
        ]
    }
]

def run_test_scenario(scenario, results_file):
    session_id = f"test-{scenario['name'].lower().replace(' ', '-')[:15]}-{int(time.time())}"
    header = f"\n{'='*80}\n SCENARIO: {scenario['name']} \n Language: {scenario['language']} | Locale: {scenario['locale']}\n{'='*80}\n"
    print(header)
    results_file.write(header)
    
    conversation_history = []
    extracted_intel_summary = {"upi": [], "links": [], "phones": [], "accounts": [], "emails": [], "wallets": []}
    
    for i, text in enumerate(scenario['messages']):
        turn_info = f"\n[Turn {i+1}/{len(scenario['messages'])}] Scammer: \"{text}\"\n"
        print(turn_info, end="")
        results_file.write(turn_info)
        
        current_time = datetime.now(timezone.utc).isoformat()
        
        payload = {
            "sessionId": session_id,
            "message": {
                "sender": "scammer",
                "text": text,
                "timestamp": current_time
            },
            "conversationHistory": conversation_history,
            "metadata": {
                "channel": "WhatsApp",
                "language": scenario['language'],
                "locale": scenario['locale']
            }
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{API_URL}/api/message",
                json=payload,
                headers={"x-api-key": API_KEY, "Content-Type": "application/json"},
                timeout=45
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                agent_response = data.get('agentResponse', '[No response]')
                intel = data.get('extractedIntelligence', {})
                agent_notes = data.get('agentNotes', '')
                
                resp_info = f"Bot ({duration:.2f}s): \"{agent_response}\"\n"
                print(resp_info, end="")
                results_file.write(resp_info)
                
                # Track extracted intelligence
                if intel.get('upiIds'):
                    extracted_intel_summary['upi'].extend(intel['upiIds'])
                if intel.get('phishingLinks'):
                    extracted_intel_summary['links'].extend(intel['phishingLinks'])
                if intel.get('phoneNumbers'):
                    extracted_intel_summary['phones'].extend(intel['phoneNumbers'])
                if intel.get('bankAccounts'):
                    extracted_intel_summary['accounts'].extend(intel['bankAccounts'])
                if intel.get('emailAddresses'):
                    extracted_intel_summary['emails'].extend(intel['emailAddresses'])
                
                conversation_history.append({"sender": "scammer", "text": text, "timestamp": current_time})
                conversation_history.append({"sender": "honeypot", "text": agent_response, "timestamp": datetime.now(timezone.utc).isoformat()})
            else:
                error_info = f"API Error {response.status_code}: {response.text}\n"
                print(error_info)
                results_file.write(error_info)
                break 

        except Exception as e:
            err_info = f"Error: {e}\n"
            print(err_info)
            results_file.write(err_info)
            break

        if i < len(scenario['messages']) - 1:
            time.sleep(DELAY_SECONDS)

    # Print summary
    summary = f"\n--- INTELLIGENCE SUMMARY ---\n"
    summary += f"UPI IDs: {list(set(extracted_intel_summary['upi']))}\n"
    summary += f"Phishing Links: {list(set(extracted_intel_summary['links']))}\n"
    summary += f"Phone Numbers: {list(set(extracted_intel_summary['phones']))}\n"
    summary += f"Bank Accounts: {list(set(extracted_intel_summary['accounts']))}\n"
    summary += f"Emails: {list(set(extracted_intel_summary['emails']))}\n"
    summary += f"----------------------------\n"
    print(summary)
    results_file.write(summary)
    results_file.write(f"\nScenario '{scenario['name']}' Complete.\n")

def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"test_results_{timestamp}.txt"
    
    with open(filename, "w", encoding="utf-8") as f:
        print("=" * 80)
        print("  AGENTIC HONEY-POT MULTI-SCENARIO TESTER")
        print(f"  Running at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Output file: {filename}")
        print("=" * 80)
        
        f.write(f"AGENTIC HONEY-POT TEST REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Scenarios: {len(TEST_SCENARIOS)}\n")
        
        if len(sys.argv) > 1:
            try:
                choice = int(sys.argv[1])
                if 0 <= choice < len(TEST_SCENARIOS):
                    run_test_scenario(TEST_SCENARIOS[choice], f)
                else:
                    print(f"Invalid index. Use 0 to {len(TEST_SCENARIOS)-1}")
                    print("\nAvailable scenarios:")
                    for i, s in enumerate(TEST_SCENARIOS):
                        print(f"  [{i}] {s['name']}")
            except ValueError:
                print("Usage: python multi_turn_test.py [scenario_index]")
        else:
            print(f"\nRunning all {len(TEST_SCENARIOS)} scenarios...\n")
            for idx, scenario in enumerate(TEST_SCENARIOS):
                print(f"\n[{idx+1}/{len(TEST_SCENARIOS)}] Starting: {scenario['name']}")
                run_test_scenario(scenario, f)
                if idx < len(TEST_SCENARIOS) - 1:
                    print("Waiting 2 seconds before next scenario...")
                    time.sleep(2)

    print(f"\n{'='*80}")
    print(f"  ALL TESTS COMPLETE!")
    print(f"  Results saved to: {filename}")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
