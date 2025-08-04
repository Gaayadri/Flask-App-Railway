"""
app.py

Purpose:
Flask backend for 2D AI Avatar Platform with:
- Coqui TTS audio generation
- Scripted Q&A with Ollama fallback
- Ngrok integration
- Full-body avatar image serving
"""

from flask import Flask, jsonify, request, send_file
from dotenv import load_dotenv
from coqui_utils import synthesize_speech
from ollama_utils import generate_ollama_response
from rapidfuzz import fuzz
import os
import requests
import json
import re
import string
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

from TTS.api import TTS
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import XttsAudioConfig, XttsArgs
from TTS.config.shared_configs import BaseDatasetConfig
from textwrap import wrap

import torchaudio
import torch

# Add required globals for safe unpickling
torch.serialization.add_safe_globals([
    XttsConfig,
    XttsAudioConfig,
    BaseDatasetConfig,
    XttsArgs
])

# Load environment variables
load_dotenv()
audio_dir = os.getenv("AUDIO_OUTPUT_DIR", "static/audio")

# Load model once
from faster_whisper import WhisperModel
#whisper_model = WhisperModel("base")  # or "small", "medium", "large"
whisper_model = WhisperModel("base", compute_type="int8", device="cpu")


# Initialize Flask app
app = Flask(__name__, static_url_path='/static', static_folder='static')
ngrok_url = None

def fetch_ngrok_url():
    """Fetch ngrok public URL if available"""
    try:
        res = requests.get("http://127.0.0.1:4040/api/tunnels")
        tunnels = res.json().get("tunnels", [])
        return next((t["public_url"] for t in tunnels if t["proto"] == "https"), None)
    except Exception as e:
        print(f"⚠️ Ngrok error: {str(e)}")
        return None


@app.route("/")
def index():
    return jsonify({
        "message": "OWNDAYS AI Avatar Backend",
        "status": "running"
    })


@app.route("/ngrok-url", methods=["GET"])
def get_ngrok_url():
    global ngrok_url
    ngrok_url = ngrok_url or fetch_ngrok_url()
    return jsonify({"url": ngrok_url}) if ngrok_url else jsonify({"error": "Ngrok unavailable"}), 500


@app.route("/generate-audio", methods=["POST"])
def generate_audio():
    """Generate speech audio from text"""
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "Text required"}), 400


    try:
        text = data["text"]
        output_path = os.path.join(audio_dir, "response.wav")
       
        if not synthesize_speech(text, output_path):
            return jsonify({"error": "TTS failed"}), 500


        if request.args.get('download') == 'true':
            return send_file(output_path, mimetype="audio/wav")


        return jsonify({
            "audio_url": f"{ngrok_url or ''}/static/audio/response.wav",
            "text_sample": text[:100]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Scripted Q&A System
# Replace the current qa_data loading block with:
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
    # Consider exiting if Q&A data is essential
    # sys.exit(1)

def normalize(text):
    """Lowercase, strip, remove punctuation and multiple spaces"""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", "", text)        # Remove punctuation
    text = re.sub(r"\s+", " ", text)           # Remove extra spaces
    return text

def find_scripted_response(user_input):
    input_clean = normalize(user_input)
    best_score = 0
    best_response = None
    best_matched_kw = ""

    for item in qa_data:
        for keyword in item["keywords"]:
            keyword_clean = normalize(keyword)

            # ✅ Exact match
            if input_clean == keyword_clean:
                print(f"[Exact Match] '{input_clean}' → '{keyword_clean}'")
                return item["answer"]

            # ✅ Fuzzy match
            score = fuzz.partial_ratio(input_clean, keyword_clean)

            # Boost longer phrases slightly
            if score > best_score or (score == best_score and len(keyword_clean) > len(best_matched_kw)):
                best_score = score
                best_response = item["answer"]
                best_matched_kw = keyword_clean

    # Only accept fuzzy matches if score is strong enough
    # You can adjust these thresholds if needed
    if best_score >= 88:
        print(f"[Fuzzy Match] Score: {best_score} → {best_matched_kw}")
        return best_response

    return None

#**Old version of /scripted-response**

# @app.route("/scripted-response", methods=["POST"])
# def scripted_response():
#     print("✅ Flask received POST to /scripted-response")
#     """Fuzzy match Q&A for Unity"""
#     try:
#         user_input = request.get_json().get("text", "").strip()
#         if not user_input:
#             return jsonify({"error": "Empty input"}), 400

#         response = find_scripted_response(user_input)

#         if response:
#             return jsonify({
#                 "response": response,
#                 "source": "fuzzy_script",
#                 "needs_tts": True
#             })
#         else:
#             return jsonify({
#                 "response": "Sorry I don't have the information, please contact customer service for further assistance.",
#                 "source": "fallback",
#                 "needs_tts": True
#             })

#     except Exception as e:
#         return jsonify({
#             "error": str(e),
#             "response": "System error occurred",
#             "needs_tts": False
#         }), 500

# New version of /scripted-response which ~ auto-handles both: Scripted Q&A and Ollama fallback.
# @app.route("/scripted-response", methods=["POST"])
# def scripted_response():
#     print("✅ Flask received POST to /scripted-response")

#     try:
#         user_input = request.get_json().get("text", "").strip()
#         if not user_input:
#             return jsonify({"error": "Empty input"}), 400

#         # Try fuzzy match against QA data
#         response = find_scripted_response(user_input)

#         if response:
#             print(f"📌 Scripted response matched: {response}")
#         else:
#             print("🔍 No match in QA — using fallback Ollama")

#             # Fallback to Ollama
#             llm_response = generate_ollama_response(user_input)
#             response = llm_response or "Sorry, I couldn't generate a response."

#         # Generate voice
#         output_path = os.path.join("static/audio", "response.wav")
#         if not synthesize_speech(response, output_path):
#             return jsonify({"error": "TTS failed"}), 500

#         return jsonify({
#             "response": response,
#             "audio_path": f"{ngrok_url or ''}/static/audio/response.wav",
#             "source": "fuzzy_script" if find_scripted_response(user_input) else "ollama_fallback",
#             "needs_tts": True
#         })

#     except Exception as e:
#         return jsonify({
#             "error": str(e),
#             "response": "System error occurred",
#             "needs_tts": False
#         }), 500

#New version to troubleshoot ollama generation
@app.route("/scripted-response", methods=["POST"])
def scripted_response():
    print("✅ Flask received POST to /scripted-response")

    try:
        user_input = request.get_json().get("text", "").strip()
        if not user_input:
            return jsonify({"error": "Empty input"}), 400

        # Try fuzzy match against QA data
        matched_response = find_scripted_response(user_input)

        if matched_response:
            print(f"📌 Scripted response matched: {matched_response}")
            response_text = matched_response
            source = "fuzzy_script"
        else:
            print("🔍 No match in QA — using fallback Ollama")
            llm_response = generate_ollama_response(user_input)
            response_text = llm_response or "Sorry, I couldn't generate a response."
            source = "ollama_fallback"

        # Generate audio
        output_path = os.path.join("static/audio", "response.wav")
        if not synthesize_speech(response_text, output_path):
            return jsonify({"error": "TTS failed"}), 500

        print(f"[🎤 XTTS audio]: {output_path}")
        return jsonify({
            "response": response_text,
            "audio_path": f"{ngrok_url or ''}/static/audio/response.wav",
            "source": source,
            "needs_tts": True
        })

    except Exception as e:
        print("❌ Error in /scripted-response:", e)
        return jsonify({
            "error": str(e),
            "response": "System error occurred",
            "needs_tts": False
        }), 500
   
@app.route("/transcribe-audio", methods=["POST"])
def transcribe_audio():
    if 'file' not in request.files:
        return jsonify({"error": "No audio file uploaded"}), 400


    file = request.files['file']
    os.makedirs("static/audio", exist_ok=True)  # ensure folder exists
    file_path = os.path.join("static/audio", file.filename)
    file.save(file_path)


    try:
        segments, info = whisper_model.transcribe(file_path, language="en")
        transcript = " ".join(segment.text for segment in segments)
        print(f"[🗣 Whisper Transcript] {transcript}")
        return jsonify({"transcript": transcript})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Normalization function
def normalize_text(text):
    return re.sub(r'[^a-z0-9]', '', text.lower())  # Removes punctuation and upper/lower case differences


# **Troubleshooting for ollama generation**
@app.route("/generate-cloned-voice", methods=["POST"])
def generate_cloned_voice():
    data = request.json 
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "Text is required"}), 400

    # *Normalize input for consistent hashing
    # fallback_text = "Sorry I don't have the information, please contact customer service for further assistance."

    # Normal XTTS voice generation — no caching
    output_path = os.path.join("static/audio", "response.wav")

    if not synthesize_speech(text, output_path):
        return jsonify({"error": "TTS failed"}), 500

    print(f"[🎤 Generated Audio]: {output_path}")
    return jsonify({"audio_path": output_path})


#**Ollama integration**
@app.route("/fallback-ollama", methods=["POST"])
def fallback_ollama():
    """Calls local Ollama LLM and returns TTS audio of response"""
    try:
        user_input = request.get_json().get("text", "").strip()
        if not user_input:
            return jsonify({"error": "Text is required"}), 400

        print(f"📩 User input: {user_input}")
        print("⚠️ No match found. Routing to /fallback-ollama.")

        # 1. Get response from Ollama
        llm_response = generate_ollama_response(user_input)
        print(f"🤖 Ollama response: {llm_response}")

        # 2. Generate cloned voice
        audio_path = os.path.join("static/audio", "response.wav")
        if not synthesize_speech(llm_response, audio_path):
            return jsonify({"error": "TTS failed"}), 500

        # 3. Return both audio path and text
        return jsonify({
            "response": llm_response,
            "audio_path": f"{ngrok_url or ''}/static/audio/response.wav"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@app.route("/fullbody-avatar", methods=["GET"])
def serve_avatar():
    """Serve the avatar image"""
    return send_file("static/image/full_body_avatar.png", mimetype="image/png")


if __name__ == '__main__':
    from flask_cors import CORS
    CORS(app)  # Enable CORS
   
    # Initialize ngrok URL
    ngrok_url = fetch_ngrok_url()
    if ngrok_url:
        print(f"\n🔗 Ngrok URL: {ngrok_url}")
        print(f"🔊 Audio endpoint: {ngrok_url}/generate-audio")
    else:
        print("⚠️ Ngrok not detected - localhost only")
   
   #app.run(host="0.0.0.0", port=5000, debug=True)
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
