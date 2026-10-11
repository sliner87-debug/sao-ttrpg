import toml
import os
from google import genai
from google.genai import types

try:
    secrets = toml.load(os.path.join(".streamlit", "secrets.toml"))
    api_key = secrets.get("GEMINI_API_KEY")

    client = genai.Client(api_key=api_key)
    print("Testing image generation...")
    result = client.models.generate_images(
        model='gemini-2.5-flash-image',
        prompt="A test image of a futuristic sword",
        config=types.GenerateImagesConfig(
            number_of_images=1,
            aspect_ratio="16:9"
        )
    )
    print("SUCCESS. Got bytes:", len(result.generated_images[0].image.image_bytes))
except Exception as e:
    print("ERROR:")
    print(str(e))
