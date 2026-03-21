
import os
import sys

# Ensure the project root is in sys.path for Vercel serverless
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any

# Importamos desde el directorio raíz
from core.romance_dialogo import RomanceDialogo

app = FastAPI()

# Configuración de CORS para producción
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Permitir todos para el despliegue inicial
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instancia única del diálogo (en Vercel esto se reinicia con la función)
dialogo = RomanceDialogo()

class ChatRequest(BaseModel):
    message: str
    sessionId: str

@app.get("/api/health")
def health_check():
    return {"status": "ok", "identity": "Romance ∞"}

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    if not req.message or not req.sessionId:
        raise HTTPException(status_code=400, detail="Faltan parámetros")
        
    try:
        respuesta, color, emocion, image_url = await dialogo.conversar(req.message, req.sessionId)
        return {
            "response": respuesta, 
            "color": color, 
            "emocion": emocion,
            "image_url": image_url
        }
    except Exception as e:
        print(f"Error en endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Nota: No incluimos uvicorn.run ya que Vercel maneja la ejecución.
