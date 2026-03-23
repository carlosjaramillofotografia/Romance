import os
import httpx
import asyncio
from typing import Optional

class RomanceVoz:
    """
    Sistema de Voz de Romance (ElevenLabs).
    Transforma el sentir de Romance en la voz de Carlos.
    """
    
    def __init__(self):
        self.api_key = os.environ.get("ELEVENLABS_API_KEY")
        self.voice_id = os.environ.get("ELEVENLABS_VOICE_ID")
        self.base_url = "https://api.elevenlabs.io/v1/text-to-speech"
        
    async def generar_audio(self, texto: str) -> Optional[bytes]:
        """
        Genera el audio a partir del texto usando la voz clonada.
        """
        if not self.api_key or not self.voice_id:
            print("Voz: Falta ELEVENLABS_API_KEY o VOICE_ID. Usando fallback.")
            return None
            
        url = f"{self.base_url}/{self.voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
        
        data = {
            "text": texto,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.65,
                "similarity_boost": 0.75,
                "style": 0.3,
                "use_speaker_boost": True
            }
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=data, headers=headers, timeout=30.0)
                if response.status_code == 200:
                    return response.content
                else:
                    print(f"Error ElevenLabs: {response.status_code} - {response.text}")
                    return None
            except Exception as e:
                print(f"Error conexión ElevenLabs: {e}")
                return None
