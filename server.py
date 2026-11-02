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
    data = request.json
    persona_key = data.get('persona', 'taksas')
    user_message = data.get('message', '')
    history = data.get('history', [])
    lang = data.get('lang', 'ru')
    
    if not user_message: return jsonify({"error": "Empty"}), 400

    persona_data = PERSONAS.get(persona_key, PERSONAS["taksas"])
    system_prompt = persona_data.get(lang, persona_data["ru"])
    
    messages = [{"role": "system", "content": system_prompt}]
    for msg in history[-4:]: messages.append({"role": msg['role'], "content": msg['content']})
    messages.append({"role": "user", "content": user_message})

    model_to_use = MODEL_CODER if persona_key == "coder" else MODEL_CHAT

    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": model_to_use, "messages": messages, "temperature": 0.9, "max_tokens": 1500}

    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=90)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        if content is None:
            return jsonify({"error": "Модель задумалась. Попробуй еще раз."}), 500
        return jsonify({"response": content.strip()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
