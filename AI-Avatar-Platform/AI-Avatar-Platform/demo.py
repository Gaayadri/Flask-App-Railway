# # demo.py

# from coqui_utils import synthesize_speech
# from did_utils import generate_avatar_video, poll_talk_status
# import requests

# def fetch_ngrok_url():
#     try:
#         res = requests.get("http://127.0.0.1:4040/api/tunnels")
#         tunnels = res.json().get("tunnels", [])
#         for tunnel in tunnels:
#             if tunnel["proto"] == "https":
#                 return tunnel["public_url"]
#         return None
#     except Exception as e:
#         raise Exception("⚠️ Failed to fetch ngrok URL. Is ngrok running?") from e

# NGROK_URL = fetch_ngrok_url()

# AUDIO_PATH = "static/audio/response.wav"
# IMAGE_URL = f"{NGROK_URL}/static/image/avatar.png"
# AUDIO_URL = f"{NGROK_URL}/static/audio/response.wav"

# # Step 1: Create speech
# synthesize_speech("Hello! I’m Sara, your AI Avatar. How can I help you today!", AUDIO_PATH)

# # Step 2: Generate video
# talk_id = generate_avatar_video(AUDIO_URL, IMAGE_URL)
# video_url = poll_talk_status(talk_id)

# print("🎬 Your avatar video is ready:")
# print(video_url)

