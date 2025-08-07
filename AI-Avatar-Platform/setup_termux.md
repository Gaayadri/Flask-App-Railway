# Setup Guide: AI Avatar on Android 11 via Termux

## Step 1: Install Termux
1. Download Termux from F-Droid (not Play Store): https://f-droid.org/packages/com.termux/
2. Install Termux:API from F-Droid: https://f-droid.org/packages/com.termux.api/

## Step 2: Setup Termux Environment
```bash
# Update packages
pkg update && pkg upgrade

# Install Python and dependencies
pkg install python git

# Install pip packages
pip install flask rapidfuzz

# Grant storage permission
termux-setup-storage
```

## Step 3: Copy Your App Files
```bash
# Create project directory
mkdir ~/ai-avatar
cd ~/ai-avatar

# Copy files from your PC to Android storage, then:
cp /storage/emulated/0/Download/app_mobile.py .
cp /storage/emulated/0/Download/requirements_mobile.txt .
cp -r /storage/emulated/0/Download/data .
```

## Step 4: Run the App
```bash
# Start the server
python app_mobile.py

# Server will run on: http://localhost:5000
# Access from Android browser: http://127.0.0.1:5000
```

## Step 5: Enable TTS (Optional)
```bash
# Install Termux:API for native Android TTS
pkg install termux-api

# Test TTS
termux-tts-speak "Hello, this is a test"
```

## Features Available:
- ✅ Q&A matching with fuzzy search
- ✅ Web interface optimized for mobile
- ✅ Android native TTS (with Termux:API)
- ✅ Voice input (Chrome browser support)
- ❌ No voice cloning (too heavy for mobile)
- ❌ No Ollama LLM (fallback to simple responses)

## Troubleshooting:
- **TTS not working**: Install Termux:API and grant permissions
- **Port already in use**: Change port in app_mobile.py line 157
- **Permission denied**: Run `termux-setup-storage` and grant access
- **Slow performance**: Close other apps, Android 11+ recommended

## Performance Tips:
- Use WiFi for better stability
- Close other heavy apps
- Keep device plugged in during development
- Consider using external keyboard for coding
