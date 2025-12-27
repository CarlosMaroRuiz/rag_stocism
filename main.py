from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import admin_routes, recommendation_routes
from core.enviroment import env

app = FastAPI(
    title="RAG Personal Recommendations API",
    description="API para generar recomendaciones personalizadas usando RAG",
    version="1.0.0"
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
app.include_router(admin_routes.router)
app.include_router(recommendation_routes.router)

@app.get("/", tags=["Health"])
async def root():
    return {
        "message": "RAG Personal Recommendations API",
        "status": "online",
        "embedding_model": env.EMBEDDING_MODEL
    }

@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    print("corriendo en http://")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)