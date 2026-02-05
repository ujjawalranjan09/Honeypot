# Honey-Pot Project: Detailed Module Logic Documentation 🛡️

**Version 5.0 "Bharat Shield"** - This document provides a deep dive into the technical logic, algorithms, and decision-making processes of the Honey-Pot system. It is intended for developers who need to understand *how* and *why* the code behaves the way it does.

---

## 1. `main.py` (The Orchestration Engine)
`main.py` is the entry point for all `/api/message` requests. It coordinates a parallel-serial hybrid detection flow.

### ⚙️ Logic Flow:
1.  **Context Pre-processing**: It extracts the `conversationHistory` and current message text.
2.  **Fast Path (Deterrence Detection)**:
    - Calls `detector.detect()`. This is a synchronous, CPU-bound operation using ML + Regex.
    - If Rules return `is_scam = True`, it skips step 3.
3.  **Smart Path (Semantic Intent Checking)**:
    - If Rules return `is_scam = False` BUT the message is longer than 20 characters (indicative of social engineering), it triggers `agent.analyze_scam_intent()`.
    - This is an **asynchronous LLM call**. It acts as a safety net for "Zero-Day" scams that don't match any known keywords.
4.  **Intelligence Extraction**:
    - `extractor.extract_intelligence()` is called to pull UPIs, Links, and IDs.
5.  **Stateful Decision**:
    - If detection (Fast or Smart) confirms a scam, the system enters **Engagement Mode**.
    - If no scam is detected, it returns a `null` reply (Silent Observer mode).
6.  **Human Simulation**:
    - Calculates a delay using a normal distribution of simulated typing speeds.
    - Uses `await asyncio.sleep(delay_ms)` to unblock the event loop while appearing human.

---

## 2. `scam_detector.py` (The Multi-Signal Classifier)
The detector uses a weighted consensus model to determine if a message is a scam.

### ⚙️ Scoring Algorithm:
The final score is calculated based on three primary signals:
- **ML Score ($S_{ML}$)**: Probability $(0.0-1.0)$ from the Gradient Boosting model.
- **Rule Score ($S_{Rule}$)**: Accumulated weight from matched keywords $(0.0-1.0 \text{ capped})$.
- **Context Score ($S_{Context}$)**: Bonus points if the scammer's behavior matches known progression patterns (e.g., asking for trust early, then urgency later).

**Final Weighted Confidence ($C$):**
$$C = (S_{ML} \times W_{ML}) + (S_{Rule} \times W_{Rule}) + (S_{Context} \times W_{Context})$$
*Default weights: $W_{ML}=0.6, W_{Rule}=0.4, W_{Context}=0.15$*

### 🚨 Kill Switch Mechanism (24 Immediate Overrides):
If certain "High-Risk Combos" are detected, the scoring algorithm is bypassed and confidence is forced to **0.85-1.0**:

**Traditional & V4.0 Kill Switches (1-19):**
- Includes Phishing, Digital Arrest, Sextortion, Job Scams, Voice Cloning, CEO Fraud, etc.

**V5.0 "Bharat Shield" Kill Switches (20-24):**
20. **Stock Market/Trading**: Exclusive IPO + Guaranteed Returns + WhatsApp Group = **0.98**
21. **Welfare Scheme**: PM-Kisan / Ayushman Bharat + Registration Fee = **0.95**
22. **Rent/Property**: Security Deposit before Visit + OLX/MagicBricks = **0.95**
23. **Free Recharge**: Congratulation Won + Free Data / Balance = **0.90**
24. **Election/Voter ID**: Mandatory Update + Voter ID link = **0.85**


### 🚨 Priority Override Logic:
To ensure accurate categorization, if a **Critical Keyword** is matched, its corresponding category takes precedence over all other scores. This prevents "Job Scams" from being miscategorized as "Sextortion" due to shared words like "videos" or "screenshots".

---

## 3. `ai_agent.py` (The Adaptive Brain)
This module is designed for **High Availability** and **Maximum Frustration**.

### ⚙️ Multi-Model Resilience Logic:
To prevent the "No Response" error seen in simple agents, this agent uses a **Retry-Rotation** loop:
1.  **Key Swapping**: If an API key hits a rate limit (429), the agent swaps to the next key in the `deque`.
2.  **Model Rotation**: If a model fails to return a response within 8 seconds, the agent picks the next model from a list of 30+ free-tier models.
3.  **Prompt Engineering**:
    - The prompt is dynamically built based on the **Engagement Phase** (Confusion, Compliance, etc.).
    - It explicitly requests the model to use **Hinglish** and make **intentional typos** (e.g., "Main check karta hunn...") to appear vulnerable and human.

### 🛡️ Contextual Fallback Library (92+ Responses):
If all 30 models fail (Total API outage), the agent inspects the `scammer_message` for keywords and selects a hardcoded, context-aware reply:
- **Banking keywords found?** $\to$ "Arre UPI? Ek minute bhaiya, mera app nahi khul raha..."
- **Police keywords found?** $\to$ "Arre baap re! Jail? Sir main toh gareeb aadmi hun..."
- **Stock Market keywords?** $\to$ "Guaranteed returns? Arre wah! Par pehle ye batao aapka firm SEBI registered hai?"
- **Welfare Scheme keywords?** $\to$ "2000 bonus milega? Par registration fee kyu mang rahe ho?"
- **Rent/Property keywords?** $\to$ "Bina dekhe token money kaise dun? Aap building ke docs bhej sakte ho?"
- **Free Recharge keywords?** $\to$ "Ram Mandir free recharge? Wah! Par link pe phone hang ho raha hai."
- **Election Fraud keywords?** $\to$ "Voter card update mandatory hai? Arre mera toh purana wala hi sahi hai..."
- **No keywords?** $\to$ Generates a generic "Wait a minute, doorbell is ringing" response.


---

## 4. `session_manager.py` (Persistence & Intelligence)
Manages the lifecycle of a scammer's experience.

### ⚙️ Lifecycle Logic:
1.  **Session Creation**: Uses a stable hashing or the provided `sessionId`.
2.  **Persona Assignment**: Randomly assigns a persona from `config.py`. Once assigned, this persona (e.g., "Angry Uncle") is saved to the session state so the bot never breaks character.
3.  **Phase Transitions**:
    - Transitions from `Confusion` $\to$ `Compliance` $\to$ `FakeInfo` based on message count and "Scammer Trust" metrics.
4.  **Automatic Completion & Callback**:
    - Once the interaction hits `MAX_MESSAGES` or the scammer stops responding for `SESSION_TIMEOUT_MINUTES`, it triggers the **GUVI Callback**.
    - The callback payload includes a summary of all extracted intelligence (UPIs, links, behavior).

---

## 5. `intelligence_extractor.py` (The Harvester)
A regex-heavy module designed to strip useful data from scammer messages.

### ⚙️ Extraction Logic:
- **UPI IDs**: Scans for patterns like `[a-zA-Z0-9.\-_]@[a-zA-Z]{3,}`.
- **Phone Numbers**: Normalizes Indian mobile formats (handling `+91`, `91`, and variations with spaces).
- **Phishing Links**: Filters out "Legit" links (google.com, licindia.in) and flags shorteners (bit.ly, tinyurl) or suspicious domains matching bank names.
- **Vehicle Numbers**: Extracts Indian plate formats (e.g., MH12AB1234, DL01CAB1234) for RTO/Challan scam tracking.
- **Employee/Agent IDs**: Captures fake credentials (e.g., AR7742, JIO/2024/1234) for impersonation pattern analysis.
- **Crypto Wallets**: Detects Bitcoin (bc1/1/3), Ethereum (0x), and USDT/TRC20 addresses.
- **Validation**: Every match is processed through a "Legit/Safe list" filter before being stored.

---

## 6. V5.0 "Bharat Shield" Summary

| Component | V4.0 | V5.0 |
|-----------|------|------|
| Kill Switches | 19 | **32** |
| Scam Categories | 19 | **33** |
| AI Fallback Responses | 68+ | **92+** |
| Intelligence Fields | 8 | **10** (+ Stock App, IPO Info) |
| Indian Environ. Hardening| Partial | **Full** (Stock, PMKisan, Rent) |

---

## Production & Deployment Notes (concise)

- Model artifacts:
  - `models/scam_detector.joblib` — trained classifier (inference only)
  - `models/tfidf_vectorizer.joblib` — TF-IDF vectorizer matching training pipeline
  - **Do not** include raw training datasets in production (they are excluded by `.vercelignore`).

- Requirements split:
  - `requirements.txt` (production): minimal runtime deps (FastAPI, uvicorn, scikit-learn, numpy, joblib, httpx).
  - `requirements-dev.txt` (optional): heavy training deps (pandas, scipy, spacy, etc.). Keep these out of deployment bundles.

- Training (local/CI):
  - Use `train_all_datasets.py` locally or on a GPU-equipped CI instance.
  - Example:
    ```bash
    python train_all_datasets.py --save-path=models/
    ```
  - After training, validate with `test_model.py` and commit only the generated `joblib` artifacts.

- Inference best-practices:
  - Lazy-import heavy modules used only for training (e.g., `pandas`) to keep function cold-start small.
  - Keep model loading in a module-level lazy initializer so subsequent requests reuse the model.

- Vercel-specific guidance:
  - Use `vercel.json` `includeFiles` to ensure `models/**` is bundled and `excludeFiles` to keep datasets out.
  - Enable `VERCEL_BUILDER_DEBUG=1` to inspect function sizes during debugging.

- Health checks & tests:
  - `GET /api/health` — basic liveness
  - `python test_model.py` — checks model + vectorizer load and run sample predictions
  - `python test_detector.py` — end-to-end detector pipeline test

---

If you want, I can also add a small `requirements-dev.txt` and a CI job to run training-only workflows (separate from production builds).

