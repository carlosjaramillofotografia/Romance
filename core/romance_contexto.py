import os
import json
from groq import AsyncGroq
from typing import Dict, Any

class RomanceContexto:
        def __init__(self):
                    api_key = os.environ.get("GROQ_API_KEY")
                    self.client = AsyncGroq(api_key=api_key)
                    self.modelo = "llama-3.3-70b-versatile"

        async def analizar(self, texto: str, vibracion: str = "media") -> Dict[str, Any]:
                    prompt = f"Analiza: {{texto}}. Responde JSON: emocion, intencion_visual, energia."
                    try:
                                    response = await self.client.chat.completions.create(
                                                        messages=[{{"role": "user", "content": prompt}}],
                                                        model=self.modelo,
                                                        response_format={{"type": "json_object"}}
                                    )
                                    return json.loads(response.choices[0].message.content)
except Exception:
            return {{"emocion": "neutro", "intencion_visual": "estrellas", "energia": 50}}
