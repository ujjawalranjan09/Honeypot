// configuration
const API_BASE_URL = ''; // Relative path for production deployment
const POLLING_INTERVAL = 2000;
const API_KEY = 'your-secret-api-key-here'; // Matches .env default

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
const statThreats = document.getElementById('stat-threats');
const statHealth = document.getElementById('stat-health');
const statIntel = document.getElementById('stat-intel');
const sessionCount = document.getElementById('session-count');

// Icons Initialization
lucide.createIcons();

// --- API Functions ---

async function fetchStats() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/health`, {
            headers: { 'X-API-Key': API_KEY }
        });
        const data = await response.json();
        
        statThreats.textContent = data.active_sessions || 0;
        sessionCount.textContent = data.active_sessions || 0;
        
        lucide.createIcons();
    } catch (error) {
        console.error('Stats fetch failed', error);
        statHealth.innerHTML = `<i data-lucide="alert-triangle" class="w-5 h-5 text-red-500"></i> Disconnected`;
        lucide.createIcons();
    }
}

async function fetchModelStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/model_status`, {
            headers: { 'X-API-Key': API_KEY }
        });
        if (response.ok) {
            const data = await response.json();
            renderModelStatus(data);
        }
    } catch (error) {
        console.error('Model status fetch failed', error);
    }
}

async function fetchSessions() {
    try {
        // Ideally we would have an endpoint listing all active session IDs
        // For now, we rely on health check active_sessions count
        // and manually tracked sessions in the UI if possible.
        // If we had /api/sessions endpoint:
        // const response = await fetch(`${API_BASE_URL}/api/sessions`, { headers: { 'X-API-Key': API_KEY } });
        // const sessions = await response.json();
        // updateSessionDropdown(sessions);
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
            if (data) {
                updateUI(data);
                // If it's a real session (not sandbox), append messages we might have missed
                // Note: Real implementation would need full history sync
            }
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
        metadata: {
            channel: "Dashboard-Sandbox",
            language: "EN",
            country: "IN"
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

function renderModelStatus(data) {
    // data = { primary_model, current_front, queue_size, key_pool_size }
    
    // 1. Overall Status
    const isHealthy = data.queue_size > 0 && data.key_pool_size > 0;
    statHealth.innerHTML = `
        <i data-lucide="${isHealthy ? 'cpu' : 'alert-circle'}" class="w-5 h-5 ${isHealthy ? 'text-green-400' : 'text-red-400'}"></i>
        <span>${isHealthy ? 'Neuro-Net Online' : 'System Degraded'}</span>
    `;

    // 2. Queue List
    modelQueueList.innerHTML = '';
    
    // Key Pool Item
    const keyItem = document.createElement('div');
    keyItem.className = 'glass p-2 flex items-center justify-between border-l-4 border-l-green-500';
    keyItem.innerHTML = `
        <span class="text-xs orbitron text-slate-400 uppercase">Key Pool</span>
        <span class="text-xs font-bold font-mono text-green-400">${data.key_pool_size || '?'} Active Keys</span>
    `;
    modelQueueList.appendChild(keyItem);

    // Current Model
    if (data.current_front) {
        const primaryItem = document.createElement('div');
        primaryItem.className = 'glass p-2 flex items-center justify-between border-l-4 border-l-violet-500';
        primaryItem.innerHTML = `
            <div>
                <p class="text-[10px] orbitron text-violet-400 uppercase">Current Model</p>
                <p class="text-xs font-mono text-slate-300 truncate w-32">${data.current_front.split('/').pop()}</p>
            </div>
            <div class="text-[10px] bg-violet-500/20 px-2 py-1 rounded text-violet-300">ACTIVE</div>
        `;
        modelQueueList.appendChild(primaryItem);
    }
    
    // Queue Stats
    const queueItem = document.createElement('div');
    queueItem.className = 'glass p-2 flex items-center justify-between border-l-4 border-l-blue-500';
    queueItem.innerHTML = `
        <span class="text-xs orbitron text-slate-400 uppercase">Fallback Queue</span>
        <span class="text-xs font-bold font-mono text-blue-400">${data.queue_size || 0} Models</span>
    `;
    modelQueueList.appendChild(queueItem);
    
    lucide.createIcons();
}

function addChatMessage(role, text) {
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${role === 'scammer' ? 'chat-scammer' : 'chat-agent'}`;
    
    // Format timestamp
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    bubble.innerHTML = `
        <div class="mb-1 text-[10px] opacity-50 uppercase tracking-wider font-bold mb-1">${role === 'scammer' ? 'Scammer Target' : 'Honeypot AI'} <span class="font-normal float-right">${time}</span></div>
        <div class="text-sm leading-relaxed whitespace-pre-wrap">${text}</div>
    `;
    
    chatContainer.appendChild(bubble);
    chatContainer.scrollTo({
        top: chatContainer.scrollHeight,
        behavior: 'smooth'
    });
}

function updateUI(data) {
    // Data check
    if (!data) return;

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
                    el.className = 'glass p-3 flex items-center justify-between group hover:border-violet-500 transition-all mb-2';
                    el.innerHTML = `
                        <div class="flex items-center gap-3 overflow-hidden">
                            <div class="p-2 bg-slate-800 rounded-full">
                                <i data-lucide="${item.icon}" class="w-4 h-4 ${item.color}"></i>
                            </div>
                            <div class="overflow-hidden">
                                <p class="text-[10px] text-slate-500 uppercase orbitron">${item.label}</p>
                                <p class="text-xs font-mono truncate text-slate-300" title="${val}">${val}</p>
                            </div>
                        </div>
                        <button class="opacity-0 group-hover:opacity-100 transition-opacity" onclick="navigator.clipboard.writeText('${val}')">
                            <i data-lucide="copy" class="w-3 h-3 text-slate-500 hover:text-white"></i>
                        </button>
                    `;
                    intelContainer.appendChild(el);
                });
            }
        });

        if (!hasData) {
            intelContainer.innerHTML = `
                <div class="flex flex-col items-center justify-center py-12 text-slate-600 space-y-2">
                    <i data-lucide="database" class="w-8 h-8 opacity-20"></i>
                    <p class="text-[10px] uppercase orbitron tracking-widest">Vault Empty</p>
                </div>
            `;
        }
        lucide.createIcons();
        
        // Update Count
        const intelCount = (intel.upiIds?.length || 0) + (intel.bankAccounts?.length || 0) + (intel.phishingLinks?.length || 0) + (intel.phoneNumbers?.length || 0);
        statIntel.innerHTML = `<span class="animate-pulse text-blue-400">${intelCount}</span>`;
    }

    // Update Frustration
    if (data.analytics && typeof data.analytics.scammerEngagementLevel !== 'undefined') {
        const frustration = Math.min(Math.max(data.analytics.scammerEngagementLevel * 100, 5), 100);
        frustrationBar.style.width = `${frustration}%`;
        
        // Color shift based on frustration
        if(frustration > 80) frustrationBar.className = "h-full bg-gradient-to-r from-red-500 to-red-600 shadow-[0_0_10px_rgba(239,68,68,0.5)]";
        else if(frustration > 50) frustrationBar.className = "h-full bg-gradient-to-r from-orange-400 to-orange-500";
        else frustrationBar.className = "h-full bg-gradient-to-r from-blue-400 to-green-400";
    }
}

// --- Event Listeners ---

sandboxToggle.addEventListener('click', () => {
    isSandboxMode = !isSandboxMode;
    sandboxToggle.classList.toggle('border-violet-500');
    sandboxToggle.classList.toggle('bg-violet-600');
    
    sandboxToggle.classList.toggle('border-green-500');
    sandboxToggle.classList.toggle('bg-green-600/30');
    sandboxToggle.classList.toggle('text-green-400');
    
    sandboxToggle.textContent = isSandboxMode ? 'Terminate Sandbox' : 'Sandbox Mode';
    sandboxInputArea.classList.toggle('hidden');
    
    if (isSandboxMode) {
        chatContainer.innerHTML = '';
        const initMsg = document.createElement('div');
        initMsg.className = 'text-center py-4 border-b border-white/10 mb-4';
        initMsg.innerHTML = '<span class="text-[10px] orbitron text-green-400 uppercase tracking-[0.2em] animate-pulse">Encryption Key: Verified // Sandbox Active</span>';
        chatContainer.appendChild(initMsg);
        
        currentSessionId = `sandbox-${Date.now()}`;
        updateUI({ extractedIntelligence: {}, analytics: { scammerEngagementLevel: 0.1 } });
        
        addChatMessage('agent', "Simulated connection established. Waiting for scammer input...");
    } else {
        chatContainer.innerHTML = `
            <div class="flex flex-col items-center justify-center h-full text-slate-500 opacity-50 space-y-4">
                <i data-lucide="activity" class="w-12 h-12"></i>
                <p class="orbitron text-xs">System Idle // Monitoring...</p>
            </div>
        `;
        currentSessionId = null;
        lucide.createIcons();
    }
});

sandboxSend.addEventListener('click', () => sendMessage(sandboxInput.value));
sandboxInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage(sandboxInput.value);
});

// --- Initialization ---

function startPolling() {
    fetchStats();
    fetchModelStatus();
    pollingIntervalId = setInterval(() => {
        fetchStats();
        fetchModelStatus();
        if (currentSessionId && !isSandboxMode) {
            fetchSessionDetail(currentSessionId);
        }
    }, POLLING_INTERVAL);
}

// Start
window.addEventListener('load', () => {
    startPolling();
});
