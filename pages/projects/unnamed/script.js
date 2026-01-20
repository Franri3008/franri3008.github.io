
const modalOverlay = document.getElementById('modal-overlay');
const nameInput = document.getElementById('name-input');
const joinBtn = document.getElementById('join-btn');
const chatArea = document.getElementById('chat-area');
const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
const connectionStatus = document.getElementById('connection-status');

// ==========================================
// CONFIGURATION: Pantry Cloud
// ==========================================
const PANTRY_ID = "c75173ef-42bc-499b-b61e-5b8cc96e842e";
const BASKET_NAME = "franri_project_chat_data";
const PANTRY_URL = `https://getpantry.cloud/apiv1/pantry/${PANTRY_ID}/basket/${BASKET_NAME}`;

let currentUser = '';
let isSending = false;
let pollingInterval = null;

// ==========================================
// INIT
// ==========================================

function init() {
    connectionStatus.style.backgroundColor = '#eab308'; // Connecting color

    setupEventListeners();

    // Try to auto-fill name
    const savedName = sessionStorage.getItem('chat_username');
    if (savedName) {
        nameInput.value = savedName;
    }

    showModal();

    // Start trying to fetch data to ensure connection works
    fetchMessages().then(startPolling).catch(err => {
        console.warn("Initial fetch failed", err);
        // If bucket doesn't exist yet, we handle it
    });
}

// ==========================================
// CORE LOGIC (Fetch / Join / Send)
// ==========================================

async function fetchMessages() {
    try {
        const response = await fetch(PANTRY_URL, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            // If 404, it means the basket doesn't exist yet. That's fine, we'll create it on first message.
            if (response.status === 404) {
                return [];
            }
            throw new Error(`Pantry error: ${response.status}`);
        }

        const data = await response.json();
        // We expect structure: { messages: [...] }
        return data.messages || [];
    } catch (e) {
        console.error("Fetch error:", e);
        return [];
    }
}

async function joinChat() {
    const name = nameInput.value.trim();
    if (!name) {
        shakeInput();
        return;
    }

    joinBtn.disabled = true;
    joinBtn.textContent = 'Checking...';

    // 1. Get current messages to check for name validation
    const messages = await fetchMessages();

    // 2. Extract all user names sent in history (to avoid confusion/collision)
    // Note: This matches the user request "If there was already a user with that name".
    // Since we don't have a "user list", we use the "message history authors" as the list of taken names.
    const usedNames = new Set(messages.map(m => m.user));

    let finalName = name;
    let attempt = 1;

    while (usedNames.has(finalName)) {
        finalName = `${name} (${attempt})`;
        attempt++;
    }

    currentUser = finalName;
    sessionStorage.setItem('chat_username', currentUser);

    joinBtn.textContent = 'Join Chat';
    joinBtn.disabled = false;
    hideModal();

    // Render what we have immediately
    renderMessages(messages);
    connectionStatus.classList.add('connected');
    connectionStatus.style.backgroundColor = '#22c55e'; // Green
}

async function sendMessage() {
    const text = messageInput.value.trim();
    if (!text || !currentUser || isSending) return;

    isSending = true;
    sendBtn.disabled = true;

    try {
        // 1. Fetch latest state (Concurrency safety attempt)
        let messages = await fetchMessages();

        // 2. Append new message
        const newMessage = {
            user: currentUser,
            text: text,
            timestamp: Date.now()
        };

        messages.push(newMessage);

        // 3. Write back to Pantry
        // PUT replaces the entire content of the basket
        await fetch(PANTRY_URL, {
            method: 'POST', // POST merges, but since we are sending the whole 'messages' array key, it overwrites that key.
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ messages: messages })
        });

        messageInput.value = '';
        renderMessages(messages); // Update UI immediately

    } catch (e) {
        console.error("Send failed", e);
        alert("Failed to send message. Please try again.");
    } finally {
        isSending = false;
        sendBtn.disabled = false;
        messageInput.focus();
    }
}

// ==========================================
// POLLING (Simple Sync)
// ==========================================

function startPolling() {
    if (pollingInterval) clearInterval(pollingInterval);
    // Poll every 5 seconds to avoid hitting rate limits too hard but keep it responsive
    pollingInterval = setInterval(async () => {
        const messages = await fetchMessages();
        renderMessages(messages);
    }, 3000);
}

// ==========================================
// UI HELPERS
// ==========================================

let lastRenderedTime = 0;

function renderMessages(messages) {
    // Basic diffing: only append new messages based on timestamp
    // Or just clear and redraw if list is small. 
    // Optimization: find messages > lastRenderedTime

    const newMessages = messages.filter(m => m.timestamp > lastRenderedTime);

    if (newMessages.length === 0) return;

    newMessages.forEach(m => {
        displayMessage(m.user, m.text, m.timestamp);
        lastRenderedTime = m.timestamp;
    });
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
    // Only scroll if we were near bottom or if it's own message
    scrollToBottom();
}

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

init();
