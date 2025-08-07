# Hybrid Client-Server Deployment Guide

## Architecture Overview
- **Server**: Runs heavy AI models (XTTS, Whisper, Ollama) in the cloud
- **Android Client**: Lightweight web app that connects to server via HTTP API
- **Benefits**: Full AI power + mobile accessibility + internet required

## Server Deployment Options

### Option 1: Railway (Recommended)
```bash
# 1. Push to GitHub
git add .
git commit -m "Add hybrid mobile support"
git push origin main

# 2. Connect Railway to your GitHub repo
# 3. Add environment variables in Railway dashboard:
AUDIO_OUTPUT_DIR=static/audio
QA_DATA_PATH=data/qa_data.json

# 4. Railway will auto-deploy using:
# Build: pip install -r requirements.txt
# Start: python app_server.py
```

### Option 2: Render.com
```yaml
# Update render.yaml
services:
  - type: web
    name: ai-avatar-server
    env: python
    plan: starter
    buildCommand: pip install -r requirements.txt
    startCommand: python app_server.py
    envVars:
      - key: AUDIO_OUTPUT_DIR
        value: static/audio
```

### Option 3: Heroku
```bash
# Create Procfile
echo "web: python app_server.py" > Procfile

# Deploy
heroku create your-ai-avatar-app
git push heroku main
```

## Android Client Setup

### Method 1: Direct Browser Access
1. **Deploy server** (get URL like `https://your-app.railway.app`)
2. **Open android_client.html** on Android device
3. **Enter server URL** in settings
4. **Click Connect** and start chatting

### Method 2: Local File Access
1. **Copy android_client.html** to Android storage
2. **Open with Chrome browser** on Android
3. **Configure server URL** to your deployed server
4. **Use full AI features** remotely

### Method 3: Simple APK Wrapper (Advanced)
```javascript
// Use Cordova/PhoneGap to wrap the HTML as native app
cordova create AIAvatar com.yourcompany.aiavatar "AI Avatar"
cd AIAvatar
cordova platform add android
// Copy android_client.html to www/index.html
cordova build android
```

## Required Server Dependencies
```txt
# Keep full requirements.txt for server
Flask==3.1.1
flask-cors==6.0.1
TTS==0.22.0
faster-whisper==1.1.1
ollama==0.5.1
rapidfuzz==3.13.0
torch==2.1.2
torchaudio==2.1.2
python-dotenv==1.1.0
# ... (all existing dependencies)
```

## API Endpoints Available

### `/mobile-chat` (Main Endpoint)
```javascript
// Complete chat with TTS
fetch('/mobile-chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({text: "Hello"})
});

// Returns:
{
    "response": "Hello! How can I help you?",
    "source": "scripted",
    "audio_base64": "UklGRiQAAABXQVZF...",
    "audio_format": "wav",
    "success": true
}
```

### `/transcribe-mobile` (Voice Input)
```javascript
// Send audio for transcription
fetch('/transcribe-mobile', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({audio_base64: audioData})
});
```

### `/generate-tts` (TTS Only)
```javascript
// Just convert text to speech
fetch('/generate-tts', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({text: "Speak this"})
});
```

## Performance Optimizations

### Server-Side
- **Audio compression**: Base64 audio ~200KB per response
- **Caching**: Consider Redis for repeated Q&A
- **Load balancing**: Use multiple server instances for scale
- **CDN**: Serve static audio files via CDN

### Client-Side
- **Audio preload**: Cache frequent responses locally
- **Progressive loading**: Show text first, audio second
- **Offline fallback**: Store Q&A data locally for basic responses
- **Compression**: Use WebP images, minify JS/CSS

## Development Workflow
1. **Test locally**: Run `python app_server.py` on localhost
2. **Update client**: Point android_client.html to `http://your-ip:5000`
3. **Test on Android**: Access via browser on same network
4. **Deploy server**: Push to Railway/Render/Heroku
5. **Update client URL**: Point to production server
6. **Distribute**: Share android_client.html file or host it

## Troubleshooting

### Connection Issues
- Check CORS settings (already enabled)
- Verify server URL (include https://)
- Test server health endpoint: `/health`

### Audio Issues
- Check browser audio permissions
- Verify base64 audio decoding
- Test with smaller audio files first

### Performance Issues
- Monitor server response times
- Check mobile network speed
- Consider audio quality reduction for mobile

## Security Considerations
- **HTTPS only** for production
- **Rate limiting** to prevent abuse
- **API keys** if needed for authentication
- **Input validation** on all endpoints
