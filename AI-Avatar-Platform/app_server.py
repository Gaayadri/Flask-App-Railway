"""
app_server.py - Server-side Flask app for Hybrid Mobile Architecture

This version keeps all heavy AI processing on the server:
- XTTS TTS processing
- Whisper transcription 
- Ollama LLM fallback
- Q&A matching

Mobile clients connect via optimized API endpoints that return:
- Text responses
- Base64 encoded audio
- Optimized for mobile bandwidth
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from coqui_utils import synthesize_speech
from ollama_utils import generate_ollama_response
from rapidfuzz import fuzz
import os
import json
import re
import base64
import tempfile
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

from faster_whisper import WhisperModel

# Load environment variables
load_dotenv()
audio_dir = os.getenv("AUDIO_OUTPUT_DIR", "static/audio")

# Initialize models (keep heavy processing on server)
whisper_model = WhisperModel("base", compute_type="int8", device="cpu")

# Initialize Flask app with CORS for mobile clients
app = Flask(__name__, static_url_path='/static', static_folder='static')
CORS(app)  # Enable CORS for all routes

# Load Q&A data
qa_data = []
qa_file = os.getenv("QA_DATA_PATH", "data/qa_data.json")
try:
    if not os.path.exists(qa_file):
        raise FileNotFoundError(f"Q&A file not found at {qa_file}")
    with open(qa_file, "r", encoding="utf-8") as f:
        qa_data = json.load(f)
    print(f"✅ Loaded {len(qa_data)} Q&A pairs from {qa_file}")
except Exception as e:
    print(f"❌ Critical: Failed to load Q&A data: {str(e)}")

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
    best_matched_kw = ""

    for item in qa_data:
        for keyword in item["keywords"]:
            keyword_clean = normalize(keyword)

            # Exact match
            if input_clean == keyword_clean:
                print(f"[Exact Match] '{input_clean}' → '{keyword_clean}'")
                return item["answer"]

            # Fuzzy match
            score = fuzz.partial_ratio(input_clean, keyword_clean)
            if score > best_score or (score == best_score and len(keyword_clean) > len(best_matched_kw)):
                best_score = score
                best_response = item["answer"]
                best_matched_kw = keyword_clean

    # Accept strong matches
    if best_score >= 88:
        print(f"[Fuzzy Match] Score: {best_score} → {best_matched_kw}")
        return best_response

    return None

def audio_to_base64(file_path):
    """Convert audio file to base64 for mobile transmission"""
    try:
        with open(file_path, "rb") as audio_file:
            audio_data = audio_file.read()
            audio_b64 = base64.b64encode(audio_data).decode('utf-8')
            return audio_b64
    except Exception as e:
        print(f"❌ Audio encoding error: {e}")
        return None

@app.route("/")
def index():
    return jsonify({
        "message": "AI Avatar Server API",
        "status": "running",
        "endpoints": [
            "/mobile-chat - Complete chat with TTS",
            "/transcribe-mobile - Audio transcription", 
            "/generate-tts - Text to speech only",
            "/health - Server health check"
        ]
    })

@app.route("/mobile-chat", methods=["POST"])
def mobile_chat():
    """
    Complete mobile chat endpoint - handles Q&A matching, fallback to Ollama, and TTS
    Returns both text response and base64 audio for offline playback
    """
    try:
        data = request.get_json()
        user_input = data.get("text", "").strip()
        
        if not user_input:
            return jsonify({"error": "Text input required"}), 400
        
        print(f"📱 Mobile input: {user_input}")
        
        # Try scripted response first
        matched_response = find_scripted_response(user_input)
        
        if matched_response:
            print(f"📌 Scripted response: {matched_response}")
            response_text = matched_response
            source = "scripted"
        else:
            print("🔍 No match - using Ollama fallback")
            llm_response = generate_ollama_response(user_input)
            response_text = llm_response or "Sorry, I couldn't generate a response."
            source = "ollama"
        
        # Generate TTS audio
        os.makedirs(audio_dir, exist_ok=True)
        output_path = os.path.join(audio_dir, "mobile_response.wav")
        
        if not synthesize_speech(response_text, output_path):
            return jsonify({
                "response": response_text,
                "source": source,
                "audio_base64": None,
                "error": "TTS generation failed"
            }), 500
        
        # Convert audio to base64
        audio_b64 = audio_to_base64(output_path)
        
        # Calculate response size for mobile optimization
        response_size = len(audio_b64) if audio_b64 else 0
        print(f"📊 Response size: {response_size/1024:.1f}KB")
        
        return jsonify({
            "response": response_text,
            "source": source,
            "audio_base64": audio_b64,
            "audio_format": "wav",
            "audio_size_kb": round(response_size/1024, 1),
            "success": True
        })
        
    except Exception as e:
        print(f"❌ Mobile chat error: {e}")
        return jsonify({
            "error": str(e),
            "response": "System error occurred",
            "success": False
        }), 500

@app.route("/transcribe-mobile", methods=["POST"])
def transcribe_mobile():
    """
    Mobile-optimized audio transcription
    Accepts base64 audio or multipart file upload
    """
    try:
        # Handle base64 audio data
        if request.is_json:
            data = request.get_json()
            audio_b64 = data.get("audio_base64")
            if audio_b64:
                # Decode base64 audio
                audio_data = base64.b64decode(audio_b64)
                
                # Save to temporary file
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                    temp_file.write(audio_data)
                    temp_path = temp_file.name
                
                # Transcribe
                segments, info = whisper_model.transcribe(temp_path, language="en")
                transcript = " ".join(segment.text for segment in segments)
                
                # Cleanup
                os.unlink(temp_path)
                
                print(f"🗣️ Mobile transcript: {transcript}")
                return jsonify({
                    "transcript": transcript,
                    "language": info.language,
                    "success": True
                })
        
        # Handle multipart file upload (fallback)
        if 'file' in request.files:
            file = request.files['file']
            temp_path = os.path.join(audio_dir, f"temp_{file.filename}")
            file.save(temp_path)
            
            segments, info = whisper_model.transcribe(temp_path, language="en")
            transcript = " ".join(segment.text for segment in segments)
            
            os.unlink(temp_path)
            
            return jsonify({
                "transcript": transcript,
                "language": info.language,
                "success": True
            })
        
        return jsonify({"error": "No audio data provided"}), 400
        
    except Exception as e:
        print(f"❌ Transcription error: {e}")
        return jsonify({
            "error": str(e),
            "success": False
        }), 500

@app.route("/generate-tts", methods=["POST"])
def generate_tts_mobile():
    """
    Mobile TTS endpoint - just generates audio from text
    Returns base64 audio for mobile playback
    """
    try:
        data = request.get_json()
        text = data.get("text", "").strip()
        
        if not text:
            return jsonify({"error": "Text required"}), 400
        
        # Generate audio
        output_path = os.path.join(audio_dir, "tts_mobile.wav")
        
        if not synthesize_speech(text, output_path):
            return jsonify({"error": "TTS generation failed"}), 500
        
        # Convert to base64
        audio_b64 = audio_to_base64(output_path)
        
        return jsonify({
            "audio_base64": audio_b64,
            "audio_format": "wav",
            "text_sample": text[:100],
            "success": True
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/health", methods=["GET"])
def health_check():
    """Mobile client health check endpoint"""
    return jsonify({
        "status": "healthy",
        "server": "ai_avatar_server",
        "qa_loaded": len(qa_data),
        "models": {
            "whisper": "loaded",
            "xtts": "loaded",
            "ollama": "available"
        },
        "mobile_optimized": True
    })

@app.route("/qa-search", methods=["POST"])  
def qa_search():
    """
    Lightweight Q&A search without TTS
    For quick mobile responses
    """
    try:
        data = request.get_json()
        user_input = data.get("text", "").strip()
        
        response = find_scripted_response(user_input)
        
        return jsonify({
            "response": response or "No matching answer found",
            "found": response is not None,
            "success": True
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting AI Avatar Server for Mobile Clients...")
    print("📱 Mobile-optimized API endpoints ready")
    print(f"📚 Loaded {len(qa_data)} Q&A pairs")
    print("🌐 CORS enabled for cross-origin requests")
    
    # Run server - ready for deployment
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
