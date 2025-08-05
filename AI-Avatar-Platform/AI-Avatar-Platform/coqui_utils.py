
"""
coqui_utils.py (For Audio Generation) ~ XTTS version


Purpose:
This module provides a utility function to convert input text into speech
using the Coqui TTS library. It loads a pre-trained TTS model and exposes
a function `synthesize_speech()` that generates a `.wav` audio file from
text input. The audio is saved to a specified path (default: static/audio/response.wav).


Used in the Flask backend to serve AI-generated speech for the AI Avatar Platform.
"""
from TTS.api import TTS
import os
from typing import Optional
import torch
import torchaudio

# NLTK-based punctuation support
import nltk
from nltk.tokenize import sent_tokenize
from nltk.data import find


def ensure_nltk_punkt():
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', quiet=True)
        print("✅ Downloaded NLTK punkt tokenizer.")

    # Manually download fallback resource if missing
    try:
        nltk.data.find('tokenizers/punkt_tab')
    except LookupError:
        nltk.download('punkt_tab', quiet=True)
        print("✅ Downloaded punkt_tab fallback.")

# Ensure it's available before usage
ensure_nltk_punkt()

import re
def preprocess_text(text: str) -> str:
    # 10‑15  ➜ 10 to 15
    text = re.sub(r"(\d+)-(\d+)", r"\1 to \2", text)

    # WWW → verbal form (pick ONE style)
    text = text.replace("www.", "double you double you double you dot ")
    # text = text.replace("www.", "w w w dot ")        # ← alternate shorter form

    # domain suffixes
    text = text.replace(".com", " dot com")

    # Acronyms that sound wrong
    text = re.sub(r"\bAI\b", "A I", text)

    return text


def punctuate_text(text: str) -> str:
    sentences = sent_tokenize(text)
    return " ".join(sentences)

# XTTS Setup
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
tts.to("cpu")
#tts.synthesizer.compute_type = "float16"
tts.synthesizer.compute_type = "float32"

client_voice_path = "client_voice/recording.wav"

# Warm-up to avoid initial delay
try:
    os.makedirs("client_voice/cache", exist_ok=True)
    warmup_path = "client_voice/cache/_warmup.wav"
    if not os.path.exists(warmup_path):
        tts.tts_to_file(
            text="hello how can i assist you today?",
            speaker_wav=client_voice_path,
            language="en",
            file_path=warmup_path
        )
        print("✅ XTTS warm-up completed.")
except Exception as e:
    print(f"⚠️ XTTS warm-up failed: {e}")

def synthesize_speech(text: str, output_path: str) -> Optional[str]:
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # clean / verbalise
        preprocessed = preprocess_text(text)

        # sentence segmentation (optional – comment out if it slows you down)
        punctuated = punctuate_text(preprocessed)

        print("📝  TTS input ▶", punctuated)

        tts.tts_to_file(
            text=punctuated,
            speaker_wav=client_voice_path,
            language="en",
            file_path=output_path
        )
        return output_path
    except Exception as e:
        print("❌ XTTS synthesis failed:", e)
        return None
    
# def generate_cloned_voice(text: str) -> Optional[str]:
#     output_path = os.path.join("static/audio", "response.wav")
#     return synthesize_speech(text, output_path) 
