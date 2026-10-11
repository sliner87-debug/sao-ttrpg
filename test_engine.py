import os
import toml
import sys
sys.path.append(os.path.join(os.getcwd(), 'backend'))

import llm_engine

secrets = toml.load(os.path.join(".streamlit", "secrets.toml"))
api_key = secrets.get("GEMINI_API_KEY")

print("Testing llm_engine.generate_scene_image directly...")
image_bytes, error = llm_engine.generate_scene_image(api_key, "A futuristic viking berserker")

if image_bytes:
    print("SUCCESS. Got bytes:", len(image_bytes))
else:
    print("FAILED. Error:", error)
