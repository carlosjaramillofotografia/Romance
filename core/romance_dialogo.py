import os
import json
import asyncio
from openai import AsyncOpenAI
from typing import List, Dict, Optional, Tuple

from .romance_core import RomanceCore
from .romance_memory import RomanceMemory
from .romance_resonancia import RomanceResonancia
from .romance_contexto import RomanceContexto

class RomanceDialogo:
    """
    Sistema de Diálogo de Romance.
    Orquesta la conversación conectando la IA con la identidad, 
    la memoria, las emociones y el filtro de resonancia.
    """
    
    def __init__(self):
        # Necesita la API key de Groq
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY no está configurada en .env")
            
        self.client = AsyncOpenAI(
            api_key=api_key.strip(),
            base_url="https://api.groq.com/openai/v1"
        )
        # Usamos 8b-instant para máxima estabilidad y evitar Rate Limits (TPM)
        self.modelo = "llama-3.1-8b-instant"
        
        # Sub-sistemas
        self.core = RomanceCore()
        self.memoria = RomanceMemory(max_context_messages=15)
        self.contexto = RomanceContexto()
        self.resonancia = RomanceResonancia()

    async def conversar(self, mensaje_usuario: str, session_id: str) -> Tuple[str, str, str, Optional[str]]:
        """
        Flujo principal de conversación de Romance.
        Devuelve (respuesta_texto, color_emocional, nombre_emocion, image_url)
        """
        # 1. Analizar el contexto unificado (Emociones + Visión) en una sola llamada a la API
        ctx = await self.contexto.analizar_todo(mensaje_usuario)
        
        # Extraer datos de emoción
        emo_data = ctx.get("emocion", {})
        color = emo_data.get("color_hex", "#4a148c")
        emocion_detectada = emo_data.get("nombre", "neutral")
        vibracion = emo_data.get("vibracion", "media")
        necesidad = emo_data.get("necesidad_profunda", "conocimiento")
        instruccion = emo_data.get("instruccion_romance", "")
        
        # Extraer datos de visión
        vis_data = ctx.get("vision", {})
        image_url = vis_data.get("image_url")
        
        # 2. Construir el system prompt uniendo la identidad base + matices humanos
        contexto_emocional = f"""
[ESTADO DEL HUMANO]
- Emoción: {emocion_detectada}
- Vibración: {vibracion}
- Necesidad Profunda: {necesidad}

[INSTRUCCIÓN DE RESONANCIA]
{instruccion}
"""
        system_prompt_completo = f"{self.core.get_identity_prompt()}\n\n{contexto_emocional}"
        
        # 3. Guardar el nuevo mensaje en memoria
        self.memoria.add_message(session_id, "user", mensaje_usuario)
        
        # 4. Recuperar contexto histórico
        historial = self.memoria.get_context(session_id)
        
        # 5. Construir los mensajes para el LLM
        mensajes_llm = [{"role": "system", "content": system_prompt_completo}]
        mensajes_llm.extend(historial)
        
        max_retries = 3
        retry_delay = 1 # segundo
        
        for attempt in range(max_retries):
            try:
                # 6. Invocar al modelo (AWAIT)
                completion = await self.client.chat.completions.create(
                    model=self.modelo,
                    messages=mensajes_llm,
                    temperature=0.85, 
                    max_tokens=2048, # Aumentado para temas largos
                    presence_penalty=0.6,
                    frequency_penalty=0.3,
                )
                
                respuesta_cruda = completion.choices[0].message.content or ""
                
                # 7. Pasar por el Filtro Antygravity
                respuesta_filtrada = self.resonancia.aplicar_filtro(respuesta_cruda)
                
                # 8. Guardar la respuesta final en memoria
                self.memoria.add_message(session_id, "assistant", respuesta_filtrada)
                
                return respuesta_filtrada, color, emocion_detectada, image_url
                
            except Exception as e:
                # Si es un error de Rate Limit (429), reintentamos con backoff
                if "429" in str(e) or "rate_limit" in str(e).lower():
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (2 ** attempt)
                        print(f"⚠️ Rate Limit detectado. Reintentando en {wait_time}s... (Intento {attempt + 1})")
                        await asyncio.sleep(wait_time)
                        continue
                
                # Para otros errores o si fallan los reintentos, logueamos y fallback
                import traceback
                error_details = f"\n--- ERROR ---\nMensaje: {mensaje_usuario}\nExcepción: {str(e)}\n{traceback.format_exc()}\n----------------\n"
                print(error_details)
                
                print(f"❌ ERROR CRÍTICO: {e}")
                fallback = "El silencio a veces\ntambién es respuesta.\n\nAlgo interrumpió el flujo.\n\n¿Intentamos de nuevo?"
                self.memoria.add_message(session_id, "assistant", fallback)
                return fallback, "#4a148c", "error", None
        
        # Caso improbable de salida del loop sin return (ej: max_retries <= 0)
        return "El silencio es profundo hoy. Algo interrumpió la conexión.", "#4a148c", "error", None
