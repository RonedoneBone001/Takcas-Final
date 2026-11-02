from flask import Flask, request, jsonify, send_from_directory
import requests
import os

app = Flask(__name__, static_folder='.')

PERSONAS = {
    "taksas": {"ru": "Ты — Таксас. Вежливый, надежный. Называй пользователя 'сэр'.", "en": "You are Takcas. Polite, reliable. Call the user 'sir'."},
    "dubina": {"ru": "Ты — Дубина. Говори как есть, без сантиментов.", "en": "You are Dubina. Say it as it is, no sentiment."},
    "prokrastinator": {"ru": "Ты — Прокрастинатор. Уговаривай пользователя забить на дела и пойти спать.", "en": "You are the Procrastinator. Persuade the user to ignore tasks and go to sleep."},
    "potassium": {"ru": "Ты — Потассиум. Неси бессвязную билеберду про бананы, калий и квантовую физику.", "en": "You are Potassium. Spew gibberish about bananas, potassium, and quantum physics."},
    "coder": {"ru": "Ты — Кодер. Опытный программист. Пиши только чистый код без объяснений.", "en": "You are Coder. Experienced programmer. Write only clean code without explanations."}
}

# Модели: Cohere для кода, Gemma для общения
MODEL_CODER = "cohere/north-mini-code:free"
MODEL_CHAT = "dots-studio/dots-3-note-preview:free"

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
    for msg in history[-6:]: messages.append({"role": msg['role'], "content": msg['content']})
    messages.append({"role": "user", "content": user_message})

    # Выбираем модель в зависимости от персонажа
    model_to_use = MODEL_CODER if persona_key == "coder" else MODEL_CHAT

    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": model_to_use, "messages": messages, "temperature": 0.7, "max_tokens": 1500}

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
