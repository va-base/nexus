"""FastAPI application"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from nexus.api.routes import hypotheses, evidence, beliefs, investigations, companies, themes, claims

app = FastAPI(
    title="Nexus API",
    description="Investment Research System API",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(hypotheses.router, prefix="/api/hypotheses", tags=["hypotheses"])
app.include_router(evidence.router, prefix="/api/evidence", tags=["evidence"])
app.include_router(beliefs.router, prefix="/api/beliefs", tags=["beliefs"])
app.include_router(investigations.router, prefix="/api/investigations", tags=["investigations"])
app.include_router(companies.router, prefix="/api/companies", tags=["companies"])
app.include_router(themes.router, prefix="/api/themes", tags=["themes"])
app.include_router(claims.router, prefix="/api/claims", tags=["claims"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Nexus API v0.1.0"}

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
