#--Old version--
import subprocess

def generate_ollama_response(prompt):
        result = subprocess.run(
            ["ollama", "run", "mistral", prompt],
            capture_output=True,
            text=True
        )
        return result.stdout.strip()

# ollama_utils.py
# import subprocess

# def generate_ollama_response(prompt: str) -> str:
#     import requests
#     payload = {
#         "model": "llama3",  # or any model installed via `ollama list`
#         "prompt": prompt
#     }
#     try:
#         res = requests.post("http://localhost:11434/api/generate", json=payload, stream=False)
#         data = res.json()
#         return data.get("response", "I'm sorry, I don't know how to answer that.")
#     except Exception as e:
#         print("⚠️ Ollama API error:", e)
#         return "Sorry, I'm currently unavailable to generate a response."

