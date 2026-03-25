import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
from test import VerifyClaimTest

# 1. Modern Lifespan Handler (Replaces @app.on_event)
@asynccontextmanager
async def lifespan(app: FastAPI):
    global brain
    # Startup: Load the heavy AI models once
    brain = VerifyClaimTest()
    yield
    # Shutdown: Clean up if necessary
    del brain

app = FastAPI(title="Fact-Check API", lifespan=lifespan)

# 2. Add CORS Middleware (Fixes the 405 Method Not Allowed error)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (perfect for local testing)
    allow_credentials=True,
    allow_methods=["*"],  # Allows POST, GET, OPTIONS, etc.
    allow_headers=["*"],
)

class ClaimRequest(BaseModel):
    claim: str

@app.get("/")
async def health():
    return {"status": "online"}

@app.post("/verify")
async def verify_endpoint(request: ClaimRequest):
    if not request.claim:
        raise HTTPException(status_code=400, detail="Claim text is required")
    try:
        # Run the intelligence pipeline
        result = brain.verify_and_format(request.claim)
        return result
    except Exception as e:
        print(f"Pipeline Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)