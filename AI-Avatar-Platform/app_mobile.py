"""
app_mobile.py - Lightweight Flask app for Android/Termux

Optimized for mobile devices with:
- Android TTS instead of XTTS
- No Whisper (use Android Speech Recognition)
- Simple Q&A matching without Ollama
- Minimal dependencies
"""

from flask import Flask, jsonify, request, render_template_string
import json
import re
import os
from rapidfuzz import fuzz
import subprocess
import tempfile
import base64

# Initialize Flask app
app = Flask(__name__)

# Load Q&A data
qa_data = []
qa_file = "data/qa_data.json"
try:
    if os.path.exists(qa_file):
        with open(qa_file, "r", encoding="utf-8") as f:
            qa_data = json.load(f)
        print(f"✅ Loaded {len(qa_data)} Q&A pairs")
    else:
        print("⚠️ Q&A file not found, using empty dataset")
except Exception as e:
    print(f"❌ Failed to load Q&A data: {e}")

def normalize(text):
    """Lowercase, strip, remove punctuation and multiple spaces"""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text

def find_scripted_response(user_input):
    """Find best matching response from Q&A data"""
    input_clean = normalize(user_input)
    best_score = 0
    best_response = None
    
    for item in qa_data:
        for keyword in item["keywords"]:
            keyword_clean = normalize(keyword)
            
            # Exact match
            if input_clean == keyword_clean:
                print(f"[Exact Match] '{input_clean}' → '{keyword_clean}'")
                return item["answer"]
            
            # Fuzzy match
            score = fuzz.partial_ratio(input_clean, keyword_clean)
            if score > best_score:
                best_score = score
                best_response = item["answer"]
    
    # Accept strong matches
    if best_score >= 88:
        print(f"[Fuzzy Match] Score: {best_score}")
        return best_response
    
    return None

def android_tts(text, output_path):
    """Use Android TTS via Termux API"""
    try:
        # Use termux-tts-speak command
        result = subprocess.run([
            "termux-tts-speak", text
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print(f"✅ Android TTS spoke: {text[:50]}...")
            return True
        else:
            print(f"❌ TTS failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ TTS timeout")
        return False
    except FileNotFoundError:
        print("❌ termux-tts-speak not found. Install Termux:API")
        return False
    except Exception as e:
        print(f"❌ TTS error: {e}")
        return False

@app.route("/")
def index():
    """Serve simple mobile web interface"""
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>AI Avatar Mobile</title>
        <style>
            body { font-family: Arial; margin: 20px; }
            .container { max-width: 400px; margin: 0 auto; }
            input, button { width: 100%; padding: 10px; margin: 5px 0; font-size: 16px; }
            .response { background: #f0f0f0; padding: 10px; margin: 10px 0; border-radius: 5px; }
            button { background: #007cba; color: white; border: none; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🤖 AI Avatar Mobile</h2>
            <input type="text" id="userInput" placeholder="Type your question..." />
            <button onclick="sendMessage()">Send</button>
            <button onclick="startListening()">🎤 Voice Input</button>
            <div id="response" class="response" style="display:none;"></div>
        </div>
        
        <script>
            function sendMessage() {
                const text = document.getElementById('userInput').value;
                if (!text.trim()) return;
                
                fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({text: text})
                })
                .then(r => r.json())
                .then(data => {
                    document.getElementById('response').innerHTML = data.response;
                    document.getElementById('response').style.display = 'block';
                    document.getElementById('userInput').value = '';
                });
            }
            
            function startListening() {
                if ('webkitSpeechRecognition' in window) {
                    const recognition = new webkitSpeechRecognition();
                    recognition.start();
                    recognition.onresult = function(event) {
                        document.getElementById('userInput').value = event.results[0][0].transcript;
                    };
                } else {
                    alert('Speech recognition not supported');
                }
            }
            
            document.getElementById('userInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') sendMessage();
            });
        </script>
    </body>
    </html>
    '''
    return html

@app.route("/chat", methods=["POST"])
def chat():
    """Handle chat requests with Android TTS"""
    try:
        data = request.get_json()
        user_input = data.get("text", "").strip()
        
        if not user_input:
            return jsonify({"error": "Empty input"}), 400
        
        print(f"📩 User: {user_input}")
        
        # Find scripted response
        response = find_scripted_response(user_input)
        
        if not response:
            response = "Sorry, I don't have information about that. Please contact customer service for assistance."
        
        print(f"🤖 Response: {response}")
        
        # Use Android TTS
        android_tts(response, None)
        
        return jsonify({
            "response": response,
            "source": "scripted" if find_scripted_response(user_input) else "fallback"
        })
        
    except Exception as e:
        print(f"❌ Chat error: {e}")
        return jsonify({
            "error": str(e),
            "response": "System error occurred"
        }), 500

@app.route("/status")
def status():
    """Check system status"""
    return jsonify({
        "status": "running",
        "platform": "android_termux",
        "qa_loaded": len(qa_data),
        "tts": "android_native"
    })

if __name__ == '__main__':
    print("🚀 Starting AI Avatar Mobile Server...")
    print("📱 Optimized for Android/Termux")
    print(f"📚 Loaded {len(qa_data)} Q&A pairs")
    
    # Run on all interfaces for mobile access
    app.run(host="0.0.0.0", port=5000, debug=False)
