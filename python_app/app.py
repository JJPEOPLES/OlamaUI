import os
import json
import datetime
import requests
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration
OLLAMA_API_URL = os.getenv('OLLAMA_API_URL', 'http://localhost:11434/api')

# Routes
@app.route('/')
def index():
    return render_template('index.html', now=datetime.datetime.now())

@app.route('/api/models', methods=['GET'])
def get_models():
    try:
        response = requests.get(f"{OLLAMA_API_URL}/tags")
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        # Get request data
        data = request.json

        model = data.get('model')
        messages = data.get('messages', [])
        options = data.get('options', {})

        # Prepare request to Ollama
        ollama_payload = {
            "model": model,
            "messages": messages,
            "stream": False
        }

        # Add options if provided
        if options:
            ollama_payload["options"] = options

        # Send request to Ollama
        response = requests.post(
            f"{OLLAMA_API_URL}/chat",
            json=ollama_payload
        )

        # Return the response
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/version', methods=['GET'])
def version():
    try:
        # Get Ollama version
        response = requests.get(f"{OLLAMA_API_URL}/version")
        ollama_version = response.json().get('version', 'unknown')

        return jsonify({
            "app_version": "1.0.0",
            "ollama_version": ollama_version,
            "python_version": os.environ.get('PYTHON_VERSION', '3.x')
        })
    except Exception as e:
        return jsonify({
            "app_version": "1.0.0",
            "ollama_version": "unknown (could not connect)",
            "python_version": os.environ.get('PYTHON_VERSION', '3.x'),
            "error": str(e)
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)