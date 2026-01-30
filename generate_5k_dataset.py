
import pandas as pd
import numpy as np
import random
from datetime import datetime

# Configuration
TOTAL_ROWS = 20000
SCAM_RATIO = 0.5
LANGUAGES = ['English', 'Hinglish', 'Hindi']
CHANNELS = ['SMS', 'Email']
LOCALE = 'IN'

# Scam Types and Templates
SCAM_TEMPLATES = {
    'English': {
        'Phishing': [
            "Your account has been compromised. Click the link to verify: {link}",
            "Unusual login detected. Verify your identity at {link}",
            "URGENT: Account deletion pending. Cancel request: {link}",
            "Security Alert: Please review recent activity at {link}",
            "Your access has been restricted. Restore access: {link}"
        ],
        'Banking': [
            "Your bank account {account} is blocked. Update KYC at {link} immediately.",
            "Transaction of Rs. {amount} detected. If not you, click {link}",
            "HDFC Bank: KYC pending. Your account will be frozen. Update: {link}",
            "SBI: One time password request for Rs. {amount}. Verify: {link}",
            "ICICI: Your debit card is blocked. Reactivate: {link}"
            "Important: Your KYC is pending. Please update your PAN card details immediately to avoid account freeze. Click here: {link}"
        ],
        'Prize': [
            "Congratulations! You won Rs. {large_amount} in the Lucky Draw! Claim: {link}",
            "You are the lucky winner of an iPhone 15! Claim now: {link}",
            "Lottery Winner! Your prize of Rs. {large_amount} is waiting. Withdraw: {link}",
            "Exclusive Offer: You got a gift card worth Rs. 5000. Redeem: {link}"
        ],
         'Subscription': [
            "Your Netflix subscription is expiring. Renew now to avoid interruption: {link}",
            "Amazon Prime: Payment failed. Update payment method: {link}",
            "Hotstar: Your membership has been suspended. Reactivate: {link}"
        ],
        'Payment': [
            "Payment of Rs. {amount} failed. Update card details: {link}",
            "Bill due: Rs. {amount}. Pay immediately to avoid disconnection: {link}",
            "Electricity Bill: Last date today. Pay now: {link}"
        ],
        'Government': [
            "Your Aadhaar card is suspended. Verify now: {link}",
            "Income Tax Refund of Rs. {amount} approved. Claim: {link}",
            "PAN Card unlink alert. Link with Aadhaar immediately: {link}"
        ],
        'Social_Media': [
            "Instagram: Unusual login attempt. Secure your account: {link}",
            "Facebook: Your page will be unpublished. Verify identity: {link}",
            "WhatsApp: Verification code request. Use link if not you: {link}"
        ],
        'Malware': [
            "Virus detected on your device! Download security tool: {link}",
            "System Cleaner: Your phone is slow. Install booster: {link}",
            "Update required: Download the latest security patch: {link}"
        ],
        'Telecom': [
            "Jio: Your plan expires today. Recharge with 50% discount: {link}",
            "Airtel: 2GB data credited. Claim now: {link}",
            "Vi: Your number will be disconnected. Recharge: {link}"
        ],
         'Loan': [
            "Pre-approved Personal Loan of Rs. 5,00,000. Interest @ 9%. Apply: {link}",
            "Instant Loan approved. Disbursal in 5 mins. Click: {link}",
            "No CIBIL check loan. Get Rs. {large_amount} now: {link}"
        ],
         'Data_Request': [
            "Send your UPI ID to receive Rs. {amount} cashback.",
            "Verify your date of birth to continue: DD/MM/YYYY",
            "Reply with your OTP to confirm the transaction."
        ],
        'OTP_Request': [
             "Paytm: Share OTP {otp} to unblock your wallet.",
             "Google Pay: Enter OTP {otp} to receive cashback.",
             "Bank verify: Provide OTP {otp} to caller for KYC."
        ],
        'Urgent_Threat': [
            "Your Google account will be deleted in 24 hours.",
            "Last warning: Pay your bills or face legal action.",
            "Police verification pending. Report to station immediately."
        ]
    },
    'Hinglish': {
        'Phishing': [
            "Tera account hack ho gaya hai. Verify karne ke liye link click kar: {link}",
            "Unusual login detect hua hai. Abhi check karo: {link}",
            "Bhai, tera account band hone wala hai. Bachane ke liye click kar: {link}",
            "Jaldi kar! Security alert aaya hai. Link: {link}",
            "Access restrict ho gaya. Wapas paane ke liye: {link}"
        ],
        'Banking': [
            "Tera bank account {account} block ho gaya. KYC update kar: {link}",
            "Rs. {amount} kat gaye tere account se? Agar tu nahi tha toh click kar: {link}",
            "HDFC: KYC baaki hai. Account freeze ho jayega. Update: {link}",
            "SBI: Paisa katne wala hai. Roko isse: {link}",
            "ICICI: Debit card band. Chalo chalu karo: {link}",
            "Account band ho jayega aaj raat tak. KYC update karo link se: {link}"
        ],
        'Prize': [
            "Mubarak ho! Tu Rs. {large_amount} jeet gaya! Claim kar: {link}",
            "iPhone 15 jeetne ka mauka! Abhi click kar: {link}",
            "Lottery lagi hai bhai! Rs. {large_amount} le lo: {link}",
            "Gift card mila hai 5000 ka. Jaldi le: {link}"
        ],
        'Subscription': [
            "Netflix khatam ho raha hai. Renew kar warna band: {link}",
            "Amazon Prime: Payment fail ho gaya. Card change kar: {link}",
            "Hotstar: Membership suspend ho gayi. Wapas chalu kar: {link}"
        ],
        'Payment': [
            "Payment fail ho gaya Rs. {amount} ka. Dubara try kar: {link}",
            "Bijli ka bill bharo warna light kat jayegi: {link}",
            "Due date aaj hai. Abhi pay kar: {link}"
        ],
        'Government': [
            "Aadhaar card suspend ho gaya. Theek kar: {link}",
            "Tax Refund aaya hai Rs. {amount}. Le le: {link}",
            "PAN-Aadhaar link nahi hai. Jaldi kar: {link}"
        ],
        'Social_Media': [
             "Insta pe koi login kar raha hai. Password badal: {link}",
             "FB page delete ho jayega. Verify kar: {link}",
             "WhatsApp code kisi ko mat dena. Link check kar: {link}"
        ],
        'Malware': [
            "Virus aa gaya phone mein! Antivirus download kar: {link}",
             "Phone slow hai? Cleaner daal: {link}",
             "Security update kar jaldi: {link}"
        ],
        'Telecom': [
            "Jio plan khatam. Sasta recharge kar: {link}",
            "Free data mila hai 2GB. Claim kar: {link}",
            "Number band hone wala hai. Recharge kar: {link}"
        ],
        'Loan': [
             "Loan approve ho gaya. Rs. 5 Lakh tak. Le le: {link}",
             "Instant loan chahiye? 5 min mein milega: {link}",
             "Bina CIBIL ke loan le lo: {link}"
        ],
        'Data_Request': [
             "Apna UPI ID bhejo cashback ke liye.",
             "DOB confirm karo process ke liye.",
             "OTP batao transaction confirm karne ke liye."
        ],
         'OTP_Request': [
             "Paytm wallet kholne ke liye OTP {otp} bata.",
             "GPay cashback ke liye OTP {otp} daal.",
             "Bank call pe OTP {otp} de do KYC ke liye."
        ],
        'Urgent_Threat': [
             "Tera Google account ud jayega 24 ghante mein.",
             "Police case ho jayega agar bill nahi bhara.",
             "Thane aaja verification ke liye."
        ]
    },
    'Hindi': {
        'Phishing': [
            "आपका खाता सुरक्षित नहीं है। सत्यापित करें: {link}",
            "असामान्य लॉगिन का पता चला है। पहचान सत्यापित करें: {link}",
            "चेतावनी: आपका खाता बंद होने वाला है। रद्द करें: {link}",
            "सुरक्षा अलर्ट: हाल की गतिविधि देखें: {link}",
            "आपकी पहुंच प्रतिबंधित कर दी गई है। बहाल करें: {link}"
        ],
        'Banking': [
            "आपका बैंक खाता {account} अवरुद्ध है। तुरंत केवाईसी अपडेट करें: {link}",
            "रु. {amount} का लेनदेन हुआ। यदि आप नहीं हैं, तो क्लिक करें: {link}",
            "HDFC: केवाईसी लंबित है। आपका खाता फ्रीज कर दिया जाएगा। अपडेट: {link}",
            "SBI: वन टाइम पासवर्ड अनुरोध। सत्यापित करें: {link}",
            "ICICI: आपका डेबिट कार्ड ब्लॉक है। पुनः सक्रिय करें: {link}",
             "सूचना: आपका खाता 24 घंटे में बंद हो जाएगा। कृपया अपना पैन कार्ड अपडेट करें: {link}"
        ],
        'Prize': [
            "बधाई हो! आपने लकी ड्रॉ में रु. {large_amount} जीते हैं! दावा करें: {link}",
            "आप iPhone 15 के भाग्यशाली विजेता हैं! अभी दावा करें: {link}",
            "लॉटरी विजेता! आपका रु. {large_amount} का पुरस्कार इंतजार कर रहा है: {link}",
            "विशेष ऑफर: आपको 5000 रुपये का गिफ्ट कार्ड मिला है। भुनाएं: {link}"
        ],
        'Subscription': [
             "आपकी नेटफ्लिक्स सदस्यता समाप्त हो रही है। नवीनीकरण करें: {link}",
             "अमेज़न प्राइम: भुगतान विफल। भुगतान विधि अपडेट करें: {link}",
             "हॉटस्टार: आपकी सदस्यता निलंबित कर दी गई है। पुनः सक्रिय करें: {link}"
        ],
        'Payment': [
             "रु. {amount} का भुगतान विफल। कार्ड विवरण अपडेट करें: {link}",
             "बिजली बिल देय: रु. {amount}। अभी भुगतान करें: {link}",
             "क्रेडिट कार्ड बिल बकाया है। जुर्माना से बचने के लिए भरें: {link}"
        ],
        'Government': [
             "आपका आधार कार्ड निलंबित है। अभी सत्यापित करें: {link}",
             "आयकर रिफंड रु. {amount} स्वीकृत। दावा करें: {link}",
             "पैन कार्ड लिंक नहीं है। आधार से तुरंत लिंक करें: {link}"
        ],
        'Social_Media': [
             "इंस्टाग्राम: असामान्य लॉगिन प्रयास। अपना खाता सुरक्षित करें: {link}",
             "फेसबुक: आपका पेज हटा दिया जाएगा। पहचान सत्यापित करें: {link}",
             "व्हाट्सएप: सत्यापन कोड अनुरोध। यदि आप नहीं हैं तो लिंक का उपयोग करें: {link}"
        ],
        'Malware': [
             "आपके डिवाइस पर वायरस का पता चला! सुरक्षा उपकरण डाउनलोड करें: {link}",
             "सिस्टम क्लीनर: आपका फोन धीमा है। बूस्टर स्थापित करें: {link}",
             "अपडेट आवश्यक: नवीनतम सुरक्षा पैच डाउनलोड करें: {link}"
        ],
        'Telecom': [
             "जियो: आपका प्लान आज समाप्त हो रहा है। 50% छूट के साथ रिचार्ज करें: {link}",
             "एयरटेल: 2GB डेटा क्रेडिट किया गया। अभी दावा करें: {link}",
             "Vi: आपका नंबर काट दिया जाएगा। रिचार्ज करें: {link}"
        ],
        'Loan': [
             "रु. 5,00,000 का पूर्व-स्वीकृत व्यक्तिगत ऋण। आवेदन करें: {link}",
             "तत्काल ऋण स्वीकृत। 5 मिनट में वितरण। क्लिक करें: {link}",
             "बिना सिबिल चेक के लोन। अभी प्राप्त करें: {link}"
        ],
        'Data_Request': [
             "रु. {amount} कैशबैक प्राप्त करने के लिए अपना यूपीआई आईडी भेजें।",
             "जारी रखने के लिए अपनी जन्म तिथि सत्यापित करें: DD/MM/YYYY",
             "लेनदेन की पुष्टि के लिए अपना ओटीपी उत्तर में भेजें।"
        ],
        'OTP_Request': [
             "Paytm: अपना बटुआ अनब्लॉक करने के लिए ओटीपी {otp} साझा करें।",
             "Google Pay: कैशबैक प्राप्त करने के लिए ओटीपी {otp} दर्ज करें।",
             "बैंक सत्यापन: केवाईसी के लिए कॉल करने वाले को ओटीपी {otp} दें।"
        ],
        'Urgent_Threat': [
             "आपका गूगल खाता 24 घंटों में हटा दिया जाएगा।",
             "अंतिम चेतावनी: अपने बिलों का भुगतान करें अन्यथा कानूनी कार्रवाई का सामना करें।",
             "पुलिस सत्यापन लंबित। तुरंत थाने में रिपोर्ट करें।"
        ]
    }
}

LEGIT_TEMPLATES = {
    'English': [
        "Hey, are we still meeting for lunch today?",
        "Please find attached the invoice for your recent purchase.",
        "Your package has been delivered. Track here: {link}",
        "Reminder: Dentist appointment tomorrow at 10 AM.",
        "Happy Birthday! Hope you have a great day.",
        "Meeting agenda updated. Check email.",
        "Your statement for {month} is generated.",
        "Thank you for your feedback!",
        "OTP for login is {otp}. Do not share."
    ],
    'Hinglish': [
        "Bhai, aaj shaam ko mil rahe hain kya?",
        "Invoice attach kiya hai email mein dekh lena.",
        "Tera parcel deliver ho gaya. Check kar le.",
        "Kal subah 10 baje dentist ke paas jana hai yaad hai na?",
        "Happy Birthday bhai! Party kab de raha hai?",
        "Meeting ka time change ho gaya hai.",
        "Bill ban gaya hai is mahine ka.",
        "Feedback ke liye dhanyavad.",
        "Login OTP {otp} hai. Kisi ko mat batana."
    ],
    'Hindi': [
        "नमस्ते, क्या हम आज दोपहर के भोजन के लिए मिल रहे हैं?",
        "कृपया अपनी हालिया खरीदारी का चालान प्राप्त करें।",
        "आपका पैकेज वितरित कर दिया गया है।",
        "अनुस्मारक: कल सुबह 10 बजे दंत चिकित्सक की नियुक्ति।",
        "जन्मदिन मुबारक हो! आशा है आपका दिन मंगलमय हो।",
        "बैठक का एजेंडा अपडेट किया गया।",
        "इस महीने का आपका विवरण तैयार है।",
        "आपकी प्रतिक्रिया के लिए धन्यवाद!",
        "लॉगिन के लिए ओटीपी {otp} है। साझा न करें।"
    ]
}

# Domains and Links
MALICIOUS_DOMAINS = [
    "http://bank-secure-verify.com", "http://account-recovery.com", "http://verify-secure-account.com",
    "http://hdfc-secure.in", "http://prize-claim.com", "http://payment-update.com",
    "http://aadhaar-verify-secure.gov.in", "http://instagram-verify-secure.com", "http://facebook-verify.com",
    "http://amazon-prime-renew.com", "http://paytm-unlock.com", "http://google-play-update.com",
    "http://bit.ly/urgent-verify", "http://secure-banking.co.in", "http://account-confirm.net"
]

LEGIT_DOMAINS = [
    "https://amazon.in/orders", "https://hdfcbank.com", "https://google.com",
    "https://facebook.com", "https://instagram.com", "https://incometax.gov.in",
    "https://netflix.com", "https://hotstar.com", "https://jio.com"
]

def generate_link(is_scam):
    if is_scam:
        base = random.choice(MALICIOUS_DOMAINS)
        param = f"?token={random.randint(10000, 99999)}" if random.random() > 0.5 else f"?id={random.randint(1000, 9999)}"
        return base + param
    else:
        return random.choice(LEGIT_DOMAINS)

def generate_dataset():
    data = []
    
    # Generate Scams (2500)
    scam_count = 0
    while scam_count < TOTAL_ROWS * SCAM_RATIO:
        lang = random.choice(LANGUAGES)
        scam_type = random.choice(list(SCAM_TEMPLATES[lang].keys()))
        templates = SCAM_TEMPLATES[lang][scam_type]
        template = random.choice(templates)
        
        link_present = 1 if "{link}" in template else 0
        link = generate_link(True)
        amount = random.choice([500, 1000, 2000, 5000, 10000, 50000])
        large_amount = random.choice(["5,00,000", "10 Lakh", "1 Crore", "25,000"])
        account = "XXXX" + str(random.randint(1000, 9999))
        otp = str(random.randint(100000, 999999))
        month = datetime.now().strftime("%B")
        
        message_text = template.format(link=link, amount=amount, large_amount=large_amount, account=account, otp=otp)
        
        # Metadata
        channel = random.choice(CHANNELS)
        locale = LOCALE
        confidence = round(random.uniform(0.76, 0.97), 2)
        urgency = random.choice(["Critical", "High", "High", "Medium"]) # Weighted towards High/Critical
        keywords = "urgent,verify,account" if "account" in message_text or "verify" in message_text else "prize,claim"
        
        data.append({
            "message_id": len(data) + 1,
            "message_text": message_text,
            "label": "scam",
            "message_type": scam_type,
            "channel": channel,
            "language": lang,
            "locale": locale,
            "scam_keywords": keywords,
            "confidence_score": confidence,
            "scam_subtype": scam_type, # Using scam_type as subtype for simplicity mapping
            "link_present": link_present,
            "urgency_level": urgency
        })
        scam_count += 1

    # Generate Legitimate (2500)
    legit_count = 0
    while legit_count < TOTAL_ROWS * (1 - SCAM_RATIO):
        lang = random.choice(LANGUAGES)
        template = random.choice(LEGIT_TEMPLATES[lang])
        
        link_present = 1 if "{link}" in template else 0
        link = generate_link(False)
        otp = str(random.randint(100000, 999999))
        month = datetime.now().strftime("%B")
        
        message_text = template.format(link=link, otp=otp, month=month)
        
        channel = random.choice(CHANNELS)
        confidence = round(random.uniform(0.01, 0.06), 2)
        
        data.append({
            "message_id": len(data) + 1,
            "message_text": message_text,
            "label": "legitimate",
            "message_type": "Legitimate",
            "channel": channel,
            "language": lang,
            "locale": LOCALE,
            "scam_keywords": "",
            "confidence_score": confidence,
            "scam_subtype": "None",
            "link_present": link_present,
            "urgency_level": "None"
        })
        legit_count += 1
        
    # Shuffle
    random.shuffle(data)
    
    # Re-assign IDs
    for i, row in enumerate(data):
        row['message_id'] = i + 1
        
    df = pd.DataFrame(data)
    df.to_csv("massive_20k_scam_dataset.csv", index=False)
    print(f"Dataset generated: massive_20k_scam_dataset.csv with {len(df)} rows.")

if __name__ == "__main__":
    generate_dataset()
