from google import genai
from google.genai import types

def process_voice_input(api_key: str, audio_bytes: bytes, action_mode: bool = False) -> str:
    """
    Processes voice audio using Gemini's native multimodal capabilities.
    If action_mode is True, transcribes the voice into a direct player combat command.
    If action_mode is False, acts as the Live Table Companion formatting encounter notes/loot.
    """
    client = genai.Client(api_key=api_key)
    
    if action_mode:
        prompt = (
            "You are a voice-to-action transcriber for a dark fantasy TTRPG. "
            "Listen to the player's voice command. "
            "Transcribe exactly what action the player wants to take in first person (e.g., 'I swing my sword at the goblin'). "
            "Output ONLY the player's action string with no extra formatting."
        )
    else:
        prompt = (
            "You are the Cardinal System and Live Table Companion for a TTRPG. "
            "Listen to this audio recording from the Game Master or player. "
            "1. Transcribe the core narration or action. "
            "2. Format it into clean, immersive TTRPG Markdown (e.g. bullet points, stat blocks, loot tables, or encounter notes). "
            "Output ONLY the resulting markdown log."
        )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav"),
            prompt
        ]
    )
    return response.text.strip()
