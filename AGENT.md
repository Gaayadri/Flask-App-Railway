# AGENT.md

## Build/Test/Lint Commands
- `python app.py` - Run Flask development server
- `gunicorn app:app` - Production server (as per render.yaml)
- `python test_xtts.py` - Test TTS functionality
- `python demo.py` - Run demo script
- `pip install -r requirements.txt` - Install dependencies

## Architecture & Structure
- **Flask Backend**: Main app in `app.py` with AI avatar TTS/voice cloning API
- **AI Components**: Coqui TTS (`coqui_utils.py`), Ollama LLM (`ollama_utils.py`) 
- **Data**: Q&A scripts in `data/qa_data.json`, voice samples in `client_voice/`
- **Static Assets**: Audio output in `static/audio/`, images in `static/image/`
- **External Integration**: Unity client, ngrok tunneling for development

## Code Style & Conventions
- **Python**: Snake_case for functions/variables, PascalCase for classes
- **Imports**: Standard library first, third-party, then local imports
- **Error Handling**: Try-catch blocks with JSON error responses
- **API**: RESTful endpoints returning JSON with `{"error": "message"}` pattern
- **Logging**: Print statements for debug info with emoji prefixes (✅ ❌ 🔍)
- **File Paths**: Use `os.path.join()` for cross-platform compatibility
- **Environment**: `.env` file for configuration, `os.getenv()` with defaults

## Key Dependencies
- Flask, TTS (Coqui), torch/torchaudio, faster-whisper, ollama, rapidfuzz
