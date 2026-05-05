const API_BASE = "http://localhost:8000";
const TOKEN_KEY = "auth_token";
const EMAIL_KEY = "auth_email";

const authScreen = document.getElementById("authScreen");
const chatScreen = document.getElementById("chatScreen");
const authError = document.getElementById("authError");
const messagesEl = document.getElementById("messages");
const inputEl = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");
const suggestionsEl = document.getElementById("suggestions");
const userEmailEl = document.getElementById("userEmail");
const chatListEl = document.getElementById("chatList");
let currentSessionId = null;
let serverSessions = [];
let draftSessions = [];

const TOOL_LABELS = {
  get_current_user_info: "Fetched user profile",
  list_orders: "Listed orders",
  lookup_order: "Checked order status",
  search_faq: "Searched FAQ",
  create_support_ticket: "Created support ticket",
};

function setAuthError(text) {
  if (!text) {
    authError.hidden = true;
    authError.textContent = "";
    return;
  }
  authError.hidden = false;
  authError.textContent = text;
}

function showAuthScreen() {
  authScreen.hidden = false;
  chatScreen.hidden = true;
}

function showChatScreen() {
  authScreen.hidden = true;
  chatScreen.hidden = false;
}

function clearAuth() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(EMAIL_KEY);
}

function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

async function apiFetch(path, options = {}) {
  const token = getToken();
  const headers = new Headers(options.headers || {});
  if (token) headers.set("Authorization", "Bearer " + token);
  const res = await fetch(API_BASE + path, { ...options, headers });
  if (res.status === 401) {
    clearAuth();
    showAuthScreen();
  }
  return res;
}

function formatTime(isoString) {
  if (!isoString) {
    return new Date().toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
  }
  const d = new Date(isoString.replace(" ", "T") + "Z");
  if (isNaN(d.getTime())) return "";
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function renderMarkdown(text) {
  let html = escapeHtml(text || "");

  html = html.replace(/```([\s\S]*?)```/g, (_, code) => {
    return `<pre><code>${code.trim()}</code></pre>`;
  });
  html = html.replace(/^### (.+)$/gm, "<h3>$1</h3>");
  html = html.replace(/^## (.+)$/gm, "<h2>$1</h2>");
  html = html.replace(/^# (.+)$/gm, "<h1>$1</h1>");
  html = html.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
  html = html.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/\*([^*\n]+)\*/g, "<em>$1</em>");
  html = html.replace(/`([^`\n]+)`/g, "<code>$1</code>");
  html = html.replace(/(?:^|\n)- (.+)(?=\n|$)/g, "<li>$1</li>");
  html = html.replace(/(<li>[\s\S]*?<\/li>)/g, "<ul>$1</ul>");
  html = html.replace(/<\/ul>\s*<ul>/g, "");
  html = html.replace(/\n/g, "<br>");
  html = html.replace(/<br>\s*<\/(ul|ol)>/g, "</$1>");
  html = html.replace(/<(pre|code|h1|h2|h3|ul|li)([^>]*)><br>/g, "<$1$2>");
  html = html.replace(/<br><\/pre>/g, "</pre>");
  return html;
}

function appendMessage(role, text, tools = [], timeStr = null) {
  const wrapper = document.createElement("div");
  wrapper.className = `message ${role}`;

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  if (role === "agent") {
    bubble.innerHTML = renderMarkdown(text);
  } else {
    bubble.textContent = text;
  }
  wrapper.appendChild(bubble);

  if (role === "agent" && tools.length > 0) {
    const badges = document.createElement("div");
    badges.className = "tool-badges";
    tools.forEach((t) => {
      const badge = document.createElement("span");
      badge.className = "tool-badge";
      badge.textContent = TOOL_LABELS[t] || t;
      badges.appendChild(badge);
    });
    wrapper.appendChild(badges);
  }

  const time = document.createElement("span");
  time.className = "message-time";
  time.textContent = formatTime(timeStr);
  wrapper.appendChild(time);

  messagesEl.appendChild(wrapper);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function showTyping() {
  const el = document.createElement("div");
  el.className = "message agent typing";
  el.id = "typing-indicator";
  el.innerHTML =
    '<div class="bubble"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>';
  messagesEl.appendChild(el);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function hideTyping() {
  document.getElementById("typing-indicator")?.remove();
}

function resetChatUi() {
  messagesEl.innerHTML = "";
  suggestionsEl.style.display = "flex";
  appendMessage(
    "agent",
    "Hi! I'm Shopify Order Assist. How can I help you today?"
  );
}

function formatDateTime(isoString) {
  if (!isoString) return "";
  const d = new Date(isoString.replace(" ", "T") + "Z");
  if (isNaN(d.getTime())) return "";
  return d.toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

function combinedSessions() {
  const draftOnly = draftSessions.filter(
    (d) => !serverSessions.some((s) => s.session_id === d.session_id)
  );
  return [...draftOnly, ...serverSessions];
}

function createSessionId() {
  if (crypto && typeof crypto.randomUUID === "function") {
    return `chat-${crypto.randomUUID().replace(/-/g, "")}`;
  }
  const rand = `${Date.now()}-${Math.random().toString(16).slice(2)}-${Math.random().toString(16).slice(2)}`;
  return `chat-${rand.replace(/[^a-zA-Z0-9]/g, "")}`;
}

function renderSessionList(sessions) {
  chatListEl.innerHTML = "";
  if (sessions.length === 0) {
    const el = document.createElement("div");
    el.className = "chat-item";
    el.innerHTML = '<div class="chat-item-title">No chats yet</div>';
    chatListEl.appendChild(el);
    return;
  }
  sessions.forEach((s) => {
    const item = document.createElement("button");
    item.type = "button";
    item.className = "chat-item";
    if (s.session_id === currentSessionId) item.classList.add("active");
    item.innerHTML =
      `<div class="chat-item-title">${s.title || "New chat"}</div>` +
      `<div class="chat-item-time">${formatDateTime(s.last_message_at)}</div>`;
    item.addEventListener("click", () => {
      currentSessionId = s.session_id;
      loadHistory();
      loadSessions();
    });
    chatListEl.appendChild(item);
  });
}

async function loadSessions() {
  if (!getToken()) return;
  try {
    const res = await apiFetch("/sessions");
    if (!res.ok) return;
    const data = await res.json();
    serverSessions = data.sessions || [];
    draftSessions = draftSessions.filter(
      (d) => !serverSessions.some((s) => s.session_id === d.session_id)
    );
    const sessions = combinedSessions();
    if (!currentSessionId && sessions.length > 0) currentSessionId = sessions[0].session_id;
    renderSessionList(sessions);
  } catch (err) {
    console.error(err);
  }
}

async function loadHistory() {
  if (!getToken()) return;
  if (!currentSessionId) {
    resetChatUi();
    return;
  }
  try {
    const res = await apiFetch(`/history?session_id=${encodeURIComponent(currentSessionId)}`);
    if (!res.ok) return;
    const data = await res.json();
    messagesEl.innerHTML = "";
    if ((data.messages || []).length === 0) {
      suggestionsEl.style.display = "flex";
      appendMessage("agent", "Hi! I'm Shopify Order Assist. How can I help you today?");
      return;
    }
    suggestionsEl.style.display = "none";
    data.messages.forEach((m) => {
      const role = m.role === "human" ? "user" : "agent";
      appendMessage(role, m.content, m.tools_used || [], m.created_at);
    });
  } catch (err) {
    console.error(err);
  }
}

async function sendMessage() {
  if (!getToken()) return;

  const text = inputEl.value.trim();
  if (!text) return;

  suggestionsEl.style.display = "none";
  inputEl.value = "";
  sendBtn.disabled = true;

  appendMessage("user", text);
  showTyping();

  try {
    const res = await apiFetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, session_id: currentSessionId }),
    });

    if (!res.ok) {
      const detail = await res.json().catch(() => ({}));
      throw new Error(detail.detail || res.status);
    }

    const data = await res.json();
    currentSessionId = data.session_id || currentSessionId;
    draftSessions = draftSessions.filter((d) => d.session_id !== currentSessionId);
    hideTyping();
    appendMessage("agent", data.response, data.tools_used || []);
    await loadSessions();
  } catch (err) {
    hideTyping();
    appendMessage(
      "agent",
      "Sorry, I'm having trouble connecting right now. Please try again."
    );
    console.error(err);
  } finally {
    sendBtn.disabled = false;
    inputEl.focus();
  }
}

function sendSuggestion(text) {
  inputEl.value = text;
  sendMessage();
}

document.getElementById("tabLogin").addEventListener("click", () => {
  document.getElementById("tabLogin").classList.add("active");
  document.getElementById("tabRegister").classList.remove("active");
  document.getElementById("loginForm").hidden = false;
  document.getElementById("registerForm").hidden = true;
  setAuthError("");
});

document.getElementById("tabRegister").addEventListener("click", () => {
  document.getElementById("tabRegister").classList.add("active");
  document.getElementById("tabLogin").classList.remove("active");
  document.getElementById("loginForm").hidden = true;
  document.getElementById("registerForm").hidden = false;
  setAuthError("");
});

document.getElementById("loginForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  setAuthError("");
  const email = document.getElementById("loginEmail").value.trim();
  const password = document.getElementById("loginPassword").value;
  try {
    const res = await fetch(API_BASE + "/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      setAuthError(data.detail || "Login failed");
      return;
    }
    localStorage.setItem(TOKEN_KEY, data.token);
    localStorage.setItem(EMAIL_KEY, data.email);
    userEmailEl.textContent = data.email;
    draftSessions = [];
    showChatScreen();
    await loadSessions();
    await loadHistory();
  } catch (err) {
    setAuthError("Network error");
    console.error(err);
  }
});

document.getElementById("registerForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  setAuthError("");
  const email = document.getElementById("registerEmail").value.trim();
  const password = document.getElementById("registerPassword").value;
  try {
    const res = await fetch(API_BASE + "/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      setAuthError(
        typeof data.detail === "string"
          ? data.detail
          : "Registration failed"
      );
      return;
    }
    localStorage.setItem(TOKEN_KEY, data.token);
    localStorage.setItem(EMAIL_KEY, data.email);
    userEmailEl.textContent = data.email;
    draftSessions = [];
    showChatScreen();
    await loadSessions();
    await loadHistory();
  } catch (err) {
    setAuthError("Network error");
    console.error(err);
  }
});

document.getElementById("logoutBtn").addEventListener("click", () => {
  clearAuth();
  currentSessionId = null;
  serverSessions = [];
  draftSessions = [];
  showAuthScreen();
  resetChatUi();
  chatListEl.innerHTML = "";
});

document.getElementById("newChatBtn").addEventListener("click", async () => {
  if (!getToken()) return;
  currentSessionId = createSessionId();
  draftSessions.unshift({
    session_id: currentSessionId,
    title: "New chat",
    last_message_at: new Date().toISOString(),
  });
  resetChatUi();
  renderSessionList(combinedSessions());
});

inputEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

async function bootstrap() {
  const token = getToken();
  if (!token) {
    showAuthScreen();
    return;
  }
  const res = await apiFetch("/auth/me");
  if (!res.ok) {
    showAuthScreen();
    return;
  }
  const me = await res.json();
  localStorage.setItem(EMAIL_KEY, me.email);
  userEmailEl.textContent = me.email;
  draftSessions = [];
  showChatScreen();
  await loadSessions();
  await loadHistory();
}

bootstrap();
