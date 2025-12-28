from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import admin_routes, exercise_routes, auth_routes
from core.enviroment import env

# Deshabilitar documentación en producción
docs_url = "/docs" if env.APP_ENV == "dev" else None
redoc_url = "/redoc" if env.APP_ENV == "dev" else None

app = FastAPI(
    title="RAG Stoic Exercises API",
    description="API para generar ejercicios estoicos personalizados usando RAG",
    version="1.0.0",
    docs_url=docs_url,
    redoc_url=redoc_url,
    root_path="/ia"  # Prefijo para funcionar bajo web.estoico.app/ia
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(auth_routes.router)
app.include_router(admin_routes.router)
app.include_router(exercise_routes.router)

@app.get("/", tags=["Health"])
async def root():
    return {
        "message": "RAG Stoic Exercises API",
        "status": "online",
        "embedding_model": env.EMBEDDING_MODEL
    }

@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001)