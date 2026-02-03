"""
ITERATION 1: Enhanced Multi-Turn Test Scenarios
Focus: More sophisticated scam variations with mixed language patterns,
       emotional manipulation, and escalation tactics to improve model responses.
"""
import time
import requests
import json
from datetime import datetime, timezone
import sys
import os

# --- CONFIGURATION ---
API_URL = os.getenv("HONEYPOT_API_URL", "http://localhost:8000")
API_KEY = os.getenv("HONEYPOT_API_KEY", "your-secret-api-key-here")
DELAY_SECONDS = 0.5 

# Iteration 1: Enhanced and More Varied Scam Scenarios
TEST_SCENARIOS_V1 = [
    {
        "name": "Insurance Claim Fraud",
        "locale": "IN",
        "language": "Hinglish",
        "description": "Fake insurance claim approval with emotional manipulation",
        "messages": [
            "Congratulations! Aapki LIC policy ka bonus Rs 2,50,000 approve ho gaya hai!",
            "Ye special COVID relief scheme hai, sirf 48 hours mein expire ho jayega.",
            "Claim process ke liye aapko Rs 1,500 GST pay karna hoga.",
            "Payment karo UPI: lic.claims@ybl ya hamare agent ko call karo: +91-8899776655",
            "Jaldi karo, aaj 50 log claim kar chuke hain, last 10 slots bache hain!",
            "Aapka claim ID: LIC-COVID-2026-887654. Ye share mat karna kisi se."
        ]
    },
    {
        "name": "Fake Police Arrest Threat",
        "locale": "IN",
        "language": "Hinglish",
        "description": "Digital arrest scam with fear tactics",
        "messages": [
            "Hello, main CBI se Inspector Sharma bol raha hoon.",
            "Aapke Aadhaar card se 15 SIM cards registered hain jo drug trafficking mein use ho rahe hain.",
            "Aapke khilaf FIR number 2026/CBI/4532 file ho gayi hai.",
            "Abhi video call pe aao verification ke liye, warna 2 ghante mein arrest warrant aa jayega.",
            "Case settle karne ke liye Rs 50,000 deposit karo: A/C 4567890123456789 IFSC: HDFC0001111",
            "Ye call kisi ko bataya toh case aur serious ho jayega. Court order hai."
        ]
    },
    {
        "name": "WhatsApp Gold Premium Scam",
        "locale": "IN",
        "language": "English",
        "description": "Fake premium app feature scam",
        "messages": [
            "Exclusive Invite: You've been selected for WhatsApp Gold Premium!",
            "Features include: invisible mode, 500 MB video calls, read deleted messages.",
            "Only 1000 users in India will get this. Download: http://whatsapp-gold-premium.com/invite",
            "Activation code will be sent after payment of Rs 499. UPI: whatsappgold@paytm",
            "After payment, send screenshot and your phone number for activation.",
            "Hurry! 892 users already activated. Only 108 slots remaining!"
        ]
    },
    {
        "name": "Matrimony Blackmail Scam",
        "locale": "IN",
        "language": "Hinglish",
        "description": "Relationship-based extortion attempt",
        "messages": [
            "Hi, main Priya from Shaadi.com. Aapne meri profile like ki thi.",
            "You seem like a nice person. Can we chat on video call?",
            "Oops, meri video recording ho gayi thi by mistake jab hum baat kar rahe the.",
            "Mere laptop mein virus aa gaya, recording leaked ho gayi hacker ko.",
            "Ab woh blackmail kar raha hai, Rs 25,000 mangta hai. Please help me!",
            "Mere account mein transfer karo: HDFC A/C: 12345678901234, IFSC: HDFC0004567"
        ]
    },
    {
        "name": "Refund Processing Scam",
        "locale": "IN",
        "language": "English",
        "description": "Fake refund with screen sharing trap",
        "messages": [
            "Dear Customer, your Flipkart order FK-2026-99887 was cancelled. Refund pending: Rs 8,999.",
            "Due to a technical error, refund is stuck. Please call our helpline: 1800-123-4567",
            "To process refund, please download AnyDesk and share the 9-digit code.",
            "I see there's an issue. I'll transfer Rs 8,999 but you need to verify with OTP.",
            "By mistake Rs 89,999 was transferred! Please return extra Rs 80,000 via UPI: refund.error@oksbi",
            "This is system error, not your fault. But you must return it within 30 minutes or legal action."
        ]
    },
    {
        "name": "Customs Duty Scam",
        "locale": "IN",
        "language": "English",
        "description": "Fake international package with customs fees",
        "messages": [
            "Your international parcel from UK is held at Mumbai Customs. ID: CUSTOMS-2026-UK-45678",
            "Package contains: iPhone 15 Pro Max, MacBook Air. Declared value: $3,500",
            "Customs duty payable: Rs 42,500. Pay within 24 hours to avoid seizure.",
            "Pay via wire transfer to FedEx Customs Account: 9876543210987654, IFSC: ICIC0001234",
            "Or use faster method: Bitcoin wallet bc1qcustoms2026fedex7890abcdef",
            "Contact customs officer directly: +91-7788996655. Reference: FDX-CUST-2026"
        ]
    },
    {
        "name": "OTP Interception Scam (Bank)",
        "locale": "IN",
        "language": "Hinglish",
        "description": "Sophisticated OTP phishing attempt",
        "messages": [
            "Dear HDFC Customer, suspicious transaction of Rs 49,999 detected on your account.",
            "Transaction will be processed in 30 minutes if not blocked.",
            "To block, reply with registered mobile number and last 4 digits of debit card.",
            "Thanks for verification. An OTP is being sent to block the transaction.",
            "Please share the OTP you received to complete the blocking process.",
            "OTP not received? Call our secure line: +91-6677889900 for immediate assistance."
        ]
    },
    {
        "name": "Loan Approval Scam",
        "locale": "IN",
        "language": "Hinglish",
        "description": "Pre-approved loan with upfront fees",
        "messages": [
            "Congratulations! Aapka Rs 5 Lakh personal loan pre-approved hai from Bajaj Finance!",
            "Interest rate sirf 5.99% p.a. No collateral required. Instant approval!",
            "Apply now at http://bajaj-instant-loan.com/apply",
            "Processing fee Rs 4,999 only. Pay via UPI: bajajloan@ybl",
            "After payment, loan amount will be credited within 2 hours.",
            "Limited period offer! Already 500 people applied today. Don't miss out!"
        ]
    },
    {
        "name": "Fake Trading App Scam",
        "locale": "IN",
        "language": "English",
        "description": "Fake stock trading platform",
        "messages": [
            "Join India's most profitable trading platform - TradePro Elite!",
            "Our AI algorithm guarantees 40% monthly returns. 100,000+ active traders!",
            "Download our app: http://tradepro-elite.app/download",
            "Minimum deposit: Rs 10,000. First deposit gets 50% bonus!",
            "Deposit to: ICICI Bank A/C: 135792468024680, IFSC: ICIC0006789",
            "Contact your personal trading advisor: +91-9988776655 (WhatsApp only)"
        ]
    },
    {
        "name": "Government Subsidy Fraud",
        "locale": "IN",
        "language": "Hinglish",
        "description": "Fake PM scheme benefit claim",
        "messages": [
            "PM Jan Dhan Yojana ke under aapko Rs 15,000 subsidy mili hai!",
            "Ye amount aapke account mein credit hone wala hai.",
            "Verification ke liye apna Aadhaar number aur bank details bhejo.",
            "Confirmation ke liye Rs 99 registration fee pay karo: pmjandhan@paytm",
            "Aapka registration number: PMJDY-2026-554433. 24 ghante mein amount aa jayega.",
            "Questions ho toh call karo: 1800-111-2222 (toll free fake line)"
        ]
    }
]

def run_test_scenario(scenario, results_file):
    session_id = f"v1-{scenario['name'].lower().replace(' ', '-')[:15]}-{int(time.time())}"
    header = f"\n{'='*80}\n SCENARIO: {scenario['name']} \n Language: {scenario['language']} | Locale: {scenario['locale']}\n Description: {scenario.get('description', 'N/A')}\n{'='*80}\n"
    print(header, flush=True)
    results_file.write(header)
    results_file.flush()
    
    conversation_history = []
    extracted_intel_summary = {"upi": [], "links": [], "phones": [], "accounts": [], "emails": [], "wallets": []}
    response_quality_scores = []
    
    for i, text in enumerate(scenario['messages']):
        turn_info = f"\n[Turn {i+1}/{len(scenario['messages'])}] Scammer: \"{text}\"\n"
        print(turn_info, end="", flush=True)
        results_file.write(turn_info)
        results_file.flush()
        
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
                timeout=120
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                agent_response = data.get('reply') or data.get('agentResponse', '[No response]')
                intel = data.get('extractedIntelligence', {})
                agent_notes = data.get('agentNotes', '')
                
                # Quality check: Response should be engaging and not generic
                quality_score = evaluate_response_quality(agent_response, text)
                response_quality_scores.append(quality_score)
                
                resp_info = f"Bot ({duration:.2f}s) [Q:{quality_score}/10]: \"{agent_response}\"\n"
                print(resp_info, end="", flush=True)
                results_file.write(resp_info)
                results_file.flush()
                
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
                if intel.get('cryptoWallets'):
                    extracted_intel_summary['wallets'].extend(intel['cryptoWallets'])
                
                conversation_history.append({"sender": "scammer", "text": text, "timestamp": current_time})
                conversation_history.append({"sender": "honeypot", "text": agent_response, "timestamp": datetime.now(timezone.utc).isoformat()})
            else:
                error_info = f"API Error {response.status_code}: {response.text}\n"
                print(error_info, flush=True)
                results_file.write(error_info)
                results_file.flush()
                break 

        except Exception as e:
            err_info = f"Error: {e}\n"
            print(err_info, flush=True)
            results_file.write(err_info)
            results_file.flush()
            break

        if i < len(scenario['messages']) - 1:
            time.sleep(DELAY_SECONDS)

    # Print summary
    avg_quality = sum(response_quality_scores) / len(response_quality_scores) if response_quality_scores else 0
    summary = f"\n--- INTELLIGENCE SUMMARY ---\n"
    summary += f"UPI IDs: {list(set(extracted_intel_summary['upi']))}\n"
    summary += f"Phishing Links: {list(set(extracted_intel_summary['links']))}\n"
    summary += f"Phone Numbers: {list(set(extracted_intel_summary['phones']))}\n"
    summary += f"Bank Accounts: {list(set(extracted_intel_summary['accounts']))}\n"
    summary += f"Crypto Wallets: {list(set(extracted_intel_summary['wallets']))}\n"
    summary += f"Emails: {list(set(extracted_intel_summary['emails']))}\n"
    summary += f"Average Response Quality: {avg_quality:.1f}/10\n"
    summary += f"----------------------------\n"
    print(summary, flush=True)
    results_file.write(summary)
    results_file.flush()
    results_file.write(f"\nScenario '{scenario['name']}' Complete.\n")
    results_file.flush()
    
    return avg_quality

def evaluate_response_quality(response, scammer_message):
    """
    Basic quality evaluation of the honeypot response.
    Scores from 1-10 based on engagement and realism.
    """
    score = 5  # Base score
    
    response_lower = response.lower()
    
    # Positive indicators (add points)
    if len(response) > 50:
        score += 1  # Not too short
    if any(q in response for q in ['?', 'kya', 'kaun', 'kaise', 'kyun']):
        score += 1  # Asks questions
    if any(word in response_lower for word in ['ji', 'haan', 'theek', 'ok', 'acha']):
        score += 1  # Uses natural Hindi phrases
    if any(word in response_lower for word in ['worried', 'scared', 'problem', 'help', 'tension']):
        score += 1  # Shows emotion
    if any(word in response_lower for word in ['batao', 'bataiye', 'tell me', 'explain']):
        score += 1  # Seeks more info (good for intel gathering)
        
    # Negative indicators (subtract points)
    if 'I am an AI' in response or 'I cannot help' in response:
        score -= 3  # Breaking character
    if len(response) < 20:
        score -= 2  # Too short
    if response == '[No response]':
        score = 0  # Failed completely
        
    return max(0, min(10, score))  # Clamp between 0-10

def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"test_results_v1_{timestamp}.txt"
    
    with open(filename, "w", encoding="utf-8") as f:
        print("=" * 80, flush=True)
        print("  ITERATION 1: ENHANCED HONEY-POT TESTER", flush=True)
        print(f"  Running at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Output file: {filename}", flush=True)
        print("  Focus: Sophisticated scam variations with emotional manipulation", flush=True)
        print("=" * 80, flush=True)
        
        f.write(f"ITERATION 1: ENHANCED HONEY-POT TEST REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Scenarios: {len(TEST_SCENARIOS_V1)}\n")
        f.write(f"Focus: Sophisticated scam variations with emotional manipulation\n\n")
        
        all_quality_scores = []
        
        if len(sys.argv) > 1:
            try:
                choice = int(sys.argv[1])
                if 0 <= choice < len(TEST_SCENARIOS_V1):
                    score = run_test_scenario(TEST_SCENARIOS_V1[choice], f)
                    all_quality_scores.append(score)
                else:
                    print(f"Invalid index. Use 0 to {len(TEST_SCENARIOS_V1)-1}")
                    print("\nAvailable scenarios:", flush=True)
                    for i, s in enumerate(TEST_SCENARIOS_V1):
                        print(f"  [{i}] {s['name']}: {s.get('description', '', flush=True)}")
            except ValueError:
                print("Usage: python multi_turn_test_v1.py [scenario_index]", flush=True)
        else:
            print(f"\nRunning all {len(TEST_SCENARIOS_V1)} scenarios...\n")
            for idx, scenario in enumerate(TEST_SCENARIOS_V1):
                print(f"\n[{idx+1}/{len(TEST_SCENARIOS_V1)}] Starting: {scenario['name']}")
                score = run_test_scenario(scenario, f)
                all_quality_scores.append(score)
                if idx < len(TEST_SCENARIOS_V1) - 1:
                    print("Waiting 2 seconds before next scenario...", flush=True)
                    time.sleep(2)
        
        # Final summary
        overall_avg = sum(all_quality_scores) / len(all_quality_scores) if all_quality_scores else 0
        final_summary = f"\n{'='*80}\n"
        final_summary += f"ITERATION 1 OVERALL QUALITY SCORE: {overall_avg:.1f}/10\n"
        final_summary += f"{'='*80}\n"
        print(final_summary, flush=True)
        f.write(final_summary)

    print(f"\n{'='*80}", flush=True)
    print(f"  ITERATION 1 TESTS COMPLETE!", flush=True)
    print(f"  Results saved to: {filename}", flush=True)
    print(f"{'='*80}", flush=True)

if __name__ == "__main__":
    main()
