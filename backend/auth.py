import datetime
from google import genai

def get_ephemeral_token(api_key: str) -> str:
    """
    Mints a secure ephemeral token for the browser to connect to the Gemini Live API.
    Locks the model, system instructions, and text modality on the server side so 
    they cannot be tampered with by the frontend JavaScript.
    """
    client = genai.Client(api_key=api_key)
    now = datetime.datetime.now(tz=datetime.timezone.utc)

    token_response = client.auth_tokens.create(
        config={
            'uses': 1,
            'expire_time': now + datetime.timedelta(minutes=30),
            'new_session_expire_time': now + datetime.timedelta(minutes=1),
            'live_connect_constraints': {
                'model': 'gemini-3.8-live',
                'config': {
                    'response_modalities': ['TEXT'],
                    'system_instruction': {
                        'parts': [{'text': "You are a TTRPG Table Companion. Listen to the human GM. Do not speak. Respond only with structured Markdown tables and bullet points summarizing the combat, entities, or loot mentioned."}]
                    },
                    'session_resumption': {}
                }
            }
        }
    )
    
    # Return the token string to be injected into the Streamlit component
    return token_response.name
