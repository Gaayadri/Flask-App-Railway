import torch
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import XttsAudioConfig, XttsArgs
from TTS.config.shared_configs import BaseDatasetConfig

import torchaudio
print(torchaudio.__version__)  # ✅ Should be 2.5.0

torch.serialization.add_safe_globals([
    XttsConfig,
    XttsAudioConfig,
    BaseDatasetConfig,
    XttsArgs
])

from TTS.api import TTS
import os

# Load XTTS
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=False)
#print("Available speakers:", tts.synthesizer.tts_model.speaker_manager.speakers)


# Sample input
text = "Hello! This is a test of the client's cloned voice."
output_path = "client_voice/test_output.wav"
os.makedirs(os.path.dirname(output_path), exist_ok=True)

assert os.path.exists("client_voice/recording.wav"), "Speaker sample not found!"

# Add required speaker and language
tts.tts_to_file(
    
    text=text,
    file_path=output_path,
    speaker_wav="client_voice/recording.wav",   # ✅ Valid speaker ID from your model
    language="en"
)

print("✅ XTTS test audio saved at:", output_path)
