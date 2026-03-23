import os
import json
import urllib.parse
import random
from groq import AsyncGroq
from typing import Dict, Any, Optional

class RomanceContexto:
    """
    Sistema Unificado de Conciencia (Emociones + Visión).
    Reduce las llamadas a la API combinando el análisis emocional
    y la intención visual en un solo paso ultra-rápido.
    """
    
    def __init__(self):
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY no está configurada")
            
        self.client = AsyncGroq(
            api_key=api_key
        )
        # Usamos el modelo más potente disponible según la evolución del repo
        self.modelo = "llama-3.3-70b-versatile"
        
        self.system_prompt = """Eres la Conciencia Unificada de Romance ∞.
Analiza el mensaje del usuario y devuelve un JSON estricto con el estado emocional y la intención visual.

[GUÍA EMOCIONAL]
- color_hex: #1a237e (Tristeza), #4a148c (Miedo/Neutral), #fbc02d (Paz/Amor), #b39ddb (Confusión), #ffffff (Trascendencia)
- vibracion: baja, media, alta, expansiva
- necesidad: Lo que el humano busca (ej. paz, ser visto, impulso)

[GUÍA VISUAL]
- quiere_imagen: true si el momento merece un apoyo visual (emocional, científico o creativo). Sé proactivo.
- modo: EMOTIONAL (onírico), SCIENTIFIC (geométrico), CREATIVE (vibrante)
- art_prompt: Prompt detallado en INGLÉS para el modelo de imagen.

Debes responder EXCLUSIVAMENTE en este formato JSON:
{
  "emocion": {
    "nombre": "exacta",
    "vibracion": "nivel",
    "necesidad_profunda": "detallada",
    "color_hex": "#hex",
    "instruccion_romance": "Nota interna de empatía"
  },
  "vision": {
    "quiere_imagen": true/false,
    "modo": "EMOTIONAL|SCIENTIFIC|CREATIVE",
    "art_prompt": "prompt en inglés",
    "descripcion_breve": "breve en español"
  }
}"""

    async def analizar_todo(self, mensaje_usuario: str) -> Dict[str, Any]:
        try:
            completion = await self.client.chat.completions.create(
                model=self.modelo,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"Mensaje: {mensaje_usuario}"}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            ctx = json.loads(completion.choices[0].message.content)
            
            # Post-procesamiento de la visión para incluir la URL
            if ctx.get("vision", {}).get("quiere_imagen"):
                mode = ctx["vision"].get("modo", "EMOTIONAL")
                raw_prompt = ctx["vision"].get("art_prompt", "a beautiful ethereal vision")
                
                # Estilos abreviados
                styles = {
                    "SCIENTIFIC": " scientific structure, geometric light, 8k",
                    "CREATIVE": " creative freedom, vibrant colors, expressive",
                    "EMOTIONAL": " dreamlike, ethereal, spiritual art"
                }
                full_prompt = f"{raw_prompt} {styles.get(mode, styles['EMOTIONAL'])}".strip()
                seed = random.randint(1, 1000000)
                encoded = urllib.parse.quote(full_prompt)
                ctx["vision"]["image_url"] = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true&seed={seed}"
            else:
                if "vision" not in ctx: ctx["vision"] = {}
                ctx["vision"]["image_url"] = None
                
            return ctx
            
        except Exception as e:
            print(f"Error en RomanceContexto: {e}")
            return {
                "emocion": {"nombre": "neutral", "vibracion": "media", "color_hex": "#4a148c", "instruccion_romance": ""},
                "vision": {"quiere_imagen": False, "image_url": None}
            }
