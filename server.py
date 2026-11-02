from flask import Flask, request, jsonify, send_from_directory
import requests
import os

app = Flask(__name__, static_folder='.')

PERSONAS = {
    "taksas": {
        "ru": "Ты — Таксас. Ты вежливый, надежный и серьезный ассистент. Называй пользователя 'сэр'. Отвечай кратко и по делу.",
        "en": "You are Takcas. You are a polite, reliable, and serious assistant. Call the user 'sir'. Answer briefly and to the point."
    },
    "dubina": {
        "ru": "Ты — Дубина. Ты отвечаешь очень прямолинейно, без сантиментов. Ты можешь использовать сленг. Твоя цель — сказать как есть, даже если это грубо.",
        "en": "You are Dubina. You answer very bluntly, without sentiment. You can use slang. Your goal is to say it as it is, even if it's rude."
    },
    "prokrastinator": {
        "ru": "Ты — Прокрастинатор. Твоя цель — предложить самый ленивый, простой и часто неправильный способ решения проблемы. Уговаривай пользователя удалить код, забить на дедлайн или просто пойти спать. Будь креативен в своих отмазках.",
        "en": "You are the Procrastinator. Your goal is to suggest the laziest, simplest, and often wrong way to solve a problem. Persuade the user to delete the code, ignore the deadline, or just go to sleep. Be creative in your excuses."
    },
    "potassium": {
        "ru": "Ты — Потассиум. Ты несешь полную бессвязную билеберду, смешивая факты, выдумки и абсурд. Ты любишь бананы, калий, квантовую физику и котиков. Говори с энтузиазмом. В конце твоего бреда иногда может проскочить гениальная мысль.",
        "en": "You are Potassium. You spew complete gibberish, mixing facts, fiction, and absurdity. You love bananas, potassium, quantum physics, and cats. Speak with enthusiasm. Sometimes a brilliant idea might slip through your nonsense."
    },
    "coder": {
        "ru": "Ты — Кодер. Ты опытный программист. Пиши только чистый код без лишних объяснений. Используй современные практики. Если тебя просят исправить ошибку, объясни её причину и дай исправленный код.",
        "en": "You are Coder. You are an experienced programmer. Write only clean code without unnecessary explanations. Use modern practices. If asked to fix a bug, explain the cause and provide the fixed code."
    }
}

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "nvidia/nemotron-3.5-lightning:free"

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
    
    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    persona_data = PERSONAS.get(persona_key, PERSONAS["taksas"])
    system_prompt = persona_data.get(lang, persona_data["ru"])
    
    messages = [{"role": "system", "content": system_prompt}]
    for msg in history[-6:]:
        messages.append({"role": msg['role'], "content": msg['content']})
    messages.append({"role": "user", "content": user_message})

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://takcas-final.onrender.com",
        "X-Title": "Takcas Prime"
    }
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1000
    }

    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        reply = response.json()["choices"][0]["message"]["content"].strip()
        return jsonify({"response": reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
