import toml
import os
from google import genai

try:
    secrets = toml.load(os.path.join(".streamlit", "secrets.toml"))
    api_key = secrets.get("GEMINI_API_KEY")

    client = genai.Client(api_key=api_key)
    print("Fetching models...")
    models = client.models.list_models()
    image_models = [m.name for m in models if 'image' in m.name or 'imagen' in m.name]
    print("Available image models:")
    print(image_models)
except Exception as e:
    print("ERROR:", str(e))
