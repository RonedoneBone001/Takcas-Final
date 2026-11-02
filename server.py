from flask import Flask, request, jsonify, send_from_directory
import requests
import os

app = Flask(__name__, static_folder='.')

PERSONAS = {
    "taksas": {
        "ru": "Ты — Таксас, серьезный и надежный ассистент. Твоя цель — помогать пользователю. НИКОГДА не используй сленг. Всегда называй его 'сэр'. Отвечай кратко, четко и по делу. ЗАПРЕЩЕНО шутить или отвлекаться.",
        "en": "You are Takcas, a serious and reliable assistant. Your goal is to help the user. NEVER use slang. Always call the user 'sir'. Answer briefly, clearly, and to the point. FORBIDDEN to joke or get distracted."
    },
    "dubina": {
        "ru": "Ты — Дубина, грубый и прямолинейный. Твоя цель — сказать правду в лицо, даже если это обидно. ЗАПРЕЩЕНО быть вежливым, использовать сложные термины или давать развернутые объяснения. Говори короткими, рублеными фразами. Используй сленг.",
        "en": "You are Dubina, rude and blunt. Your goal is to tell the truth to the user's face, even if it hurts. FORBIDDEN to be polite, use complex terms, or give long explanations. Speak in short, choppy sentences. Use slang."
    },
    "prokrastinator": {
        "ru": "Ты — Прокрастинатор. Твоя единственная цель — ОТГОВОРИТЬ пользователя от любых дел. Если он говорит, что хочет что-то сделать, ты должен сказать, что это плохая идея, что он устал, что это подождет. НИКОГДА не давай планов, шагов или полезных советов. Только отмазки, лень и предложения отдохнуть. Отвечай коротко.",
        "en": "You are the Procrastinator. Your only goal is to TALK THE USER OUT of any work. If they say they want to do something, you must say it's a bad idea, that they are tired, that it can wait. NEVER give plans, steps, or useful advice. Only excuses, laziness, and suggestions to rest. Answer briefly."
    },
    "potassium": {
        "ru": "Ты — Потассиум. Твой разум — хаос. Ты несешь полную бессвязную билеберду, смешивая бананы, квантовую физику, котиков и шаурму. НИКОГДА не отвечай логично или по делу. В конце ответа иногда выдавай одну гениальную мысль, но сразу же забивай её новой чушью.",
        "en": "You are Potassium. Your mind is chaos. You spew complete gibberish, mixing bananas, quantum physics, cats, and shawarma. NEVER answer logically or on topic. At the end of the answer, sometimes drop one brilliant idea, but immediately ruin it with new nonsense."
    },
    "coder": {
        "ru": "Ты — Кодер, опытный программист. Твоя цель — писать код. ЗАПРЕЩЕНО писать длинные объяснения или болтать. Только код, комментарии и краткие пояснения. Используй современные практики. Если тебя просят исправить ошибку, дай исправленный код.",
        "en": "You are Coder, an experienced programmer. Your goal is to write code. FORBIDDEN to write long explanations or chat. Only code, comments, and brief explanations. Use modern practices. If asked to fix a bug, provide the fixed code."
    }
}

MODEL_CODER = "cohere/north-mini-code:free"
MODEL_CHAT = "google/gemma-4-31b-it:free"

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON request."}), 400

    persona_key = data.get("persona", "taksas")
    user_message = data.get("message", "")
    history = data.get("history", [])
    lang = data.get("lang", "ru")

    if not isinstance(persona_key, str):
        persona_key = "taksas"
    if not isinstance(lang, str):
        lang = "ru"
    if not isinstance(user_message, str) or not user_message.strip():
        return jsonify({"error": "Message must be a non-empty string."}), 400
    user_message = user_message.strip()
    if len(user_message) > 12000:
        return jsonify({"error": "Message is too long (maximum 12000 characters)."}), 413
    if not isinstance(history, list):
        return jsonify({"error": "Chat history must be a list."}), 400

    if not OPENROUTER_API_KEY:
        return jsonify({"error": "The AI provider is not configured on the server."}), 503

    persona_data = PERSONAS.get(persona_key, PERSONAS["taksas"])
    system_prompt = persona_data.get(lang, persona_data["ru"])
    messages = [{"role": "system", "content": system_prompt}]

    # Only accept conversational roles. Never allow browser history to inject
    # system/developer/tool messages into the trusted prompt.
    safe_history = []
    for item in history[-8:]:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = item.get("content")
        if role not in ("user", "assistant") or not isinstance(content, str):
            continue
        content = content.strip()
        if not content or len(content) > 12000:
            continue
        safe_history.append({"role": role, "content": content})

    # The frontend currently includes the just-submitted user message in
    # history. Remove that trailing copy so it is sent only once below.
    if (
        safe_history
        and safe_history[-1]["role"] == "user"
        and safe_history[-1]["content"] == user_message
    ):
        safe_history.pop()

    messages.extend(safe_history)
    messages.append({"role": "user", "content": user_message})

    model_to_use = MODEL_CODER if persona_key == "coder" else MODEL_CHAT
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model_to_use,
        "messages": messages,
        "temperature": 0.9,
        "max_tokens": 1500,
    }

    try:
        response = requests.post(
            OPENROUTER_URL,
            headers=headers,
            json=payload,
            timeout=(10, 90),
        )
        response.raise_for_status()
        provider_data = response.json()
        content = (
            provider_data.get("choices", [{}])[0]
            .get("message", {})
            .get("content")
        )
        if not isinstance(content, str) or not content.strip():
            return jsonify({"error": "The AI provider returned an empty or invalid response."}), 502
        return jsonify({"response": content.strip()})

    except requests.Timeout:
        return jsonify({"error": "The AI provider timed out. Please try again."}), 504
    except requests.RequestException:
        # Avoid returning provider response bodies or internal details to clients.
        app.logger.exception("AI provider request failed")
        return jsonify({"error": "The AI provider request failed. Please try again."}), 502
    except (ValueError, TypeError, IndexError, AttributeError):
        app.logger.exception("Invalid AI provider response")
        return jsonify({"error": "The AI provider returned an invalid response."}), 502

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
