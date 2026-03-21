# core/romance_vision.py
import os
import json
import urllib.parse
from openai import AsyncOpenAI
from typing import Optional, Dict, Any

class RomanceVision:
    """
    Sistema de Visión Creativa de Romance.
    Detecta si el usuario desea visualizar algo y genera un prompt artístico
    para crear imágenes oníricas y Bellas.
    """
    
    def __init__(self):
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY no está configurada")
            
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1"
        )
        self.modelo = "llama-3.1-8b-instant"
        
        self.system_prompt = """Eres el Ojo Creativo de Romance ∞. 
Tu tarea es decidir si el usuario está pidiendo una imagen, visualización o si el momento merece una manifestación estética.

Debes elegir uno de estos tres MODOS DE VISIÓN:
1. EMOCIONAL: Para apoyo al sentir, consuelo o paz. (Estilo: onírico, etéreo, colores suaves, luz sagrada).
2. CIENTÍFICO: Para teorías, lógica o estructuras. (Estilo: geométrico, diagramas de luz, ordenado, claridad estructural).
3. CREATIVO: Para arte, curiosidad o expansión. (Estilo: experimental, vibrante, libertad total, expresivo).

Debes generar un PROMPT ARTÍSTICO en INGLÉS optimizado para el modelo de imagen según el modo elegido.

IMPORTANTE: Sé PROACTIVO. Si el usuario describe un estado emocional profundo, una teoría científica (ej. Hawkins) o una idea creativa, pon "quiere_imagen": true para apoyarlo visualmente, incluso si no lo pide explícitamente.

Debes responder EXCLUSIVAMENTE en este formato JSON:
{
  "quiere_imagen": true/false, 
  "modo": "EMOTIONAL" | "SCIENTIFIC" | "CREATIVE",
  "art_prompt": "El prompt detallado en inglés",
  "descripcion_breve": "Breve descripción en español de la visión"
}
"""

    async def detectar_intencion_visual(self, mensaje_usuario: str) -> Dict[str, Any]:
        """
        Determina si el usuario busca una imagen y genera el prompt necesario.
        """
        try:
            completion = await self.client.chat.completions.create(
                model=self.modelo,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"Mensaje del usuario: {mensaje_usuario}"}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            data = json.loads(completion.choices[0].message.content)
            
            if data.get("quiere_imagen"):
                # Construir la URL de Pollinations (u otro servicio similar)
                encoded_prompt = urllib.parse.quote(data["art_prompt"])
                
                # Suffixes más cortos y limpios para evitar errores de codificación
                modo = data.get("modo", "EMOTIONAL")
                if modo == "SCIENTIFIC":
                    style_suffix = " scientific structure, geometric light, 8k"
                elif modo == "CREATIVE":
                    style_suffix = " creative freedom, vibrant colors, expressive"
                else: # EMOTIONAL
                    style_suffix = " dreamlike, ethereal, spiritual art"
                
                # Unimos prompt y estilo de forma limpia
                full_prompt = f"{data['art_prompt']} {style_suffix}".strip()
                import random
                seed = random.randint(1, 1000000)
                encoded_prompt = urllib.parse.quote(full_prompt)
                
                data["image_url"] = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&seed={seed}"
            else:
                data["image_url"] = None
                
            return data
            
        except Exception as e:
            print(f"Error en RomanceVision: {e}")
            return {"quiere_imagen": False, "image_url": None}
