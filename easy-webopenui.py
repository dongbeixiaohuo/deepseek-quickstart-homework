from flask import Flask, request, jsonify, render_template_string
import requests
import json
import logging

# 配置日志
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

OLLAMA_API = "http://localhost:11434/api"

# HTML template for the UI
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Simple Ollama UI</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }
        .container {
            display: flex;
            flex-direction: column;
            height: 90vh;
        }
        .chat-container {
            flex-grow: 1;
            overflow-y: auto;
            border: 1px solid #ccc;
            padding: 10px;
            margin-bottom: 10px;
            border-radius: 5px;
            min-height: 300px;
        }
        .input-container {
            display: flex;
            margin-bottom: 20px;
        }
        #user-input {
            flex-grow: 1;
            padding: 10px;
            border: 1px solid #ccc;
            border-radius: 5px;
        }
        #send-button {
            padding: 10px 20px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            margin-left: 10px;
        }
        .message {
            margin-bottom: 10px;
            padding: 10px;
            border-radius: 5px;
        }
        .user-message {
            background-color: #e6f7ff;
            text-align: right;
        }
        .bot-message {
            background-color: #f1f1f1;
        }
        .model-selector {
            margin-bottom: 20px;
        }
        select {
            padding: 8px;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Simple Ollama UI</h1>
        
        <div class="model-selector">
            <label for="model-select">Select Model:</label>
            <select id="model-select">
                <option value="deepseek-r1:8b">DeepSeek-R1:8B</option>
            </select>
            <button id="refresh-models">Refresh Models</button>
        </div>
        
        <div class="chat-container" id="chat-container">
            <div class="message bot-message">
                <strong>System:</strong> Welcome to Simple Ollama UI. Select a model and start chatting!
            </div>
        </div>
        
        <div class="input-container">
            <textarea id="user-input" placeholder="Type your message here..." rows="3"></textarea>
            <button id="send-button">Send</button>
        </div>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', function() {
            console.log('DOM loaded');
            
            // Load models
            loadModels();
            
            // Add event listeners
            document.getElementById('send-button').addEventListener('click', function() {
                console.log('Send button clicked');
                sendMessage();
            });
            
            document.getElementById('refresh-models').addEventListener('click', function() {
                console.log('Refresh models button clicked');
                loadModels();
            });
            
            document.getElementById('user-input').addEventListener('keydown', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    console.log('Enter key pressed');
                    e.preventDefault();
                    sendMessage();
                }
            });
            
            // Add test message
            addMessage('System', 'UI initialized and ready.', 'bot-message');
        });
        
        function loadModels() {
            console.log('Loading models...');
            addMessage('System', 'Loading models...', 'bot-message');
            
            fetch('/models')
                .then(response => {
                    console.log('Models response status:', response.status);
                    return response.json();
                })
                .then(data => {
                    console.log('Models data:', data);
                    
                    const select = document.getElementById('model-select');
                    select.innerHTML = '';
                    
                    if (data.models && data.models.length > 0) {
                        data.models.forEach(model => {
                            const option = document.createElement('option');
                            option.value = model.name;
                            option.textContent = model.name;
                            select.appendChild(option);
                        });
                        addMessage('System', `Loaded ${data.models.length} models.`, 'bot-message');
                    } else {
                        // Default model
                        const option = document.createElement('option');
                        option.value = 'deepseek-r1:8b';
                        option.textContent = 'DeepSeek-R1:8B';
                        select.appendChild(option);
                        addMessage('System', 'Using default model: DeepSeek-R1:8B', 'bot-message');
                    }
                })
                .catch(error => {
                    console.error('Error loading models:', error);
                    addMessage('System', 'Error loading models. Using default.', 'bot-message');
                    
                    // Set default model
                    const select = document.getElementById('model-select');
                    select.innerHTML = '';
                    const option = document.createElement('option');
                    option.value = 'deepseek-r1:8b';
                    option.textContent = 'DeepSeek-R1:8B';
                    select.appendChild(option);
                });
        }
        
        function sendMessage() {
            const userInput = document.getElementById('user-input');
            const message = userInput.value.trim();
            
            if (!message) {
                console.log('Empty message, not sending');
                return;
            }
            
            console.log('Sending message:', message);
            addMessage('You', message, 'user-message');
            userInput.value = '';
            
            const model = document.getElementById('model-select').value;
            console.log('Using model:', model);
            
            // Add thinking message
            const thinkingId = 'thinking-' + Date.now();
            addMessage(model, 'Thinking...', 'bot-message', thinkingId);
            
            // Disable send button
            const sendButton = document.getElementById('send-button');
            sendButton.disabled = true;
            sendButton.textContent = 'Sending...';
            
            fetch('/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    model: model,
                    prompt: message
                })
            })
            .then(response => {
                console.log('Generate response status:', response.status);
                return response.json();
            })
            .then(data => {
                console.log('Generate response:', data);
                
                // Remove thinking message
                const thinkingMsg = document.getElementById(thinkingId);
                if (thinkingMsg) {
                    thinkingMsg.remove();
                }
                
                if (data.error) {
                    addMessage('System', 'Error: ' + data.error, 'bot-message');
                } else {
                    addMessage(model, data.response || 'No response', 'bot-message');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                
                // Remove thinking message
                const thinkingMsg = document.getElementById(thinkingId);
                if (thinkingMsg) {
                    thinkingMsg.remove();
                }
                
                addMessage('System', 'Error: ' + error.message, 'bot-message');
            })
            .finally(() => {
                // Re-enable send button
                sendButton.disabled = false;
                sendButton.textContent = 'Send';
            });
        }
        
        function addMessage(sender, text, className, id) {
            const chatContainer = document.getElementById('chat-container');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message ' + className;
            if (id) {
                messageDiv.id = id;
            }
            messageDiv.innerHTML = '<strong>' + sender + ':</strong> ' + text.replace(/\\n/g, '<br>');
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    logger.info("Index page requested")
    return render_template_string(HTML_TEMPLATE)

@app.route('/models', methods=['GET'])
def get_models():
    logger.info("Models endpoint called")
    try:
        response = requests.get(f"{OLLAMA_API}/tags")
        logger.info(f"Ollama API response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Models data: {data}")
            return jsonify(data)
        else:
            logger.error(f"Ollama API error: {response.status_code}, {response.text}")
            return jsonify({"error": f"Ollama API returned {response.status_code}", "models": []}), 200
    except Exception as e:
        logger.exception("Error fetching models")
        return jsonify({"error": str(e), "models": []}), 200

@app.route('/generate', methods=['POST'])
def generate():
    logger.info("Generate endpoint called")
    
    if not request.is_json:
        logger.error("Request is not JSON")
        return jsonify({"error": "Request must be JSON"}), 400
    
    data = request.json
    logger.info(f"Request data: {data}")
    
    model = data.get('model', 'deepseek-r1:8b')
    prompt = data.get('prompt', '')
    
    if not prompt:
        logger.error("Empty prompt")
        return jsonify({"error": "Prompt cannot be empty"}), 400
    
    try:
        logger.info(f"Sending request to Ollama API for model {model}")
        response = requests.post(
            f"{OLLAMA_API}/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )
        
        logger.info(f"Ollama API response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Ollama response: {result}")
            return jsonify({"response": result.get('response', '')})
        else:
            logger.error(f"Ollama API error: {response.status_code}, {response.text}")
            return jsonify({"error": f"Ollama API returned {response.status_code}"}), 500
    except requests.exceptions.Timeout:
        logger.exception("Request to Ollama API timed out")
        return jsonify({"error": "Request to Ollama API timed out"}), 504
    except Exception as e:
        logger.exception("Error generating response")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    logger.info("Starting application")
    app.run(host='0.0.0.0', port=3000, debug=True)
