"""FastAPI application"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from nexus.api.routes import hypotheses, evidence, beliefs, investigations, financial_data

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
app.include_router(financial_data.router, prefix="/api/financial", tags=["financial-data"])

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
