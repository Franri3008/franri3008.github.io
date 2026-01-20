import { joinRoom } from 'https://cdn.skypack.dev/trystero';

const modalOverlay = document.getElementById('modal-overlay');
const nameInput = document.getElementById('name-input');
const joinBtn = document.getElementById('join-btn');
const chatArea = document.getElementById('chat-area');
const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
const connectionStatus = document.getElementById('connection-status');

// ==========================================
// Trystero Configuration (P2P Mesh)
// ==========================================
// We use a specific namespace ID to group our peers.
const APP_ID = 'franri_project_unnamed_chat_v1';
const room = joinRoom({ appId: APP_ID }, 'global_lobby');

// Actions
const [sendMessageSignal, getMessageSignal] = room.makeAction('chat');
const [checkNameSignal, getCheckNameSignal] = room.makeAction('checkName');
const [nameTakenSignal, getNameTakenSignal] = room.makeAction('nameTaken');
const [announceNameSignal, getAnnounceNameSignal] = room.makeAction('announceName');

// State
let currentUser = '';
let peerNames = {}; // peerId -> name
const myPeerId = room.selfId;

// Local History Storage
const STORAGE_KEY = 'chat_messages_v2_p2p';

// ==========================================
// Init & Listeners
// ==========================================

function init() {
    connectionStatus.style.backgroundColor = '#eab308'; // Yellow = Connecting to mesh...

    // Trystero Events
    room.onPeerJoin(peerId => {
        // When a new peer joins, tell them who we are
        if (currentUser) {
            announceNameSignal({ name: currentUser }, peerId);
        }
    });

    room.onPeerLeave(peerId => {
        if (peerNames[peerId]) {
            // Optional: User left system message
            // displaySystemMessage(`${peerNames[peerId]} left.`);
            delete peerNames[peerId];
        }
    });

    // Received a Chat Message
    getMessageSignal((data, peerId) => {
        const senderName = peerNames[peerId] || data.user || 'Unknown';
        displayMessage(senderName, data.text, data.timestamp);
    });

    // Received a Name Announcement (someone joined or introduced themselves)
    getAnnounceNameSignal((data, peerId) => {
        peerNames[peerId] = data.name;
    });

    // Received a Name Check request
    getCheckNameSignal((data, peerId) => {
        // Someone is asking if data.name is taken
        if (currentUser === data.name) {
            nameTakenSignal({ name: data.name, originalReqId: data.reqId }, peerId);
        }
    });

    // Setup UI
    setupEventListeners();

    // Load local history
    loadMessages();

    // Check session storage
    const savedName = sessionStorage.getItem('chat_username');
    if (savedName) {
        nameInput.value = savedName;
    }

    showModal();

    // Give the mesh a moment to find peers, then turn green? 
    // Trystero doesn't have a distinct "Connected" event for the whole mesh, 
    // but we can assume we are ready.
    setTimeout(() => {
        connectionStatus.style.backgroundColor = '#22c55e'; // Green
        connectionStatus.title = "Connected to P2P Swarm";
        // connectionStatus.classList.add('connected');
    }, 1000);
}

// ==========================================
// P2P Logic
// ==========================================

async function joinChat() {
    let name = nameInput.value.trim();
    if (!name) {
        shakeInput();
        return;
    }

    connectionStatus.style.backgroundColor = '#eab308'; // Checking...

    const finalName = await findAvailableName(name);

    currentUser = finalName;
    sessionStorage.setItem('chat_username', currentUser);

    // Broadcast my name to everyone to update their lists
    announceNameSignal({ name: currentUser });

    connectionStatus.style.backgroundColor = '#22c55e'; // Green
    hideModal();
}

/**
 * Iteratively checks if a name is taken by asking peers.
 * If taken, appends (x) and retries.
 */
async function findAvailableName(baseName) {
    let attempt = 0;
    let currentName = baseName;

    while (true) {
        if (attempt > 0) {
            currentName = `${baseName} (${attempt})`;
        }

        const isTaken = await checkNameInSwarm(currentName);
        if (!isTaken) {
            return currentName;
        }
        attempt++;
    }
}

function checkNameInSwarm(nameToCheck) {
    return new Promise((resolve) => {
        let taken = false;
        const reqId = Date.now() + Math.random();

        // Listen for objections
        const removeListener = getNameTakenSignal((data, peerId) => {
            if (data.name === nameToCheck && data.originalReqId === reqId) {
                taken = true;
            }
        });

        // Broadcast Check
        checkNameSignal({ name: nameToCheck, reqId: reqId });

        // Wait for responses (short timeout since P2P can be fast, but latency varies)
        // 500ms is usually enough for a LAN/fast WAN check
        setTimeout(() => {
            // Clean up listener? Trystero doesn't explicitly remove listeners easily in this API style,
            // but our logic handles ignores. 
            // Actually, `getNameTakenSignal` returns a specific listener? No. 
            // Trystero's makeAction is persistent. We need to handle the one-off logic carefully.
            // Since we can't unregister easily with the closure implementation above without a wrapper, 
            // we'll just ignore late messages in the next loop iteration.
            resolve(taken);
        }, 600);
    });
}

// ==========================================
// Logic
// ==========================================

function sendMessage() {
    const text = messageInput.value.trim();
    if (text && currentUser) {
        const timestamp = Date.now();

        // 1. Send to all peers
        sendMessageSignal({
            user: currentUser,
            text: text,
            timestamp: timestamp
        });

        // 2. Display locally
        displayMessage(currentUser, text, timestamp);
        messageInput.value = '';
    }
}

function displayMessage(user, text, timestamp) {
    const isOwn = user === currentUser;

    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${isOwn ? 'own' : 'other'}`;

    const date = new Date(timestamp);
    const timeStr = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    msgDiv.innerHTML = `
        <div class="message-header">
            <span class="sender-name">${escapeHtml(user)}</span>
            <span class="timestamp">${timeStr}</span>
        </div>
        <div class="message-content">${escapeHtml(text)}</div>
    `;

    chatArea.appendChild(msgDiv);
    scrollToBottom();

    // Save to local history
    saveMessage(user, text, timestamp);
}

function saveMessage(user, text, timestamp) {
    let history = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
    history.push({ user, text, timestamp });
    if (history.length > 50) history = history.slice(-50);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
}

function loadMessages() {
    const history = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
    history.forEach(m => displayMessage(m.user, m.text, m.timestamp));
}

// ==========================================
// UI Helpers
// ==========================================

function setupEventListeners() {
    joinBtn.addEventListener('click', joinChat);
    nameInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') joinChat();
    });
    sendBtn.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
}

function showModal() {
    modalOverlay.classList.add('active');
    nameInput.focus();
}

function hideModal() {
    modalOverlay.classList.remove('active');
    messageInput.focus();
}

function scrollToBottom() {
    chatArea.scrollTop = chatArea.scrollHeight;
}

function shakeInput() {
    nameInput.classList.add('shake');
    setTimeout(() => nameInput.classList.remove('shake'), 500);
}

function escapeHtml(text) {
    if (!text) return text;
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Start
init();
