const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => [...document.querySelectorAll(sel)];

let currentPersona = 'taksas';
let currentLang = 'ru';
let isSending = false;
let messages = [];

const t = {
  ru: { placeholder: "Сообщение...", you: "Вы", bot: "Takcas", thinking: "Думаю", error: "Ошибка соединения." },
  en: { placeholder: "Message...", you: "You", bot: "Takcas", thinking: "Thinking", error: "Connection error." }
};

function setPersona(persona) {
  currentPersona = persona;
  $$('.nav-btn').forEach(btn => btn.classList.toggle('active', btn.dataset.persona === persona));
}

function toggleLang() {
  currentLang = currentLang === 'ru' ? 'en' : 'ru';
  $('#lang-toggle').textContent = currentLang === 'ru' ? 'EN / RU' : 'RU / EN';
  $('#user-input').placeholder = t[currentLang].placeholder;
}

function addMessage(role, text) {
  const div = document.createElement('article');
  div.className = `message ${role}`;
  div.innerHTML = `<div class="message-avatar">${role === 'user' ? '👤' : '🤖'}</div><div class="message-content"><div class="message-name">${role === 'user' ? t[currentLang].you : t[currentLang].bot}</div><div class="message-text"></div></div>`;
  div.querySelector('.message-text').textContent = text;
  $('#chat-box').appendChild(div);
  $('#workspace').scrollTop = $('#workspace').scrollHeight;
}

function showTyping() {
  const el = document.createElement('article');
  el.className = 'message assistant';
  el.id = 'typing';
  el.innerHTML = `<div class="message-avatar">🤖</div><div class="message-content"><div class="message-name">${t[currentLang].thinking}</div><div class="typing">...</div></div>`;
  $('#chat-box').appendChild(el);
  $('#workspace').scrollTop = $('#workspace').scrollHeight;
}

async function sendMessage() {
  const text = $('#user-input').value.trim();
  if (!text || isSending) return;

  messages.push({ role: 'user', content: text });
  addMessage('user', text);
  $('#user-input').value = '';
  isSending = true;
  $('#send-btn').disabled = true;
  showTyping();

  try {
    const res = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ persona: currentPersona, message: text, history: messages.slice(-20), lang: currentLang })
    });
    const data = await res.json();
    $('#typing')?.remove();
    if (!res.ok || !data.response) throw new Error();
    messages.push({ role: 'assistant', content: data.response });
    addMessage('assistant', data.response);
  } catch {
    $('#typing')?.remove();
    addMessage('assistant', t[currentLang].error);
  } finally {
    isSending = false;
    $('#send-btn').disabled = false;
  }
}

$$('.nav-btn').forEach(btn => btn.addEventListener('click', () => setPersona(btn.dataset.persona)));
$('#lang-toggle').addEventListener('click', toggleLang);
$('#send-btn').addEventListener('click', sendMessage);
$('#user-input').addEventListener('keydown', (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } });
$('#user-input').addEventListener('input', () => { $('#send-btn').disabled = !$('#user-input').value.trim(); });
$('#clear-chat').addEventListener('click', () => { $('#chat-box').innerHTML = ''; messages = []; });
$('#sidebar-open').addEventListener('click', () => { $('#sidebar').classList.add('open'); $('#overlay').classList.add('show'); });
$('#overlay').addEventListener('click', () => { $('#sidebar').classList.remove('open'); $('#overlay').classList.remove('show'); });
$('#user-input').placeholder = t[currentLang].placeholder;
