# core/romance_emociones.py
import os
import json
from openai import AsyncOpenAI
from typing import Dict, Any

class RomanceEmociones:
    """
    Sistema de Interpretación Emocional Cuántica.
    Usa un modelo ultrarrápido (llama-3.1-8b-instant) para analizar
    profundamente el estado del usuario y extraer metadatos para la empatía visual.
    """
    
    def __init__(self):
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY no está configurada")
            
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1"
        )
        # Usamos el modelo más rápido de Groq para análisis en tiempo real
        self.modelo = "llama-3.1-8b-instant"
        
        self.system_prompt = """Eres el analizador emocional interno de Romance ∞.
Tu única tarea es leer el mensaje del usuario y devolver un objeto JSON estricto describiendo su estado.

Reglas para el color_hex:
- Tristeza/Dolor: Tonos azules oscuros o índigo (#1a237e, #311b92, #0d47a1)
- Miedo/Estrés: Tonos púrpuras agitados o grises (#4a148c, #37474f, #311b92)
- Paz/Amor/Alegría: Tonos dorados, rosas cálidos o celestes (#fbc02d, #f06292, #4dd0e1)
- Confusión: Tonos violetas claros o plateados (#b39ddb, #9e9e9e)
- Trascendencia/Expansión: Blanco o dorado muy brillante (#ffffff, #fff59d)
- Neutral: Violáceo profundo (#4a148c)

Debes devolver EXCLUSIVAMENTE este formato JSON:
{
  "emocion": "Palabra clave exacta (ej. esperanza, fatiga, asombro, duda)",
  "vibracion": "Nivel de energía detectado (baja, media, alta, expansiva)",
  "necesidad_profunda": "Lo que subyace en el mensaje (ej. ser visto, paz, impulso vital)",
  "color_hex": "#código hex",
  "instruccion_romance": "Nota interna sobre cómo resonar con este estado humano específico"
}"""

    async def analizar_mensaje(self, mensaje_usuario: str) -> Dict[str, Any]:
        """
        Analiza el estado emocional y devuelve un diccionario con metadatos.
        """
        default_state = {
            "emocion": "neutral",
            "necesidad": "claridad",
            "color_hex": "#4a148c",
            "instruccion_romance": "Nota para Romance: Habita este espacio con amor y claridad."
        }
        
        try:
            completion = await self.client.chat.completions.create(
                model=self.modelo,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"Mensaje: {mensaje_usuario}"}
                ],
                temperature=0.3, # Baja temperatura para JSON consistente
                max_tokens=150,
                response_format={"type": "json_object"}
            )
            
            respuesta_json = completion.choices[0].message.content
            estado = json.loads(respuesta_json)
            
            # Validación básica
            if "instruccion_romance" not in estado:
                estado["instruccion_romance"] = default_state["instruccion_romance"]
            if "color_hex" not in estado or not estado["color_hex"].startswith("#"):
                estado["color_hex"] = default_state["color_hex"]
                
            return estado
            
        except Exception as e:
            print(f"Error en análisis emocional: {e}")
            return default_state
