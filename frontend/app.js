// configuration
const API_BASE_URL = 'http://127.0.0.1:8000';
const POLLING_INTERVAL = 3000;
const API_KEY = 'YOUR_SECRET_API_KEY';

// State
let activeSessions = [];
let currentSessionId = null;
let isSandboxMode = false;
let pollingIntervalId = null;

// DOM Elements
const chatContainer = document.getElementById('chat-container');
const sessionSelect = document.getElementById('active-session-select');
const sandboxToggle = document.getElementById('sandbox-toggle');
const sandboxInputArea = document.getElementById('sandbox-input-area');
const sandboxInput = document.getElementById('sandbox-input');
const sandboxSend = document.getElementById('sandbox-send');
const intelContainer = document.getElementById('intel-container');
const frustrationBar = document.getElementById('frustration-bar');
const modelQueueList = document.getElementById('model-queue-list');

// Icons Initialization
lucide.createIcons();

// --- API Functions ---

async function fetchStats() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/health`, {
            headers: { 'X-API-Key': API_KEY }
        });
        const data = await response.json();
        
        document.getElementById('stat-threats').textContent = data.active_sessions || 0;
        document.getElementById('session-count').textContent = data.active_sessions || 0;
        document.getElementById('stat-health').innerHTML = `
            <i data-lucide="${data.gemini_configured ? 'check-circle' : 'alert-circle'}" class="w-5 h-5 ${data.gemini_configured ? 'text-green-400' : 'text-red-400'}"></i>
            ${data.gemini_configured ? 'Online' : 'Offline'}
        `;
        lucide.createIcons();
    } catch (error) {
        console.error('Stats fetch failed', error);
    }
}

async function fetchSessions() {
    try {
        const response = await fetch(`${API_BASE_URL}/api_logger/sessions`, {
            headers: { 'X-API-Key': API_KEY }
        });
        // Note: Using a mock fallback if internal logger endpoint isn't exposed
        // For hackathon, we'll poll health and use session IDs we've seen
    } catch (err) {}
}

async function fetchSessionDetail(sessionId) {
    if (!sessionId) return;
    try {
        const response = await fetch(`${API_BASE_URL}/api/session/${sessionId}`, {
            headers: { 'X-API-Key': API_KEY }
        });
        if (response.ok) {
            const data = await response.json();
            updateUI(data);
        }
    } catch (error) {
        console.error('Session detail fetch failed', error);
    }
}

async function sendMessage(text) {
    if (!text.trim()) return;
    
    // If no session exists in sandbox, create one
    if (isSandboxMode && !currentSessionId) {
        currentSessionId = `sandbox-${Date.now()}`;
    }

    const payload = {
        sessionId: currentSessionId,
        message: {
            sender: "scammer",
            text: text,
            timestamp: new Date().toISOString()
        },
        conversationHistory: [], // Server handles history tracking
        metadata: {
            channel: "Web-Sandbox",
            language: "Hinglish",
            locale: "IN"
        }
    };

    try {
        // Add user message to UI immediately
        addChatMessage('scammer', text);
        sandboxInput.value = '';

        const response = await fetch(`${API_BASE_URL}/api/message`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': API_KEY
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();
        if (data.reply) {
            addChatMessage('agent', data.reply);
            updateUI(data);
        }
    } catch (error) {
        console.error('Send message failed', error);
        addChatMessage('agent', "ERROR: Connection to neural core lost.");
    }
}

// --- UI Functions ---

function addChatMessage(role, text) {
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${role === 'scammer' ? 'chat-scammer' : 'chat-agent'}`;
    bubble.textContent = text;
    chatContainer.appendChild(bubble);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function updateUI(data) {
    // Update Intel
    const intel = data.extractedIntelligence;
    if (intel) {
        intelContainer.innerHTML = '';
        const items = [
            { label: 'UPI IDs', icon: 'credit-card', color: 'text-violet-400', list: intel.upiIds },
            { label: 'Bank A/C', icon: 'university', color: 'text-blue-400', list: intel.bankAccounts },
            { label: 'Phishing', icon: 'link', color: 'text-red-400', list: intel.phishingLinks },
            { label: 'Phones', icon: 'phone', color: 'text-green-400', list: intel.phoneNumbers }
        ];

        let hasData = false;
        items.forEach(item => {
            if (item.list && item.list.length > 0) {
                hasData = true;
                item.list.forEach(val => {
                    const el = document.createElement('div');
                    el.className = 'glass p-3 flex items-center justify-between group hover:border-blue-500 transition-all';
                    el.innerHTML = `
                        <div class="flex items-center gap-3">
                            <i data-lucide="${item.icon}" class="w-4 h-4 ${item.color}"></i>
                            <div>
                                <p class="text-[10px] text-slate-500 uppercase orbitron">${item.label}</p>
                                <p class="text-xs font-mono">${val}</p>
                            </div>
                        </div>
                        <i data-lucide="copy" class="w-3 h-3 text-slate-600 opacity-0 group-hover:opacity-100 cursor-pointer"></i>
                    `;
                    intelContainer.appendChild(el);
                });
            }
        });

        if (!hasData) {
            intelContainer.innerHTML = '<p class="text-slate-500 text-center py-8 text-xs orbitron opacity-50">Intelligence stream empty</p>';
        }
        lucide.createIcons();
    }

    // Update Frustration
    if (data.analytics && data.analytics.scammerEngagementLevel) {
        const frustration = data.analytics.scammerEngagementLevel * 100;
        frustrationBar.style.width = `${frustration}%`;
    }

    // Update Overall Intel Count
    const intelCount = (intel.upiIds?.length || 0) + (intel.bankAccounts?.length || 0) + (intel.phishingLinks?.length || 0) + (intel.phoneNumbers?.length || 0);
    document.getElementById('stat-intel').textContent = intelCount;
}

// --- Event Listeners ---

sandboxToggle.addEventListener('click', () => {
    isSandboxMode = !isSandboxMode;
    sandboxToggle.classList.toggle('bg-violet-600');
    sandboxToggle.classList.toggle('bg-green-600');
    sandboxToggle.textContent = isSandboxMode ? 'Exit Sandbox' : 'Sandbox Mode';
    sandboxInputArea.classList.toggle('hidden');
    
    if (isSandboxMode) {
        chatContainer.innerHTML = '<div class="text-center py-4 orbitron text-[10px] text-violet-400 uppercase tracking-widest border-b border-violet-900/30 mb-4 italic">Sandbox Protocol Initiated: Authorized Scammer Simulation</div>';
        currentSessionId = `sandbox-${Date.now()}`;
    } else {
        chatContainer.innerHTML = '';
        currentSessionId = null;
    }
});

sandboxSend.addEventListener('click', () => sendMessage(sandboxInput.value));
sandboxInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage(sandboxInput.value);
});

// --- Initialization ---

function startPolling() {
    fetchStats();
    pollingIntervalId = setInterval(() => {
        fetchStats();
        if (currentSessionId && !isSandboxMode) {
            fetchSessionDetail(currentSessionId);
        }
    }, POLLING_INTERVAL);
}

// Start
window.addEventListener('load', () => {
    startPolling();
});
