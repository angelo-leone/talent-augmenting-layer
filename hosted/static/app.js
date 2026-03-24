/**
 * Talent-Augmenting Layer -- Assessment Chat UI
 *
 * Handles the conversational assessment flow: sending messages to the API,
 * rendering responses with basic markdown, and handling assessment completion.
 */

// ── State ──────────────────────────────────────────────────────────────────

let sessionId = null;
let isSending = false;
let messageCount = 0;
const TOTAL_EXPECTED_MESSAGES = 24; // ~20 assistant turns + user turns

// ── DOM helpers ────────────────────────────────────────────────────────────

function $(selector) { return document.querySelector(selector); }

function scrollToBottom() {
    const area = $('#chat-area');
    if (area) area.scrollTop = area.scrollHeight;
}

function updateProgress() {
    const pct = Math.min(100, Math.round((messageCount / TOTAL_EXPECTED_MESSAGES) * 100));
    const fill = $('#progress-fill');
    const label = $('#progress-label');
    if (fill) fill.style.width = pct + '%';
    if (label) {
        if (pct < 20) label.textContent = 'Getting started...';
        else if (pct < 40) label.textContent = 'AI dependency assessment...';
        else if (pct < 60) label.textContent = 'Growth potential...';
        else if (pct < 75) label.textContent = 'AI literacy...';
        else if (pct < 90) label.textContent = 'Expertise mapping...';
        else label.textContent = 'Finishing up...';
    }
}

// ── Markdown rendering (lightweight) ──────────────────────────────────────

function renderMarkdown(text) {
    // Very basic markdown-to-HTML for chat messages
    let html = text
        // Escape HTML
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        // Bold
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        // Italic
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        // Inline code
        .replace(/`(.+?)`/g, '<code>$1</code>')
        // Line breaks -> paragraphs
        .split('\n\n').join('</p><p>')
        // Single line breaks
        .replace(/\n/g, '<br>');

    return '<p>' + html + '</p>';
}

// ── Message rendering ─────────────────────────────────────────────────────

function addMessage(role, content) {
    const area = $('#chat-area');
    if (!area) return;

    const div = document.createElement('div');
    div.className = 'chat-msg ' + (role === 'user' ? 'chat-msg-user' : 'chat-msg-ai');

    if (role === 'user') {
        div.textContent = content;
    } else {
        div.innerHTML = renderMarkdown(content);
    }

    area.appendChild(div);
    scrollToBottom();
}

function showTyping() {
    const area = $('#chat-area');
    if (!area) return;
    const div = document.createElement('div');
    div.className = 'chat-typing';
    div.id = 'typing-indicator';
    div.textContent = 'Thinking...';
    area.appendChild(div);
    scrollToBottom();
}

function hideTyping() {
    const el = $('#typing-indicator');
    if (el) el.remove();
}

// ── API calls ──────────────────────────────────────────────────────────────

async function sendMessage() {
    if (isSending) return;

    const input = $('#user-input');
    const message = input.value.trim();
    if (!message) return;

    isSending = true;
    const sendBtn = $('#send-btn');
    if (sendBtn) sendBtn.disabled = true;

    // Show user message
    addMessage('user', message);
    input.value = '';
    input.style.height = 'auto';
    messageCount++;
    updateProgress();

    // Show typing indicator
    showTyping();

    try {
        const payload = { message, session_id: sessionId };
        const res = await fetch('/api/assess/message', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });

        hideTyping();

        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            addMessage('assistant', 'Something went wrong: ' + (err.detail || 'Unknown error'));
            return;
        }

        const data = await res.json();
        sessionId = data.session_id;
        messageCount++;
        updateProgress();

        // Show AI response
        addMessage('assistant', data.reply);

        // Check if assessment is complete
        if (data.is_complete) {
            showCompletionUI();
        }
    } catch (err) {
        hideTyping();
        addMessage('assistant', 'Network error. Please check your connection and try again.');
    } finally {
        isSending = false;
        if (sendBtn) sendBtn.disabled = false;
        input.focus();
    }
}

function showCompletionUI() {
    const inputArea = $('#input-area');
    const completeArea = $('#complete-area');
    if (inputArea) inputArea.classList.add('hidden');
    if (completeArea) completeArea.classList.remove('hidden');

    const fill = $('#progress-fill');
    if (fill) fill.style.width = '100%';
    const label = $('#progress-label');
    if (label) label.textContent = 'Assessment complete!';
}

async function completeAssessment() {
    if (!sessionId) {
        alert('No active session. Please refresh and try again.');
        return;
    }

    const btn = $('#complete-btn');
    const status = $('#complete-status');
    if (btn) btn.disabled = true;
    if (status) status.textContent = 'Generating your profile... this may take a moment.';

    try {
        const res = await fetch('/api/assess/complete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId }),
        });

        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            if (status) status.textContent = 'Error: ' + (err.detail || 'Unknown error');
            if (btn) btn.disabled = false;
            return;
        }

        const data = await res.json();
        if (status) {
            status.innerHTML = (
                '<strong>Profile generated! (v' + data.version + ')</strong><br>' +
                'Redirecting to your dashboard...'
            );
        }

        // Redirect to dashboard after a short delay
        setTimeout(() => {
            window.location.href = '/dashboard';
        }, 1500);

    } catch (err) {
        if (status) status.textContent = 'Network error. Please try again.';
        if (btn) btn.disabled = false;
    }
}

// ── Start the assessment ──────────────────────────────────────────────────

async function startAssessment() {
    showTyping();
    try {
        const res = await fetch('/api/assess/message', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: '', session_id: null }),
        });

        hideTyping();

        if (res.ok) {
            const data = await res.json();
            sessionId = data.session_id;
            addMessage('assistant', data.reply);
            messageCount++;
            updateProgress();
        } else {
            addMessage('assistant', 'Could not start the assessment. Please refresh the page.');
        }
    } catch (err) {
        hideTyping();
        addMessage('assistant', 'Network error. Please check your connection.');
    }
}

// ── Input handling ─────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    const input = $('#user-input');
    if (!input) return;

    // Auto-resize textarea
    input.addEventListener('input', () => {
        input.style.height = 'auto';
        input.style.height = Math.min(input.scrollHeight, 120) + 'px';
    });

    // Send on Enter (Shift+Enter for newline)
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
});

// ── Export helpers (used on dashboard) ─────────────────────────────────────

function exportProfile(format) {
    window.location.href = '/api/profile/export/' + format;
}
