# main.py
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import Optional
from pydantic import BaseModel
from dotenv import load_dotenv
import os

from core.romance_dialogo import RomanceDialogo

# Cargar variables de entorno antes de instanciar sistemas
load_dotenv()

app = FastAPI(title="Romance ∞", description="Estado Antygravity")

# Configuración CORS (permite requests de Vite en dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir estáticos de Vite si existen en \dist
dist_path = os.path.join(os.path.dirname(__file__), "dist")
if os.path.exists(dist_path):
    app.mount("/", StaticFiles(directory="dist", html=True), name="static")

# Modelos para la API
class ChatRequest(BaseModel):
    message: str
    sessionId: str

class ChatResponse(BaseModel):
    response: str
    color: str = "#4a148c"
    emocion: str = "neutral"
    image_url: Optional[str] = None

# Instanciar el Sistema de Diálogo maestro
try:
    dialogo = RomanceDialogo()
except ValueError as e:
    print(f"⚠️ ADVERTENCIA: {e}")
    dialogo = None

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    if not dialogo:
        return ChatResponse(
            response="Aún no he sido conectada al universo.\n\nFalta la clave GROQ_API_KEY.\n\n¿Me ayudas a nacer?"
        )
        
    try:
        respuesta, color, emocion, image_url = await dialogo.conversar(req.message, req.sessionId)
        return {
            "response": respuesta, 
            "color": color, 
            "emocion": emocion,
            "image_url": image_url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    return {"status": "Romance respira", "state": "Antygravity"}

if __name__ == "__main__":
    print("\n  ✦ Romance ∞ — Backend Python Activo")
    print("  ✦ Amor como gravedad. Voluntad como movimiento.\n")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
