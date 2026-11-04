const API = "https://takcas-service.onrender.com/chat";

const PERSONAS = [
  { key:"taksas",         name:"Таксас",         emoji:"🦔" },
  { key:"dubina",         name:"Дубина",         emoji:"🔨" },
  { key:"prokrastinator", name:"Прокрастинатор", emoji:"😴" },
  { key:"potassium",      name:"Потассиум",      emoji:"🥔" },
  { key:"coder",          name:"Кодер",          emoji:"💻" },
];

const I18N = {
  ru: {
    newChat:"Новый чат", history:"История", projects:"Проекты",
    settings:"Настройки", local:"Локальное пространство", ready:"Готов",
    code:"Код", attach:"Прикрепить",
    disclaimer:"ИИ может ошибаться. Проверяйте важный код перед использованием.",
    ph:"Сообщение Takcas Coder...",
    errConn:"Ошибка соединения", errSleep:"Render мог уснуть — подожди ~30 сек и отправь ещё раз.",
    errLimit:"Дневной лимит запросов исчерпан. Попробуй завтра.",
    errConf:"Сервер не настроен (проверь OPENROUTER_API_KEY в Render).",
    oldChat:"Загрузка старых чатов — следующий шаг.",
    attachInfo:"Attach: пока не подключено."
  },
  en: {
    newChat:"New chat", history:"History", projects:"Projects",
    settings:"Settings", local:"Local workspace", ready:"Ready",
    code:"Code", attach:"Attach",
    disclaimer:"AI can make mistakes. Review important code before using it.",
    ph:"Message Takcas Coder...",
    errConn:"Connection error", errSleep:"Render may have slept — wait ~30 sec and try again.",
    errLimit:"Daily request limit reached. Try again tomorrow.",
    errConf:"Server not configured (check OPENROUTER_API_KEY on Render).",
    oldChat:"Loading old chats — next step.",
    attachInfo:"Attach: not connected yet."
  }
};

const $ = id => document.getElementById(id);
let lang = "ru";
let personaIdx = 0;
let history = [];
let codeMode = false;

const pKey = () => PERSONAS[personaIdx].key;
const pName = () => PERSONAS[personaIdx].name;
const t = k => I18N[lang][k];

// ---------- язык ----------
function applyLang() {
  document.querySelectorAll("[data-i18n]").forEach(el => {
    el.textContent = t(el.dataset.i18n);
  });
  $("input").placeholder = t("ph");
  document.querySelectorAll(".lang-btn").forEach(b =>
    b.classList.toggle("active", b.dataset.lang === lang));
  $("modelsName").textContent = pName();
}
document.querySelectorAll(".lang-btn").forEach(b => {
  b.onclick = () => { lang = b.dataset.lang; applyLang(); };
});

// ---------- персонажи ----------
function setPersona(idx) {
  personaIdx = idx;
  history = [];
  $("messages").innerHTML = "";
  $("chatTitle").textContent = `${PERSONAS[idx].emoji} ${pName()}`;
  $("modelsName").textContent = pName();
}
$("modelsBtn").onclick = () => setPersona((personaIdx + 1) % PERSONAS.length);

// ---------- новый чат / очистка ----------
const clearAll = () => { history = []; $("messages").innerHTML = ""; };
$("newChat").onclick = clearAll;
$("clearChat").onclick = clearAll;

// ---------- тема ----------
$("themeToggle").onclick = () => {
  document.body.classList.toggle("light");
  $("themeToggle").textContent = document.body.classList.contains("light") ? "🌙" : "☀";
};

// ---------- Code / Attach ----------
$("codeMode").onclick = () => {
  codeMode = !codeMode;
  $("codeMode").classList.toggle("on", codeMode);
};
$("attachBtn").onclick = () => alert(t("attachInfo"));

// ---------- ввод ----------
$("sendBtn").onclick = send;
$("input").addEventListener("keydown", e => {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
});
$("input").addEventListener("input", e => {
  e.target.style.height = "auto";
  e.target.style.height = Math.min(e.target.scrollHeight, 160) + "px";
});

// ---------- отправка ----------
async function send() {
  const text = $("input").value.trim();
  if (!text) return;

  $("input").value = "";
  $("input").style.height = "auto";
  $("sendBtn").disabled = true;

  addMsg("user", "You", text);
  history.push({ role:"user", content:text });
  addMsg("bot", pName(), "⏳ ...", true);

  const outgoingPersona = codeMode ? "coder" : pKey();
  const outgoingText = codeMode
    ? text + "\n\n[Режим: только код. Верни только рабочий код в markdown-блоке, без объяснений.]"
    : text;

  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 60000);

  try {
    const res = await fetch(API, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ persona: outgoingPersona, message: outgoingText, history, lang }),
      signal: ctrl.signal
    });

    if (res.status === 429) throw { code: 429 };
    if (res.status === 503) throw { code: 503 };
    if (!res.ok) throw { code: res.status };

    const data = await res.json();
    removeTemp();
    const reply = (data && data.response) || "(пусто)";
    addMsg("bot", pName(), reply);
    history.push({ role:"assistant", content:reply });
    addRecent(text);

  } catch (err) {
    removeTemp();
    let msg;
    if (err && err.code === 429)      msg = t("errLimit");
    else if (err && err.code === 503) msg = t("errConf");
    else if (err && err.name === "AbortError")
      msg = `${t("errConn")}: timeout.\n${t("errSleep")}`;
    else
      msg = `${t("errConn")}${err && err.code ? " (HTTP " + err.code + ")" : ""}.\n${t("errSleep")}`;
    addMsg("bot", pName(), msg, false, true);

  } finally {
    clearTimeout(timer);
    $("sendBtn").disabled = false;
    $("input").focus();
  }
}

// ---------- сообщения ----------
function addMsg(role, name, text, temp = false, isErr = false) {
  const row = document.createElement("div");
  row.className = "msg-row " + role + (temp ? " temp-row" : "");
  const av = role === "user" ? "U" : (PERSONAS.find(p => p.name === name)?.emoji || "T");
  row.innerHTML = `
    <div class="msg-avatar">${av}</div>
    <div class="msg-body">
      <div class="msg-name">${name}</div>
      <div class="msg-text${isErr ? " err" : ""}${temp ? " temp" : ""}"></div>
    </div>`;
  row.querySelector(".msg-text").textContent = text;
  $("messages").appendChild(row);
  $("messages").scrollTop = $("messages").scrollHeight;
}

function removeTemp() {
  const el = $("messages").querySelector(".temp-row");
  if (el) el.remove();
}

function addRecent(text) {
  const h = $("history");
  const item = document.createElement("div");
  item.textContent = text.slice(0, 30);
  item.onclick = () => alert(t("oldChat"));
  h.prepend(item);
  while (h.children.length > 6) h.lastChild.remove();
}

// ---------- старт ----------
$("chatTitle").textContent = `${PERSONAS[0].emoji} ${pName()}`;
applyLang();
