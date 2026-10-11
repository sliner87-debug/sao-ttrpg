import toml
import os
from google import genai
from google.genai import types

try:
    secrets = toml.load(os.path.join(".streamlit", "secrets.toml"))
    api_key = secrets.get("GEMINI_API_KEY")

    client = genai.Client(api_key=api_key)
    print("Testing generate_content for image...")
    response = client.models.generate_content(
        model='gemini-3.1-flash-lite-image',
        contents="A test image of a futuristic sword",
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(
                aspect_ratio="16:9"
            ),
        )
    )
    
    success = False
    for part in response.parts:
        if part.inline_data:
            print("SUCCESS. Got bytes:", len(part.inline_data.data))
            success = True
    
    if not success:
        print("NO IMAGE DATA FOUND IN RESPONSE.")
        print(response)
        
except Exception as e:
    print("ERROR:")
    print(str(e))
