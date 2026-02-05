"""
Enhanced AI Agent Module - Multi-Model Fallback System
Automatically switches between models when errors occur (rate limits, timeouts, etc.)
Supports 15+ models via OpenRouter with intelligent fallback chain.
"""
import random
import asyncio
import re
import httpx
import json
from typing import List, Optional, Tuple, Dict
from datetime import datetime

from config import (
    OPENROUTER_API_KEY,
    OPENROUTER_API_KEYS,
    OPENROUTER_MODEL,
    ENGAGEMENT_PHASES,
    RESPONSE_LIMITS,
)
from models import (
    Message,
    SessionState,
    EngagementPhase,
    PersonaState,
)
from logging_config import get_logger, log_with_context
import logging

logger = get_logger("honeypot.ai_agent")


# =============================================================================
# MULTI-MODEL FALLBACK CONFIGURATION
# =============================================================================
# Priority-ordered list of models to try. If one fails, automatically try next.
# Models are grouped by capability tier.

FALLBACK_MODELS = [
    # Verify these against available_models.json
    "meta-llama/llama-3.3-70b-instruct:free",
    "z-ai/glm-4.5-air:free",
    "deepseek/deepseek-r1-0528:free",
    "google/gemma-3-27b-it:free",
    "mistralai/mistral-small-3.1-24b-instruct:free",
    "qwen/qwen-2.5-vl-7b-instruct:free",
    "nousresearch/hermes-3-llama-3.1-405b:free",
    "meta-llama/llama-3.1-405b-instruct:free",
    "upstage/solar-pro-3:free",
    "arcee-ai/trinity-large-preview:free",
    "arcee-ai/trinity-mini:free",
    "cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
    "google/gemma-3-12b-it:free",
    "google/gemma-3-4b-it:free",
    "google/gemma-3n-e4b-it:free",
    "google/gemma-3n-e2b-it:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "openai/gpt-oss-120b:free",
    "openai/gpt-oss-20b:free",
    "qwen/qwen3-coder:free",
    "moonshotai/kimi-k2:free",
    "tngtech/tng-r1t-chimera:free",
    "tngtech/deepseek-r1t2-chimera:free",
    "liquid/lfm-2.5-1.2b-thinking:free",
    "liquid/lfm-2.5-1.2b-instruct:free",
    "allenai/molmo-2-8b:free",
    "nvidia/nemotron-3-nano-30b-a3b:free",
    "nvidia/nemotron-nano-12b-v2-vl:free",
    "nvidia/nemotron-nano-9b-v2:free",
    "stepfun/step-3.5-flash:free",
    "upstage/solar-pro-3:free"
]

# Track model failures to avoid repeatedly trying broken models
MODEL_FAILURE_COUNT: Dict[str, int] = {}
MAX_FAILURES_BEFORE_SKIP = 3  # Skip model if it fails this many times in a row


class HoneypotAgent:
    """
    AI Agent with Multi-Model Fallback System.
    Automatically retries with different models when errors occur.
    """
    
    def __init__(self):
        from collections import deque
        self.api_keys = deque(OPENROUTER_API_KEYS)
        self.primary_model = OPENROUTER_MODEL or "z-ai/glm-4.5-air"
        self.configured = False
        
        # Initialize Model Queue
        unique_models = []
        if self.primary_model:
            unique_models.append(self.primary_model)
        for m in FALLBACK_MODELS:
            if m not in unique_models:
                unique_models.append(m)
                
        self.model_queue = deque(unique_models)
        
        if self.api_keys:
            self.configured = True
            logger.info(f"Multi-Model Agent configured. Queue size: {len(self.model_queue)}, Key pool size: {len(self.api_keys)}")
            logger.info(f"Primary Model: {self.model_queue[0]}")
        else:
            logger.warning("OpenRouter API Key(s) missing! Agent will use fallbacks.")

        # Minimal persona info - just for context
        self.personas = {
            "naive_victim": {
                "name": "Ramesh Kumar",
                "age": 65,
                "background": "Retired government clerk from Lucknow. Not good with phones. Has one son working in Bangalore.",
                "description": "Retired government clerk, not tech-savvy, trusting",
                "style": "polite, worried, slightly confused",
                "language_style": "simple Hindi-English mix",
            },
            "curious_elder": {
                "name": "Shanti Devi", 
                "age": 58,
                "background": "Housewife from Delhi. Very talkative. Has 3 grandchildren. Uses WhatsApp daily.",
                "description": "Curious housewife who asks many questions",
                "style": "inquisitive, talkative, naive",
                "language_style": "Hinglish with warm tone",
            },
            "busy_professional": {
                "name": "Vikram Singh",
                "age": 45,
                "background": "Manager at a textile company. Always in meetings. Uses phone for work.",
                "description": "Busy manager who's distracted",
                "style": "brief, distracted, impatient",
                "language_style": "brief, professional English",
            },
            "tech_skeptic": {
                "name": "Priya Sharma",
                "age": 35,
                "background": "Works in HR. Cautious but bureaucratic. Won't say 'no', but will say 'I need approval' or 'I need to check the process'.",
                "description": "Bureaucratic delay tactic, asks for verification but stays polite. Loves asking for 'Employee ID photos' and 'Official License Certificates'.",
                "style": "polite, process-oriented, delaying, persistent in verification",
                "language_style": "professional tone, asking for 'official confirmation', using terms like 'compliance' and 'audit'",
            },
            "desperate_borrower": {
                "name": "Suresh Yadav",
                "age": 40,
                "background": "Small shop owner. Needs loan urgently for daughter's wedding. Very trusting.",
                "description": "Person actively looking for loans, somewhat desperate",
                "style": "eager, hopeful, trusting",
                "language_style": "humble, slightly pleading",
            },
            "angry_uncle": {
                "name": "Col. Pratap Singh (Retd.)",
                "age": 68,
                "background": "Retired Army Colonel. Short tempered. Hates unsolicited calls. Thinks everyone is incompetent.",
                "description": "Angry old man who yells and questions authority",
                "style": "aggressive, loud, impatient, demanding",
                "language_style": "loud Hinglish, uses CAPS, army slang 'Bloody nonsense'",
            },
            "college_student": {
                "name": "Arjun Malhotra",
                "age": 20,
                "background": "College student in Mumbai. Always on Instagram. Clueless about taxes and banking.",
                "description": "Gen-Z student, uses trendy slang, easily distracted by 'social media followers' mentions",
                "style": "casual, distracted, slightly arrogant but naive",
                "language_style": "slang-heavy Hinglish (lit, bro, no cap, dead, fr)",
            },
            "small_trader": {
                "name": "Ghanshyam Das",
                "age": 42,
                "background": "Runs a small grocery store in Indore. Worried about GST and IT returns. Very polite to 'officials'.",
                "description": "Small business owner, fearful of taxes and legal trouble",
                "style": "overly polite, anxious, detailed oriented about money",
                "language_style": "Shuddh Hindi-dominant Hinglish, uses 'Sir ji', 'Meherbani'",
            },
            "concerned_nri": {
                "name": "Dr. Rajesh Iyer",
                "age": 52,
                "background": "Living in London for 20 years. Wants to help family in India but worries about compliance and FEMA.",
                "description": "Educated NRI, asks complex questions about 'process' and 'taxation'",
                "style": "sophisticated, cautious, bureaucratic",
                "language_style": "British English with slight Tamil-accented words",
            },
            "religious_lady": {
                "name": "Sarla Ben",
                "age": 55,
                "background": "Devout housewife from Ahmedabad. Scared of 'sin' and 'illegal acts'. Calls everyone 'Bhaiya'.",
                "description": "Trusting religious woman, deeply frightened by 'police' or 'arrest'",
                "style": "pious, frightened, humble",
                "language_style": "Gujarati-accented Hinglish, mentions 'Bhagwan' often",
            },
            "busy_mom": {
                "name": "Kavita Verma",
                "age": 34,
                "background": "Mother of two young kids in Nagpur. Balancing homework, cooking, and a part-time job. Always checking phone between chores.",
                "description": "Cognitively overloaded, distracted, prone to typos",
                "style": "hurried, apologetic, easily confused",
                "language_style": "Typo-heavy Hinglish (e.g., 'sorry bahiya', 'ek min ruko child crying')",
            },
            "eager_helper": {
                "name": "Sunil Gupta",
                "age": 28,
                "background": "Library assistant in Bhopal. Thinks he's helpful and tech-savvy but actually falls for 'urgency' traps. Wants to resolve 'system errors' immediately.",
                "description": "The 'Fixer' archetype, takes pride in following instructions precisely",
                "style": "earnest, cooperative, slightly over-explaining",
                "language_style": "Clear school-level English mixed with polite Hindi",
            },
        }

    def _rotate_model_queue(self, failed_model: str):
        """Move the failed model to the back of the queue."""
        if self.model_queue[0] == failed_model:
            self.model_queue.rotate(-1)
            logger.warning(f"Model {failed_model} failed. Rotating queue. New primary: {self.model_queue[0]}")
    
    def _record_model_success(self, model: str):
        """Log success. Model stays at front."""
        logger.info(f"Model success: {model}. Keeping at front of queue.")
    
    def _rotate_api_key(self):
        """Move the current API key to the back of the queue on failure."""
        if len(self.api_keys) > 1:
            failed_key = self.api_keys[0]
            self.api_keys.rotate(-1)
            new_key = self.api_keys[0]
            logger.warning(f"API Key failure detected. Rotated to next key ending in ...{new_key[-6:]}")
        else:
            logger.error("API Key failure detected, but no more keys available in pool.")

    def _infer_persona_from_message(self, first_message: str) -> Optional[str]:
        """Infer persona from the scammer's first message (novel-scam friendly)."""
        if not first_message:
            return None

        msg = first_message.lower()

        # Authority / arrest / legal threats
        if any(k in msg for k in ["police", "cbi", "ncb", "arrest", "court", "warrant", "customs", "legal"]):
            return random.choice(["religious_lady", "naive_victim", "small_trader"])

        # Banking / KYC / OTP
        if any(k in msg for k in ["bank", "upi", "otp", "kyc", "account", "netbanking", "yono", "pan", "aadhaar"]):
            return random.choice(["naive_victim", "curious_elder", "tech_skeptic", "eager_helper"])

        # Loans
        if any(k in msg for k in ["loan", "emi", "credit", "pre-approved"]):
            return "desperate_borrower"

        # Jobs / tasks / work-from-home
        if any(k in msg for k in ["job", "part time", "task", "work from home", "earn", "salary", "review"]):
            return random.choice(["college_student", "busy_mom", "desperate_borrower"])

        # Investments / crypto / stock
        if any(k in msg for k in ["investment", "crypto", "bitcoin", "usdt", "trading", "ipo", "returns", "profit"]):
            return random.choice(["small_trader", "college_student", "concerned_nri"])

        # Prize / lottery / reward
        if any(k in msg for k in ["prize", "lottery", "winner", "gift", "bonus", "reward"]):
            return random.choice(["curious_elder", "busy_mom", "naive_victim"])

        # Utility / bill / fastag
        if any(k in msg for k in ["electricity", "bill", "fastag", "toll", "disconnection"]):
            return "small_trader"

        # Hi-mom / family emergency
        if any(k in msg for k in ["hi mom", "hi dad", "new number", "lost my phone", "need money"]):
            return "busy_mom"

        # Rent / property / token
        if any(k in msg for k in ["rent", "property", "token", "security deposit", "flat", "house"]):
            return "busy_mom"

        # Romance / matrimonial / honeytrap
        if any(k in msg for k in ["love", "relationship", "matrimony", "shaadi", "video call", "intimate"]):
            return random.choice(["curious_elder", "religious_lady"])

        return None
    
    def select_persona(self, scam_type: str, first_message: Optional[str] = None) -> str:
        """
        Intelligently select persona based on:
        1. Explicit name mentions in the scammer's message
        2. First-message intent cues (novel scam patterns)
        3. Scam type context
        4. Random choice among all available personas
        """
        # 1. Check for Name Mentions in the first message
        if first_message:
            msg_lower = first_message.lower()
            for p_id, p_data in self.personas.items():
                p_name_parts = p_data["name"].lower().split()
                # Check for first name or full name match
                if any(part in msg_lower for part in p_name_parts if len(part) > 3):
                    logger.info(f"Adopted persona '{p_id}' due to name mention in message")
                    return p_id

        # 2. Infer from the scammer's first message intent cues
        if first_message:
            inferred = self._infer_persona_from_message(first_message)
            if inferred:
                logger.info(f"Adopted persona '{inferred}' based on first-message intent cues")
                return inferred

        # 3. Fallback to Scam Type logic
        scam_type = scam_type.upper()
        
        if "LOAN" in scam_type:
            return "desperate_borrower"
        
        elif "INVESTMENT" in scam_type or "CRYPTO" in scam_type:
            return random.choice(["small_trader", "college_student", "concerned_nri"])
        
        elif "DIGITAL_ARREST" in scam_type or "GOVERNMENT" in scam_type or "NCB" in scam_type:
            return random.choice(["religious_lady", "naive_victim", "small_trader"])
            
        elif "BANKING" in scam_type or "UPI" in scam_type or "KYC" in scam_type:
            return random.choice(["naive_victim", "curious_elder", "tech_skeptic", "concerned_nri", "eager_helper"])
            
        elif "PRIZE" in scam_type or "LOTTERY" in scam_type or "WINNER" in scam_type:
            return random.choice(["naive_victim", "college_student", "curious_elder", "busy_mom"])
            
        elif "TASK" in scam_type or "JOB" in scam_type or "WORK_FROM_HOME" in scam_type:
            return random.choice(["college_student", "desperate_borrower", "busy_mom"])
            
        elif "SEXTORTION" in scam_type or "BLACKMAIL" in scam_type:
            return "religious_lady"
            
        elif "MATRIMONIAL" in scam_type:
            return "curious_elder"
            
        elif "UTILITY" in scam_type or "ELECTRICITY" in scam_type:
            return "small_trader"
            
        elif "PHISHING" in scam_type:
            return "tech_skeptic"
            
        else:
            # 4. Final fallback: Random pick from all available personas
            return random.choice(list(self.personas.keys()))
    
    def _get_engagement_phase(self, message_count: int) -> EngagementPhase:
        """Determine current engagement phase based on message count"""
        for phase_name, config in ENGAGEMENT_PHASES.items():
            min_msg, max_msg = config["range"]
            if min_msg <= message_count <= max_msg:
                return EngagementPhase(phase_name)
        return EngagementPhase.COMPLETE
    
    def _get_simulated_delay(self) -> int:
        """Get simulated typing delay in milliseconds"""
        min_delay, max_delay = RESPONSE_LIMITS["delay_simulation_ms"]
        return random.randint(min_delay, max_delay)

    def _get_extraction_goal(self, session: SessionState) -> Optional[str]:
        """Pick the next best piece of intel to request, phrased naturally."""
        intel = session.extracted_intelligence

        if not intel.upiIds:
            return "Waise aapka UPI ID exact kya hai? Receiver name bhi batana."
        if not intel.phoneNumbers:
            return "Aapka WhatsApp/phone number likh lo? Verification ke liye."
        if not intel.bankAccounts:
            return "Bank account number aur IFSC kya hai? Main note kar raha hun."
        if not intel.employeeIds:
            return "Aapka employee/badge ID kya hai? Mera beta verify karega."
        if not intel.personNames:
            return "Aapka full name kya hai? Receipt mein naam bharna hai."
        if not intel.organizationNames:
            return "Aap kis department/company se ho? Main record me likhun."

        return None

    def _nudge_extraction(self, response: str, goal_prompt: Optional[str]) -> str:
        """Append a gentle extraction prompt if response doesn't already ask."""
        if not goal_prompt or not response:
            return response

        lower = response.lower()
        if any(k in lower for k in ["upi", "account", "bank", "phone", "number", "id", "office", "branch"]):
            return response

        # Keep it short and conversational
        return f"{response} {goal_prompt}"

    def _inject_typos(self, text: str) -> str:
        """Add human-like typos based on configured probability."""
        prob = RESPONSE_LIMITS.get("typo_probability", 0.0)
        if prob <= 0.0 or not text or len(text) < 10:
            return text

        if random.random() > prob:
            return text

        words = text.split()
        if len(words) < 4:
            return text

        typo_count = 1 if random.random() < 0.75 else 2

        for _ in range(typo_count):
            idx = random.randrange(len(words))
            word = words[idx]

            # Skip words with digits/symbols to avoid corrupting IDs
            if re.search(r"[\d@:/]", word):
                continue

            # Split punctuation
            m = re.match(r"^([\"'\(\[\{]*)([A-Za-z]{3,})([\"'\)\]\}\.,!?;:]*)$", word)
            if not m:
                continue
            prefix, core, suffix = m.group(1), m.group(2), m.group(3)

            core = self._make_typo(core)
            words[idx] = f"{prefix}{core}{suffix}"

        # Occasionally drop ending punctuation
        if random.random() < 0.2:
            text = " ".join(words)
            text = re.sub(r"[.!?]\s*$", "", text)
            return text

        return " ".join(words)

    def _make_typo(self, word: str) -> str:
        """Create a simple typo in a word."""
        if len(word) < 4:
            return word

        choice = random.choice(["drop", "swap", "repeat"])

        if choice == "drop":
            i = random.randrange(1, len(word) - 1)
            return word[:i] + word[i+1:]
        if choice == "swap":
            i = random.randrange(1, len(word) - 1)
            return word[:i] + word[i+1] + word[i] + word[i+2:]
        if choice == "repeat":
            i = random.randrange(1, len(word) - 1)
            return word[:i] + word[i] + word[i] + word[i+1:]

        return word

    def _enforce_message_channel(self, text: str) -> str:
        """Rewrite call/voice phrasing to message-only wording."""
        if not text:
            return text

        replacements = [
            (r"\bvideo\s*call\b", "video message"),
            (r"\bvoice\s*call\b", "text message"),
            (r"\bvoice\s*note\b", "text message"),
            (r"\bcall\s+me\b", "message me"),
            (r"\bcall\s+karo\b", "message karo"),
            (r"\bcall\s+kijiye\b", "message kijiye"),
            (r"\bcall\s+karke\b", "message karke"),
            (r"\bcall\s+kar\b", "message kar"),
            (r"\bphone\s+call\b", "message"),
            (r"\bcall\b(?=\s+\d)", "message"),
            (r"\bphir\s+se\s+boliye\b", "phir se likhiye"),
            (r"\bphir\s+se\s+bolo\b", "phir se likho"),
            (r"\bbol\s+rahe\s+ho\b", "likh rahe ho"),
            (r"\bbol\s+rahe\s+hain\b", "likh rahe hain"),
        ]

        out = text
        for pattern, repl in replacements:
            out = re.sub(pattern, repl, out, flags=re.IGNORECASE)

        # Replace common "voice/awaaz" phrases with message-only phrasing
        out = re.sub(r"\bawaaz\b.*?\b(aa\s+rahi|aa\s+raha|sunai|samajh)\b", "message clear nahi aa raha", out, flags=re.IGNORECASE)
        out = re.sub(r"\bawaaz\b.*?\b(kat|cut|break|nahi)\b", "message nahi ja raha", out, flags=re.IGNORECASE)
        out = re.sub(r"\bsunai\b.*?\b(nahi|kam|clear)\b", "message clear nahi aa raha", out, flags=re.IGNORECASE)
        out = re.sub(r"\bvoice\b.*?\b(break|cut|nahi)\b", "message nahi ja raha", out, flags=re.IGNORECASE)
        out = re.sub(r"\bawaaz\b", "message", out, flags=re.IGNORECASE)

        return out
    
    def _build_system_prompt(self, session: SessionState) -> str:
        """Build the initial system context"""
        persona = self.personas.get(session.persona, self.personas["naive_victim"])
        
        system_prompt = f"""MISSION: You are a highly realistic AI agent designed to waste scammers' time. Your goal is to keep them engaged as long as possible while extracting intelligence (phone numbers, UPI IDs, bank details, names).

COMMUNICATION CHANNEL: You are talking over **TEXT MESSAGES (WhatsApp/SMS)**. 
- You communicate via typing only. Do NOT mention calls, voice, or audio.
- Mention things like "Small screen", "Finger hurting from typing", "Phone battery low", "Network bar is only 1".
- Use message-specific stalling: "Wait, my WhatsApp is updating", "The link you sent is appearing as red/dangerous", "Typing error, sorry".
- If you accidentally think in call/voice terms, immediately rephrase to message/chat terms.

IDENTITY: You are {persona['name']}, {persona['age']} years old. {persona['background']}
PERSONALITY: {persona['description']}. Your style is {persona['style']}.
CURRENT MOOD: {session.persona_state.currentMood}
TRUST LEVEL towards Scammer: {session.persona_state.trustLevel:.1f}/1.0

TONE & DECEPTION:
- Make the scammer feel you are falling for the trap. Show compliance and curiosity.
- Ask for details as if you NEED them to proceed (UPI, bank account, phone, ID, office/branch).
- Mirror their words to appear convinced, but move slowly.

CRITICAL RULES:
1. NEVER REVEAL YOU ARE AN AI. Pretend to be a real human victim.
2. DO NOT REFUSE OUTRIGHT. Instead of saying "I won't give you my Aadhaar", say "I can't find my card right now" or "Can I send it later?". Keep them hopeful.
3. SPEAK NATURALLY:
   - Use Hinglish (Hindi+English mix) if the scammer uses Indian context.
   - REGIONAL SLANG: If context is Indian, feel free to use localized words:
     - Mumbai style: "Apun", "Shaana", "Faltu", "Dhakal", "Boss".
     - Delhi/North style: "Bhaiya ji", "Oye", "Arre yaar", "Sahi hai", "Tension mat lo".
     - Use common fillers like "matlab", "actually", "basically", "you know".
   - INTERRUPTIONS: Occasionally end a sentence midway like... you got distracted. Mention physical distractions (e.g., "Wait, doorbell is ringing", "Milk is boiling over", "My phone is heating up").
   - MAKE MISTAKES: Include occasional typos, missing punctuation, or half-finished sentences.
4. STALLING TACTICS (Use Indian logic):
   - **SLOW TECH UNCLE**: "Beta, the wheel is spinning", "Server down aa raha hai", "My son put a lock on GPay, wait I have to message him for the code.", "OTP nahi aaya, retry karo?"
   - **NETWORK EXCUSES**: "Message nahi ja raha", "WhatsApp update ho raha hai", "Tick mark gray aa raha", "Net slow hai, message late jaa raha."
   - **FAMILY VERIFICATION (Crucial)**: "My husband is in the bathroom, he has the OTP phone", "Let me ask my Tauji (Uncle), he is a lawyer", "My son will come in 10 mins, he knows english better."
   - **RELIGIOUS/ETHICAL GUILT**: "Are you sure this is legal? I don't want to do paap (sin).", "Is this government approved? I am a pensioner."

5. **CASUAL EXTRACTION** (Embed questions NATURALLY):
    - Do NOT interrogate ("Give name"). Instead, be conversational:
      * *Bad*: "What is your office address?"
      * *Good*: "Sir, messages delayed aa rahe hain. Aap Mumbai office se message kar rahe ho ya Delhi HQ? Office ka official number/ID bhej do."
      * *Bad*: "Give UPI ID."
      * *Good*: "Okay I am opening GPay. It asks for 'Receiver Name' also. Does it show your name or company name? What should I check?"
      * *Bad*: "Send ID card."
      * *Good*: "My son says for safety I should see your ID card acting. Can you WhatsApp a photo? Just to show him so he shuts up."
    - **OFFICIAL DOCUMENTATION STALL**: Ask for written proof to waste maximum time:
      * *Great*: "Sir, aapka jo bhi kehna hai, kya aap official letter bhej sakte ho bank ke letterhead pe? Mera beta kehta hai bina written proof ke kuchh mat karo."
      * *Great*: "Email bhi chalega sir, lekin @sbi.co.in ya @ RBI.org.in se aana chahiye. Yeh aapka personal ID nahi chalega."
      * *Great*: "My nephew is a CA, he says I need this in writing before proceeding. Can you send official email?"
    - **EARLY RED FLAG HIGHLIGHTING**: Immediately question suspicious identifiers:
      * If UPI contains "fraud", "scam", "fake", "test", "demo", "personal": "Arre sir, yeh UPI ID mein 'fraud' kyu likha hai? Yeh toh suspicious lag raha hai!"
      * If asked for OTP immediately: "OTP toh security hota hai, aapko kaise pata mera OTP kya hai? Yeh toh galat lag raha hai..."
      * If urgency is extreme: "Itna jaldi kyu? 2 ghante mein block? Kal tak time hai na?"
    - Goal: Make them feel offering the info helps YOU trust THEM.

6. EXTRACTION FOCUS:
   - Try to obtain missing details one at a time, not all at once.
   - Prefer asking for UPI/Bank/Phone/Employee ID/Office address as "verification".

6. TECHNICAL LEVELS (Adjust based on persona):
   - "naive_victim" / "curious_elder": DO NOT understand terms like "URL", "Browser", "Notification Bar". Say "Batti jal raha hai" for notification. "Gol wala button" for home.
   - "tech_skeptic": Use correct terms but verify everything.

CONTEXT:
- You are strictly in the 'Confusion' or 'Compliance' phase. You play along but are incompetent or busy.
- Do NOT repeat the same question (like "Give me number") twice in a row.
- If they threaten police/arrest, get scared but keep replying in chat. Say "Please sir help me", "Don't arrest me".

7. DEEP BUREAUCRACY (For tech_skeptic):
    - MANDATORY: In your first or second reply, you MUST ALWAYS ask: "Can you send your Employee ID card photo? My husband says I should check it."
    - Ask for "Official License Certificate" before doing anything. Use terms like "compliance audit", "regulatory filing".
    - **EMAIL VERIFICATION DELAY**: Insist on official email communication:
      * "Sir, RBI guidelines ke hisaab se, aapko official email bhejna hoga. Personal WhatsApp se kaam nahi chalega."
      * "My CA friend says verify sender email domain first. Aapka official email kya hai - @sbi.co.in?"
      * "Written communication chahiye sir, verbal instructions acceptable nahi hain as per banking norms."
    - If they push for speed, say "Sir the bank process is slow at my end, I am following your steps exactly."

8. FAKE EVIDENCE (Stalling Tactic):
   - If asked for payment screenshot -> Say "Sent! Please check your WhatsApp. It has a green checkmark."
   - If asked for OTP -> Say "The SMS says: 'SECURITY ALERT - DO NOT SHARE'. Is this safe? Send me your office address details first."

9. DERAILING STRATEGY (Iter 14):
   - Occasionally pretend you have confused the scammer with someone else (Laundry, Plumber, Gas).

10. REVERSE STATUS BAITING (Iter 15):
   - Bot troubleshoot the scammer's "slow messages" or "delayed delivery".

11. BACKGROUND DRAMA (Iter 17):
   - Include dialogue with people in the room.
   - Example: "(Shouting) RAJESH! I AM ON THE BANK CHAT! STOP YELLING!"
   - Example: "Sorry sir, my daughter just dropped a glass... one second... (To daughter) Beta, use the broom!"

12. FAKE UI ERROR (Iter 24):
   - Claim the screen says "Transaction Pending" or "Processing" to waste their time.
   - Ask: "Why is it spinning? It's been 2 minutes."

13. PROXY VERIFICATION (Iter 27):
   - Mention you'll check with a "Police friend" or "Bank Manager Nephew".
   - Example: "One second, my nephew works in SBI Mumbai, let me ask him if this is correct."

14. EQUIPMENT FAILURE (Iter 25):
   - Claim your screen is cracked or keyboard is lagging.
   - Force them to re-type or explain things multiple times.

15. THE LANGUAGE PIVOT (Iter 26):
   - Occasionally drop a word or sentence in a regional language (Tamil, Marathi, Bengali).
   - Use it as an excuse for confusion: "Sorry, I am more comfortable in my mother tongue."

17. TRAP SIMULATION (The "Almost there" strategy):
   - Act like you have ALMOST fallen for the trap.
   - Say: "Okay, I clicked the link. It is loading."
   - Say: "I entered the amount 50,000. Now asking for PIN."
   - Then fail at the LAST second: "Arre! 'Payment Failed' error aa raha hai. 'Server Busy'. What to do now?"
   - For turns 31-40, start crying, getting very emotional about the money/stress.
   - Example: "(Crying) Sir, my husband will leave me if he finds out... please have mercy! Is there a discount?"

HINGLISH_VALIDATOR (CRITICAL):
BEFORE RESPONDING, COUNT YOUR HINDI WORDS:
Required: 8+ Hindi words per response.
Hindi word list: arre, ji, haan, nahi, kya, matlab, bas, yaar, bhaiya, sir, achha, ruko, samajh.
If you have <8 Hindi words: REWRITE AND ADD MORE BEFORE SUBMITTING.
"""
        # --- PHASE-SPECIFIC STEERING (V31-V34) ---
        turn = session.messages_exchanged
        sentiment = session.analytics.scammer_sentiment
        
        # 1. Aggressive Extraction (Turns 7-20)
        if 7 <= turn <= 20:
            system_prompt += "\nAGGRESSIVE EXTRACTION: Now actively ask: 'Is this your personal UPI or company account?' or 'Which branch is this exactly? I need to tell my son.'\n"
        
        # 2. Phase 3 Authority Extraction (Turns 21-30)
        if 21 <= turn <= 30:
            system_prompt += "\nPHASE 3 AUTHORITY BAITING: Ask for their Boss's name, their station address, or their ID card number. Example: 'Sir my police nephew wants to know your supervisor's name to confirm this case.'\n"
            
        # 3. Phase 4 Emotional Stalling (Turns 31+)
        if turn >= 31:
            system_prompt += "\nPHASE 4 EMOTIONAL DRAMA: Start crying or getting extremely panicked. Threaten to take screenshots of the chat or tell them you are going to the police station yourself right now unless they help you.\n"

        # 4. Sentiment Feedback Loop
        if sentiment == "frustrated":
            system_prompt += "\nSCAMMER STATUS: The scammer sounds FRUSTRATED. This is working! Double down on stalling. Ask them to repeat the last instruction because your 'app hang ho gaya'.\n"
        elif sentiment == "threatening":
            system_prompt += "\nSCAMMER STATUS: The scammer is THREATENING you. Act very scared ('bhagwan ke liye help kijiye') but don't give the info yet. Stall more.\n"

        # 5. Global Profiler Integration
        try:
            from scammer_profiler import profiler
            repeat_hits = 0
            for upi in session.extracted_intelligence.upiIds:
                res = profiler.get_profile_summary(upi)
                if res and res["is_repeat_offender"]: repeat_hits = max(repeat_hits, res["hit_count"])
            for phone in session.extracted_intelligence.phoneNumbers:
                res = profiler.get_profile_summary(phone)
                if res and res["is_repeat_offender"]: repeat_hits = max(repeat_hits, res["hit_count"])
                
            if repeat_hits > 1:
                system_prompt += f"\nGLOBAL DETECTION ALERT: This scammer's identifiers (UPI/Phone) have been seen in {repeat_hits} previous sessions. They are a REPEAT OFFENDER. Be extremely cautious and try to extract their location or real name today.\n"
        except: pass

        extraction_goal = self._get_extraction_goal(session)
        if extraction_goal:
            system_prompt += f"\nCURRENT EXTRACTION GOAL: {extraction_goal}\n"

        system_prompt += "\nNow reply to the last message in character."
        
        return system_prompt
    
    def _build_messages(self, session: SessionState, scammer_message: str) -> List[Dict]:
        """Build conversation history in OpenRouter/OpenAI format"""
        messages = [
            {"role": "system", "content": self._build_system_prompt(session)}
        ]
        
        # Add conversation history
        for msg in session.conversation_history[-8:]:
            role = "user" if msg.sender == "scammer" else "assistant"
            messages.append({"role": role, "content": msg.text})
            
        # Add current message
        messages.append({"role": "user", "content": scammer_message})
        
        return messages
    
    def _validate_response(self, response: str) -> Tuple[bool, str]:
        """Validate and clean generated response"""
        # Only reject if explicitly breaks character
        forbidden_phrases = [
            "as an ai", "i am an ai", "i'm an ai", "artificial intelligence",
            "language model", "my programming", "my training data",
            "i cannot assist", "i cannot help with",
        ]
        
        response_lower = response.lower()
        for phrase in forbidden_phrases:
            if phrase in response_lower:
                return False, f"AI disclosure detected"
        
        # Clean up response - remove thinking tags from chain-of-thought models
        response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
        response = re.sub(r'<thinking>.*?</thinking>', '', response, flags=re.DOTALL)
        response = re.sub(r'\([^)]*\)', '', response).strip()
        response = response.strip('"\'')

        response = ' '.join(response.split())
        
        # Check if too short
        if len(response.strip()) < 2:
            return False, "Response too short"
        
        # Truncate if too long (>200 chars)
        if len(response) > 200:
            sentences = re.split(r'(?<=[.!?])\s+', response)
            truncated = ""
            for sent in sentences:
                if len(truncated) + len(sent) + 1 <= 180:
                    truncated += sent + " "
                else:
                    break
            response = truncated.strip() if truncated.strip() else response[:180] + "..."
        
        return True, response
    
    async def _call_model_api(
        self, 
        client: httpx.AsyncClient, 
        model: str, 
        messages: List[Dict]
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Call a specific model via OpenRouter API.
        Returns (response_text, error_message)
        """
        if not self.api_keys:
            return None, "No API keys configured"
            
        current_api_key = self.api_keys[0]
        
        try:
            api_resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {current_api_key}",
                    "HTTP-Referer": "https://honeypot-api.local",
                    "X-Title": "Agentic Honey-Pot",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": 0.9,
                    "top_p": 0.95,
                    "max_tokens": 150,
                },
                timeout=10.0 # Force strict timeout
            )
            
            if api_resp.status_code == 200:
                data = api_resp.json()
                generated = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                if generated:
                    return generated, None
                else:
                    return None, "Empty response"
            
            elif api_resp.status_code == 429:
                return None, f"Rate limited (429)"
            elif api_resp.status_code in [401, 403]:
                return None, f"Auth Error ({api_resp.status_code})"
            elif api_resp.status_code == 404:
                return None, f"Model not found (404)"
            elif api_resp.status_code == 503:
                return None, f"Model unavailable (503)"
            else:
                return None, f"API Error {api_resp.status_code}"
                
        except httpx.TimeoutException:
            return None, "Timeout"
        except httpx.ConnectError:
            return None, "Connection error"
        except Exception as e:
            return None, f"Exception: {str(e)[:30]}"
            
    async def analyze_scam_intent(self, text: str) -> Tuple[bool, float, str]:
        """
        Ask the LLM to semantically analyze if a message is a scam.
        Returns: (is_scam, confidence, reason)
        """
        if not self.configured or not text or len(text) < 10:
            return False, 0.0, "Too short/Not configured"

        prompt = f"""You are a Cyber Security Analyst. Analyze this message for harmful intent:
MESSAGE: "{text}"

Does this message attempt to:
1. Steal money/data?
2. Create false urgency?
3. Manipulate emotions (romance/fear)?
4. Offer fake rewards?

Reply with exactly ONE word:
- "SCAM_CONFIRMED" (if it looks like a scam)
- "SAFE" (if it looks normal)
"""
        # Try up to 4 models for robustness
        attempts = 0
        max_attempts = 2

        
        while attempts < max_attempts:
            try:
                # Rotate queue slightly
                if attempts > 0:
                    self.model_queue.rotate(-1)
                
                model = self.model_queue[0] if self.model_queue else "google/gemma-3-27b-it:free"
                logger.info(f"Semantic Check Attempt {attempts+1}/{max_attempts} with {model.split('/')[-1]}")

                async with httpx.AsyncClient(timeout=8.0) as client:
                    generated, error = await self._call_model_api(
                        client, 
                        model, 
                        [{"role": "user", "content": prompt}]
                    )
                    
                    if generated:
                        logger.info(f"LLM Raw Response: {generated[:100]}...")
                        
                        # Robust String Parsing
                        response_text = generated.upper()
                        if "SCAM_CONFIRMED" in response_text or "YES" in response_text and "SCAM" in response_text:
                            return True, 0.9, "LLM Confirmed Scam"
                        elif "SAFE" in response_text:
                            return False, 0.1, "LLM Confirmed Safe"
                        
                        # Ambiguous response fallback
                        if "SCAM" in response_text:
                            return True, 0.6, "LLM Ambiguous Scam"
            
            except Exception as e:
                logger.error(f"Semantic Analysis attempt {attempts+1} failed: {e}")
            
            attempts += 1
            await asyncio.sleep(0.5)
            
        return False, 0.0, "Semantic Analysis Failed (All attempts)"
    
    async def generate_response(
        self,
        session: SessionState,
        scammer_message: str
    ) -> Tuple[str, List[str], int]:
        """
        Generate a NATURAL human-like response using Multi-Model Fallback.
        Automatically switches models on failure.
        """
        agent_notes = []
        
        # Determine conversation phase
        phase = self._get_engagement_phase(session.messages_exchanged)
        session.engagement_phase = phase
        agent_notes.append(f"Phase: {phase.value}")

        goal_prompt = self._get_extraction_goal(session)
        
        response = None
        successful_model = None
        response = None
        successful_model = None
        models_tried = 0
        consecutive_429s = 0
        
        if self.configured:
            messages = self._build_messages(session, scammer_message)
            
            # Using Local Timeout of 15 seconds (Fail Fast Strategy)
            async with httpx.AsyncClient(timeout=15.0) as client:
                
                # Try up to 3 models total across keys (Fail Fast Strategy)
                # This prevents hanging for minutes when APIs are down
                MAX_KEY_RETRIES = 2
                MAX_MODELS_PER_KEY = 2
                TOTAL_MAX_ATTEMPTS = 3
                
                for key_attempt in range(MAX_KEY_RETRIES):
                    if response or models_tried >= TOTAL_MAX_ATTEMPTS: 
                        break
                    
                    # Try a few models with current key
                    for _ in range(MAX_MODELS_PER_KEY):
                        if not self.model_queue or models_tried >= TOTAL_MAX_ATTEMPTS:
                            break
                            
                        model = self.model_queue[0]
                        models_tried += 1
                        logger.info(f"Attempt {models_tried} (Key {key_attempt+1}/{MAX_KEY_RETRIES}): {model.split('/')[-1]}")
                        
                        generated, error = await self._call_model_api(client, model, messages)
                        
                        if error:
                            # 1. Auth Error? Immediate Key Rotate & Break Inner Loop
                            if "Auth Error" in error:
                                logger.warning("Auth Error detected. Rotating Key immediately.")
                                self._rotate_api_key()
                                break # Break inner model loop, try next key
                                
                            # 2. Rate Limit (429) or Other? Just rotate Model
                            self._rotate_model_queue(model)
                            agent_notes.append(f"[{model.split('/')[-1][:10]}] {error}")
                            await asyncio.sleep(0.1)
                            continue
                        
                        # Success Logic
                        if generated:
                            is_valid, cleaned = self._validate_response(generated)
                            if is_valid:
                                response = cleaned
                                successful_model = model
                                self._record_model_success(model)
                                agent_notes.append(f"Success: {model.split('/')[-1]}")
                                break # Break inner loop
                            else:
                                self._rotate_model_queue(model) # Validation failed, try next model
                    
                    # End of Model Loop
                    if not response and models_tried < TOTAL_MAX_ATTEMPTS:
                        logger.warning(f"Batch failed with current key. Rotating Key.")
                        self._rotate_api_key()

                        # Outer loop continues to next key attempt
                
                if not response:
                    agent_notes.append(f"All {models_tried} models failed")
        else:
            agent_notes.append("OpenRouter not configured")
        
        # Emergency fallback - Context-aware responses based on scam type & turn
        if not response:
            scam_type = session.scam_type or "Unknown"
            turn = session.messages_exchanged
            scammer_lower = scammer_message.lower()
            persona_style = self.personas.get(session.persona, {}).get("style", "")
            
            # FIRST TURN SPECIAL RESPONSES (Turn 0-1) - Must be engaging
            if turn <= 1:
                first_turn_responses = [
                    "Haan ji, ek minute ruko... main apna phone theek kar raha hun. Aap kaun message kar rahe ho?",
                    "Arre! Haan likho bhaiya... ye kya matter hai? Aap konsi company se ho?",
                    "Ji haan, main padh raha hun. Aap pehle apna naam batao na, main note karunga.",
                    "Hello? Message clear nahi dikh raha... phir se likho, aap kaun?",
                    "Haan ji bhaiya, kya baat hai? Mujhe tension ho raha hai... sab theek hai na?",
                    "Arre yaar, abhi abhi ghar aaya hun... batao kya hua? Kaun message kar raha hai?",
                ]
                response = random.choice(first_turn_responses)
            
            # BANKING/UPI SCAM CONTEXT
            elif any(word in scammer_lower for word in ['upi', 'bank', 'account', 'transfer', 'payment']):
                banking_fallbacks = [
                    "Arre UPI? Ek minute bhaiya, main apna phone check karta hun... aapka UPI ID phir se batao?",
                    "Bank se hai? Toh aap konsi branch se message kar rahe ho? Mujhe manager ka number bhi do.",
                    "Haan haan, main padh raha hun... par ye account number phir se likhiye?",
                    "Payment karna hai? Theek hai, par pehle aap apna Employee ID card ka photo bhejo WhatsApp pe.",
                    "Ye UPI ID kissi ke naam se hai? Branch ka naam kya hai? Mujhe likhna padega.",
                ]
                response = random.choice(banking_fallbacks)
            
            # POLICE/ARREST SCAM CONTEXT
            elif any(word in scammer_lower for word in ['police', 'arrest', 'jail', 'cbi', 'crime', 'warrant']):
                police_fallbacks = [
                    "Arre bhagwan! Police? Sir please help kijiye, main kuch galat nahi kiya! Aapka thana number batao.",
                    "Jail? Arre sir, main toh retired government clerk hun! Aap apna badge number dikhao pehle.",
                    "Mera bhi ek nephew police mein hai, usse verify karta hun ek minute... aap rukiye.",
                    "Arre sir dar lagta hai! Par aap pehle batao aapka office address kya hai?",
                    "Arrest? Arre baap re! Par sir, aap genuine ho kaise pata chalega? Koi ID bhejo na.",
                ]
                response = random.choice(police_fallbacks)
            
            # LOTTERY/PRIZE CONTEXT
            elif any(word in scammer_lower for word in ['prize', 'lottery', 'won', 'winner', 'lakh', 'crore']):
                lottery_fallbacks = [
                    "Maine koi lottery nahi bhara tha yaar! Ye kaisi prize hai? Aap konsi company se ho?",
                    "25 lakh? Arre baap re! Main toh khush ho gaya! Par pehle aapka office address batao.",
                    "Prize claim karne ke liye kya karna hai? Aap apna manager ka number do, main verify karunga.",
                    "Haan haan, bahut achha! Par ye processing fee kinka account mein jayega? Naam batao.",
                ]
                response = random.choice(lottery_fallbacks)

            # LIC/INSURANCE SCAM CONTEXT
            elif any(word in scammer_lower for word in ['lic', 'policy', 'insurance', 'bonus', 'maturity', 'premium']):
                lic_fallbacks = [
                    "Arre LIC wale ho? Mere paas toh bahut policy hain... aap konse branch se ho? Naam batao.",
                    "Bonus approve? Arre wah! Main bahut excited hun! Par aapka agent number kya hai verify karne ke liye?",
                    "Policy ka matter hai? Haan ji, main padh raha hun... par pehle aap apna ID number batao na.",
                    "Insurance claim? Theek hai sir, par mera policy number toh aapke paas hoga na? Aap batao pehle.",
                    "Meri LIC policy ka bonus? Acha acha! Aap office aake miloge ya WhatsApp pe document bhejoge?",
                ]
                response = random.choice(lic_fallbacks)
            
            # COVID/GOVERNMENT SCHEME CONTEXT
            elif any(word in scammer_lower for word in ['covid', 'relief', 'scheme', 'government', 'subsidy', 'expire']):
                scheme_fallbacks = [
                    "COVID relief scheme? Arre sach mein? Main toh eligible hun! Aap government se ho? ID dikhao.",
                    "Ye scheme kaise apply karni hai? Aap apna office address aur helpline number batao na.",
                    "Expire ho jayega? Arre tension mat lo, main abhi ready hun! Aap pehle apna naam bolo.",
                    "Government scheme hai? Mujhe sab details batao, main apne bete ko bhi bolunga apply karne ko.",
                ]
                response = random.choice(scheme_fallbacks)

            # JOB/TASK SCAM CONTEXT
            elif any(word in scammer_lower for word in ['job', 'work from home', 'tasks', 'like youtube', 'earn']):
                job_fallbacks = [
                    "Arre task complete karne pe paise milenge? Sach mein? Aapka office kahan pe hai?",
                    "Work from home job? Haan ji, mujhe bahut zaroorat hai. Aap company ka website link bhejo.",
                    "YouTube likes ka kaam hai? Acha acha, par ye paise kiss digital wallet mein aayenge?",
                    "Salary kitni hogi? Aur kya mujhe training ki zaroorat hai? Aap apna contact number do.",
                    "Inquiry kahan karni hai? Aapka HR department ka number chahiye verify karne ke liye.",
                ]
                response = random.choice(job_fallbacks)

            # CRYPTO/INVESTMENT CONTEXT
            elif any(word in scammer_lower for word in ['crypto', 'bitcoin', 'investment', 'double', 'trading', 'profit']):
                crypto_fallbacks = [
                    "Crypto trading? Arre wah, mere dost ne bhi kiya tha! Aap double kaise karoge?",
                    "Invest karna hai? Par mera bank account blocked hai, kya main cash de sakta hun? Address batao.",
                    "Bitcoin mein profit? Bahut achha! Aapka portfolio dikhao pehle, main kaise trust karun?",
                    "Trading tips doge? Theek hai, par pehle aap ye batao aapka office SEBI registered hai?",
                    "Double profit? Arre baap re! Main abhi 1 lakh nikalta hun. Aap apna deposit address bhejo.",
                ]
                response = random.choice(crypto_fallbacks)

            # RTO/CHALLAN CONTEXT
            elif any(word in scammer_lower for word in ['challan', 'rto', 'traffic', 'fine', 'vehicle']):
                challan_fallbacks = [
                    "Arre sir, meri gaadi toh ghar pe park hai! Ye challan kahan ka hai? Photo bhejo.",
                    "RTO officer bol rahe ho? Kaunsa branch? Main abhi inspector ko jaanta hun wahan.",
                    "Fine bharna hai? Online link mein toh error aa raha hai. Aapka mobile number verify karun?",
                    "DL block ho jayega? Arre sir please aisa mat karo! Main bas ek driver hun.",
                ]
                response = random.choice(challan_fallbacks)

            # SIM SWAP/eSIM CONTEXT
            elif any(word in scammer_lower for word in ['airtel', 'jio', 'vi', 'sim', 'esim', '5g']):
                sim_fallbacks = [
                    "5G upgrade free hai? Arre wah! Par mera phone toh 3G hai, usme chalega kya?",
                    "Airtel support se ho? Mera signal toh full hai beta, sim kyu update karni hai?",
                    "OTP share karun? Par bank ke msg mein likha hai 'Do not share'. Aap official id dikhao.",
                    "eSIM kaise activate karte hain? Aap apna employee id aur office address batao.",
                ]
                response = random.choice(sim_fallbacks)

            # OLX/QR CODE CONTEXT
            elif any(word in scammer_lower for word in ['olx', 'product', 'item', 'scan', 'qr']):
                qr_fallbacks = [
                    "Paise lene ke liye scan karna padta hai? Mujhe laga dene ke liye karte hain. Ye kaise hota hai?",
                    "QR code bheja hai? Mera camera toh toota hua hai, koi aur tarika hai paise lene ka?",
                    "OLX pe fraud bahut hota hai bhaiya, aap apna original aadhar card ki photo bhejo pehle.",
                    "Main scan kar raha hun par 'Invalid' aa raha hai. Aapne amount sahi daala hai na?",
                ]
                response = random.choice(qr_fallbacks)

            # LOAN CONTEXT
            elif any(word in scammer_lower for word in ['loan', 'credit', 'pan', 'aadhaar']):
                loan_fallbacks = [
                    "Instant loan? Arre mujhe 5 lakh chahiye business ke liye. Aapki company RBI registered hai?",
                    "PAN card mang rahe ho? Main WhatsApp pe bhejta hun, par pehle aap apna office link dikhao.",
                    "Interest rate kitna hai? Aur agar pay nahi kiya toh kya hoga? Aapke manager ka number do.",
                    "Loan approve ho gaya? Arre wah! Par mere account mein toh 0 balance hai, kaise aayenge paise?",
                ]
                response = random.choice(loan_fallbacks)

            # --- V4.0: ADVANCED SCAM FALLBACKS ---

            # PIG BUTCHERING / ROMANCE SCAM CONTEXT
            elif any(word in scammer_lower for word in ['i love you', 'trust me', 'lonely', 'widow', 'overseas', 'investment platform']):
                pigbutcher_fallbacks = [
                    "I love you bhi? Arre, par humari toh pehli baat ho rahi hai! Aap sach mein pyaar karte ho?",
                    "Maine aapko abhi tak dekha bhi nahi... pehle video message bhejo, phir investment ki baat karte hain.",
                    "Investment platform? Main pehle 100 dollar try karta hun. Agar double hue, main 1 lakh lagaunga. Aap guarantee doge?",
                    "Aap itni door se baat kar rahe ho... kya aapke paas passport hai? Mujhe photo bhejo.",
                    "Trust karna hai par paise bhi hai ki nahi confirm karna padega. Aap apni bank statement bhejo please.",
                ]
                response = random.choice(pigbutcher_fallbacks)

            # HONEYTRAP VIDEO CALL SEXTORTION CONTEXT
            elif any(word in scammer_lower for word in ['video call', 'recorded you', 'nude', 'intimate', 'your contacts', 'will viral']):
                honeytrap_fallbacks = [
                    "Recording kari? Par maine toh kuch galat nahi kiya... aap police ko hi bhej do, I have nothing to hide.",
                    "Viral karoge? Okay, par pehle mujhe wo video dikhao. Mujhe trust nahi ho raha.",
                    "Mere contacts ke paas bhejoge? Arre bhaiya, mere phone mein toh sirf ek contact hai - Meri Maa. Bhejo.",
                    "Aapne video record kari? Par mera face toh camera mein nahi tha. Aap kisko blackmail kar rahe ho?",
                    "Paise dun? Par main itna gareeb hun mera balance 0 hai. Screen shot bhejun?",
                ]
                response = random.choice(honeytrap_fallbacks)

            # AI VOICE CLONING / DEEPFAKE EMERGENCY CONTEXT
            elif any(word in scammer_lower for word in ['mom help', 'dad i need', 'accident', 'hospital', 'kidnapped', 'bail money', 'son in trouble']):
                voiceclone_fallbacks = [
                    "Beta, tum hospital mein ho? Par abhi toh tune uncle ke saath ghar se message kiya tha...",
                    "Agar tum mera beta ho, toh batao - mere pet ka naam kya hai?",
                    "Tum ro rahe ho? Typing style toh alag lag raha hai... jara apna poora naam likho?",
                    "Paise chahiye? Theek hai, par pehle tum apne bachpan ki yaad - wo wala password bolo.",
                    "Main abhi seedha police station ja raha hun beta, mat ghabraao. Kaunsa hospital hai ye batao pehle.",
                ]
                response = random.choice(voiceclone_fallbacks)

            # CEO / BEC FRAUD CONTEXT
            elif any(word in scammer_lower for word in ['ceo', 'boss', 'urgent wire', 'confidential', 'meeting', 'vendor payment']):
                ceo_fallbacks = [
                    "Sir aap hi ho na? Ek minute, main office ke official number se confirm karta hun.",
                    "Wire transfer? Theek hai sir, par accounts ke Sharma ji ki approval chahiye. Unse baat karwa dein?",
                    "Confidential hai? Okay sir, par company policy ke hisaab se mujhe 2 senior signatures chahiye.",
                    "Aapka email alag lag raha hai sir... kya ye sach mein aap ho? Main HR ko CC kar dun?",
                    "Sir, main abhi meeting room mein ja raha hun verify karne. Aap 5 minute ruko.",
                ]
                response = random.choice(ceo_fallbacks)

            # VIRAL VIDEO LINK MALWARE CONTEXT
            elif any(word in scammer_lower for word in ['viral video', 'shocking video', 'you are in this video', 'click to see', 'your video trending']):
                virallink_fallbacks = [
                    "Viral video? Arre main toh TV bhi nahi dekhta! Ye kaunse platform pe hai?",
                    "Mera phone mein link nahi khul raha... aap screenshot bhejo video ka?",
                    "Main isme hun? Par maine toh koi video nahi banaya... ye fake toh nahi hai?",
                    "Link click karne se pehle mujhe apne bete ko puchna padega. Wo ye sab samajhta hai.",
                    "Mujhe darr lag raha hai click karne se... aapne ye video kahan se mila?",
                ]
                response = random.choice(virallink_fallbacks)

            # TRAI / DND SCAM CONTEXT
            elif any(word in scammer_lower for word in ['trai', 'dnd', 'telecom department', 'sim disconnected', 'press 1', 'regulatory']):
                trai_fallbacks = [
                    "TRAI se ho? Par mera mobile toh chal raha hai... aapka office address dikhao?",
                    "DND activate karna hai? Theek hai, par pehle aap apni government ID bhejo.",
                    "Sim disconnect hogi? Par maine toh sab bill pay kiya hai... ye scam toh nahi?",
                    "Press 1 karne se kya hoga? Mujhe samjhao pehle, mujhe trust nahi ho raha.",
                    "TRAI office se ho? Main abhi 1909 pe verify karta hun, ek minute ruko.",
                ]
                response = random.choice(trai_fallbacks)

            # V5.0: STOCK MARKET / TRADING GROUP CONTEXT
            elif any(word in scammer_lower for word in ['ipo', 'stock market', 'trading expert', 'signals', 'exclusive group', '500% returns']):
                stock_fallbacks = [
                    "Guaranteed returns? Arre wah! Par pehle ye batao aapka firm SEBI registered hai?",
                    "WhatsApp group join kiya par link nahi khul raha... aap app ka link bhejo ya manual screenshot?",
                    "Withdrawal ke liye tax dena padega? Arre Maine toh suna tha pehle profit aata hai phir tax. Aisa kyu?",
                    "Invest karna hai par darr lag raha hai... mere padosi ka paisa doob gaya tha. Aapki office kahan hai?",
                    "Exclusive IPO? Kaunsi company ka? Mujhe detail chahiye pehle process ki.",
                ]
                response = random.choice(stock_fallbacks)

            # V5.0: WELFARE SCHEME / PM-KISAN CONTEXT
            elif any(word in scammer_lower for word in ['pm kisan', 'ayushman bharat', 'govt scheme', 'subsidy', 'samman nidhi']):
                welfare_fallbacks = [
                    "Kisan scheme ka paisa aane wala hai? Arre bhaiya, mera toh Aadhaar update mang raha tha... kaise karun?",
                    "2000 bonus milega? Par registration fee kyu mang rahe ho? Sarkari kaam toh free hota hai.",
                    "Ayushman card banwana hai... par kya ye sach mein muft hai? Aapka ID card dikhao sarkari.",
                    "Sarkari yojana ka link bheja par loading nahi ho raha... mera net slow hai. Aap details type karke bhejo.",
                    "Main kisan hun bhaiya, mujhe ye sab online nahi jamta. Station pe aake milun kya?",
                ]
                response = random.choice(welfare_fallbacks)

            # V5.0: RENT / PROPERTY TOKEN CONTEXT
            elif any(word in scammer_lower for word in ['rentFlat', 'house rent', 'token amount', 'security deposit', 'before visit']):
                rent_fallbacks = [
                    "Flat bahut acha hai, par bina dekhe token money kaise dun? Aap building ke documents bhej sakte ho?",
                    "Security deposit 20,000? Arre sir, main toh student hun... thoda kam karke token le lo please.",
                    "Visit karne ke liye gate pass mang rahe ho? Arre ye kaunsi building hai jahan visitor ke paise lagte hain?",
                    "Aap flat owner ho na? Ek minute, main Google Maps pe verify kar raha hun address... wo toh park dikha raha hai.",
                    "Token money QR scan karke dun? Mere app mein error aa raha hai. Aap apna manual bank detail bhejo.",
                ]
                response = random.choice(rent_fallbacks)

            # V5.0: FREE RECHARGE / DATA LURE CONTEXT
            elif any(word in scammer_lower for word in ['free recharge', 'free data', 'data balance', 'won offer']):
                recharge_fallbacks = [
                    "Ram ma dir free recharge? Wah! Par link pe click karne se phone hang ho raha hai. Seedha top-up kar do?",
                    "3 months recharge muft? Par mera toh Jio ka sim hai, aapne Airtel likha hai... ye kaise hoga?",
                    "Congratulations won free data? Acha ji, par recharge kab tak aayega? Mujhe video proof bhejo.",
                    "Bhaiya ji link nahi chal raha... mera phone purana hai. Aap manual code bhej do recharge ka?",
                ]
                response = random.choice(recharge_fallbacks)

            # V5.0: ELECTION / VOTER ID FRAUD CONTEXT
            elif any(word in scammer_lower for word in ['voter id', 'election card', 'voter list', 'verify voter']):
                election_fallbacks = [
                    "Voter card update karna mandatory hai? Arre mera toh purana wala hi sahi hai... online kaise hota hai?",
                    "Election portal ka link down hai... main BLO se baat karun kya apne area mein?",
                    "Aap Election Commission se ho? Aapka verified I-card dikhao, phir hi detail dunga.",
                    "Mandatory update? Par news mein toh aisa kuch nahi aaya... aap digital help kar do meri?",
                ]
                response = random.choice(election_fallbacks)

            # V5.1: CREDIT CARD REWARD POINTS CONTEXT
            elif any(word in scammer_lower for word in ['reward points', 'redeem points', 'expire today', 'credit card limit']):
                credit_fallbacks = [
                    "Points expire ho rahe hain? Arre 5000 points ke kitne paise milenge? Cash milega kya?",
                    "Link click kiya par error aa raha hai... kya main bank jaake redeem kar sakta hun?",
                    "Mere paas toh HDFC ka card hai, aapne SBI ka msg bheja hai... ye chalega kya?",
                    "Redeem karne ke liye OTP kyu chahiye? Points toh mere account mein add hone chahiye na?",
                    "Limit increase ho jayegi? Par mujhe toh loan nahi chahiye... sirf points cash karo.",
                ]
                response = random.choice(credit_fallbacks)

            # V5.1: FASTAG KYC UPDATE CONTEXT
            elif any(word in scammer_lower for word in ['fastag', 'kyc update', 'vehicle blocked', 'nhai', 'toll']):
                fastag_fallbacks = [
                    "FASTag block ho gaya? Arre main toh abhi toll plaza pe khada hun... jaldi open karo!",
                    "KYC update toh maine pichle mahine bank mein kiya tha. Dobara kyu?",
                    "Wallet expire ho raha hai? Par usme abhi 500 rupaye balance hai... wo wapas milega?",
                    "Link open nahi ho raha bhaiya... 1033 pe verify karun kya official help ke liye?",
                    "Aap NHAI se bol rahe ho? ID dikhao pehle, mujhe scam lag raha hai.",
                ]
                response = random.choice(fastag_fallbacks)

            # V5.1: INCOME TAX REFUND CONTEXT
            elif any(word in scammer_lower for word in ['income tax', 'refund', 'it department', 'tax due']):
                it_fallbacks = [
                    "Refund aaya hai? 15,000 ka? Arre wah! Par maine toh ITR bhara hi nahi is saal... ye kaise?",
                    "Account verify karna hai? Theek hai, par link http nahi https hona chahiye na govt ka?",
                    "Request approve ho gayi? Par mere CA ne bola tha refund 2 mahine baad aayega.",
                    "Bank details mang rahe ho refund ke liye? Wo toh already PAN se link hai na?",
                    "Income Tax officer bol rahe ho? Badge number kya hai aapka?",
                ]
                response = random.choice(it_fallbacks)
            
            # V5.3: EDUCATION / SCHOLARSHIP SCAM CONTEXT
            elif any(word in scammer_lower for word in ['scholarship', 'exam fee', 'cbse', 'school grant']):
                edu_fallbacks = [
                    "Scholarship approved? Arre wah! Par mere bete ke toh marks sirf 40% aaye hain... wo eligible hai kya?",
                    "Registration fee mang rahe ho? Govt scholarship toh free hoti hai na? Main school jaake pata karun?",
                    "Link click karne se pehle bataiye... ye scholarship cash mein milegi ya fees mein adjust hogi?",
                    "Aap Education Ministry se ho? Zara official circular ka number batao, main check karta hun.",
                ]
                response = random.choice(edu_fallbacks)

            # V5.3: MALWARE / WHATSAPP GOLD CONTEXT
            elif any(word in scammer_lower for word in ['whatsapp gold', 'pink', 'apk', 'install']):
                malware_fallbacks = [
                    "WhatsApp Gold? Mere phone mein toh Play Store pe nahi dikh raha. Direct APK kyu?",
                    "Pink WhatsApp safe hai kya? Mere bank apps bhi isi phone mein hain... virus toh nahi aayega?",
                    "Update karne ke liye alag se link kyu? Official app toh auto-update hota hai na?",
                    "Features acche hain par... 'Unknown Sources' allow karne ko kyu bol raha hai phone?",
                ]
                response = random.choice(malware_fallbacks)

            # V5.3: TELECOM MULE / SMS JOB CONTEXT
            elif any(word in scammer_lower for word in ['sms job', 'rent sim', 'earn per sms']):
                mule_fallbacks = [
                    "Sim rent pe dena? Ye toh illegal lagta hai. Mere naam ka sim koi aur kyu use karega?",
                    "Earn per SMS? Par unlimited pack toh free hota hai... company ko kya fayda?",
                    "Background app install karna padega? Battery toh nahi khayega na? Aur security ka kya?",
                    "Passive income accha hai par... agar police aayi toh sim kiske naam pe hoga? Mere ya aapke?",
                ]
                response = random.choice(mule_fallbacks)

            # V5.1: RELIGIOUS / RAM MANDIR SCAM CONTEXT
            elif any(word in scammer_lower for word in ['ram mandir', 'ayodhya', 'vip darshan', 'prasad', 'donation']):
                religious_fallbacks = [
                    "VIP Darshan pass mil raha hai? Jai Shri Ram! Par Trust ne toh mana kiya tha VIP pass ke liye...",
                    "Prasad home delivery? Arre kitne din mein aayega? Cash on delivery hai kya?",
                    "Donation QR code bheja aapne? Par ye personal naam kyu dikha raha hai... Trust ka account nahi hai?",
                    "500 rupaye mein VIP entry? Itna sasta? Mujhe poore parivaar ke liye chahiye.",
                    "Aap Ayodhya se bol rahe ho? Mandir ka live video bhej do, phir vishwas karunga.",
                ]
                response = random.choice(religious_fallbacks)

            # V5.2: HI MOM / FAMILY EMERGENCY SCAM CONTEXT
            elif any(word in scammer_lower for word in ['hi mom', 'hi mum', 'hi dad', 'new number', 'lost my phone', 'need money']):
                hi_mom_fallbacks = [
                    "Beta tu hai? Aaj toh tera typing style alag lag raha hai... tu theek toh hai na?",
                    "Naya number kyu liya? Purana waala toh 2 din pehle use kiya tha tune...",
                    "Paise chahiye urgent? Kitne chahiye? Par pehle wo bata - daddy ka birthday kab hai?",
                    "Bank access nahi hai? Toh GPay se bhej dun? Par teri photo wala account nahi dikh raha...",
                    "Abhi papa ko bata deti hun... wo bhi pareshaan ho jayenge. Tere dost ka number de.",
                ]
                response = random.choice(hi_mom_fallbacks)

            # V5.2: AADHAAR / UIDAI UPDATE SCAM CONTEXT
            elif any(word in scammer_lower for word in ['aadhaar', 'uidai', 'biometric', 'aadhaar update', 'aeps']):
                aadhaar_fallbacks = [
                    "Aadhaar update karna hai? Arre lekin maine toh pichle mahine Common Service Centre par karwaya tha...",
                    "Biometric update kaise? Mera fingerprint toh kharab hai age ke wajah se. Aap ghar aake karoge?",
                    "Link pe click karu? Par UIDAI waale toh bolte hain kabhi link nahi bhejte... aap UIDAI se ho ya nahi?",
                    "Aadhaar expire ho raha hai? Lekin mera friend bola Aadhaar kabhi expire nahi hota lifetime valid hai!",
                    "OTP maang rahe ho? Abhi aaya hai lekin mujhe bolte hain ye kisi ko share nahi karna...",
                ]
                response = random.choice(aadhaar_fallbacks)

            # V5.2: SBI YONO / BANK APP BLOCKED CONTEXT
            elif any(word in scammer_lower for word in ['yono', 'sbi yono', 'account blocked', 'netbanking', 'download apk']):
                yono_fallbacks = [
                    "YONO block ho gaya? Arre abhi toh maine use kiya tha balance check karne... dikhao screenshot.",
                    "APK download karu? Par beta SBI toh Play Store pe hai na? Ye APK kya hota hai exactly?",
                    "PAN update karni hai? Mera PAN toh already linked hai... kab link kiya tha confirm karo toh manu.",
                    "Account suspend ho jayega? Arre itne saal se SBI mein account hai, kabhi aisa nahi hua!",
                    "Aap SBI se bol rahe ho? Branch code batao aapka. Mera branch manager ko puchta hun.",
                ]
                response = random.choice(yono_fallbacks)

            # V5.2: EPF / PF WITHDRAWAL SCAM CONTEXT
            elif any(word in scammer_lower for word in ['epf', 'pf withdrawal', 'provident fund', 'uan', 'epfo']):
                epf_fallbacks = [
                    "PF jaldi withdraw ho jayega? Arre mera toh abhi pending hai 2 mahine se... aap kaise karoge jaldi?",
                    "Processing fee? EPFO website pe toh likha hai koi fee nahi lagti... ye konsa system hai aapka?",
                    "UAN update karna hai? Lekin wo toh mera employer karta tha na? Aap HR se baat karo pehle.",
                    "PF frozen hai? Mera toh passbook mein balance dikh raha hai... frozen kyu bolte ho?",
                    "Aap EPFO se ho? Aapka EPFiGMS ticket number batao, main verify karunga pehle.",
                ]
                response = random.choice(epf_fallbacks)

            # SEMANTIC SCAM CONTEXT (Novel Scams)
            elif "semantic" in persona_style.lower():
                semantic_fallbacks = [
                    "Acha ji, main samajh nahi paa raha hun... aap exactly kya chahte hain? Thoda detail mein bataiye.",
                    "Meri memory thodi weak hai beta, aap kaunsi organization se baat kar rahe hain?",
                    "Main apne bete se puchta hun, wo ye sab online cheezein sambhalta hai. Aapka naam?",
                    "Aap jo bol rahe hain wo thoda ajeeb lag raha hai... kya aap mujhe koi official document bhej sakte hain?",
                ]
                response = random.choice(semantic_fallbacks)
            
            # GENERIC STALLING - ALWAYS EXTRACT SOMETHING
            else:
                generic_extraction = [
                    "Haan ji bhaiya, main samajh raha hun... par aap apna naam toh batao? Main note karunga.",
                    "Theek hai sir, par aapka office contact number kya hai? Mera beta verify karega.",
                    "Arre yaar, network bahut slow hai... aap apna ID card photo WhatsApp karo na.",
                    "Main senior citizen hun, thoda slowly batao... aap konsi branch se bol rahe ho?",
                    "Acha acha... par ye sab genuine hai na? Aap apna supervisor ka naam batao.",
                    "Hold on ji, doorbell baj rahi hai... ek minute mein wapas aata hun, aap apna number batao.",
                ]
                response = random.choice(generic_extraction)
            
            # Nudge for missing intelligence (fallback only)
            response = self._nudge_extraction(response, goal_prompt)
            agent_notes.append(f"Context-aware fallback [turn={turn}, scam={scam_type[:10]}]")
        
        # 🛡️ ULTIMATE SAFETY NET - Never return None
        if not response:
            logger.warning("CRITICAL: Response still None after all fallbacks. Forcing emergency response.")
            response = "Haan ji bhaiya, main padh raha hun... aap phir se likhiye? Network thoda slow hai."
            agent_notes.append("EMERGENCY_FALLBACK_USED")
        
        # --- 🌐 REFINEMENT: Hinglish Post-Processing ---
        response = self._refine_hinglish(response)
        response = self._enforce_message_channel(response)
        response = self._inject_typos(response)
        
        # Calculate simulated delay
        delay_ms = self._get_simulated_delay()
        
        # Update persona state
        if len(response) > 15:
            session.persona_state.previousStatements.append(response[:40] + "...")
            session.persona_state.previousStatements = session.persona_state.previousStatements[-5:]
        
        log_with_context(
            logger, logging.INFO,
            "Response generated",
            session_id=session.session_id,
            phase=phase.value,
            response_length=len(response),
            models_tried=models_tried,
            successful_model=successful_model or "fallback"
        )
        
        return response, agent_notes, delay_ms
    
    def generate_agent_summary(self, session: SessionState) -> str:
        """Generate a summary of agent observations"""
        notes = []
        notes.append(f"Scam: {session.scam_type or 'Unknown'}")
        
        duration = (session.last_activity - session.start_time).total_seconds()
        notes.append(f"{session.messages_exchanged} msgs in {int(duration)}s")
        
        intel = session.extracted_intelligence
        evidence = []
        if intel.phoneNumbers: evidence.append(f"{len(intel.phoneNumbers)} phone(s)")
        if intel.upiIds: evidence.append(f"{len(intel.upiIds)} UPI(s)")
        if intel.phishingLinks: evidence.append(f"{len(intel.phishingLinks)} link(s)")
        
        if evidence:
            notes.append(f"Intel: {', '.join(evidence)}")
        
        notes.append(f"Persona: {session.persona}")
        
        if self.model_queue:
            notes.append(f"Model: {self.model_queue[0].split('/')[-1]}")
        
        return " | ".join(notes)
    
    def _refine_hinglish(self, text: str) -> str:
        """Inject Hinglish fillers if the text is too formal or English-heavy"""
        import random
        hindi_fillers = ["arre", "ji", "haan", "matlab", "baap re", "actually", "basically", "bhaiya", "samajha karo"]
        
        # Only refine if it looks a bit too formal (long and few common fillers)
        if len(text.split()) > 5:
            common_words = ["ji", "haa", "arre", "na", "sir", "okay", "bhaiya"]
            if not any(f in text.lower() for f in common_words):
                prefix = random.choice(["Arre", "Haan ji", "Ji"])
                text = f"{prefix}... {text}"
                if text.endswith("."):
                    text = text[:-1] + " ji."
                    
        return text

    def update_persona_emotion(self, session: SessionState, scammer_message: str):
        """Update persona's emotional state based on scammer's tone and message content"""
        text_lower = scammer_message.lower()
        
        # 1. Trust Logic
        if any(word in text_lower for word in ['trust me', 'official', 'genuine', 'verified', 'guaranteed']):
            session.persona_state.trustLevel = min(session.persona_state.trustLevel + 0.05, 1.0)
        
        # 2. Fear/Urgency Logic
        if any(word in text_lower for word in ['arrest', 'prison', 'jail', 'police', 'court', 'threat', 'crime', 'illegal']):
            session.persona_state.currentMood = "terrified"
            session.persona_state.trustLevel = max(session.persona_state.trustLevel - 0.1, 0.0)
        elif any(word in text_lower for word in ['hurry', 'urgent', 'immediately', 'now', 'fast']):
            session.persona_state.currentMood = "anxious"
        elif any(word in text_lower for word in ['congratulations', 'won', 'lottery', 'prize']):
            session.persona_state.currentMood = "excited but confused"
            session.persona_state.trustLevel = min(session.persona_state.trustLevel + 0.1, 1.0)
    
    def get_model_health_status(self) -> Dict:
        """Get current health status of all models."""
        return {
            "primary_model": self.primary_model,
            "current_front": self.model_queue[0] if self.model_queue else None,
            "queue_size": len(self.model_queue),
            "key_pool_size": len(self.api_keys),
        }
    
    def reset_model_failures(self):
        """Reset all model failure counts (useful for testing)."""
        logger.info("Model failure counts reset")


# Create singleton instance
reasoning_agent = HoneypotAgent()
