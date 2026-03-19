from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import alerts, digest, checklist

app = FastAPI(
    title="Community Guardian API",
    description="AI-powered community safety and digital wellness platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts"])
app.include_router(digest.router, prefix="/api/digest", tags=["Digest"])
app.include_router(checklist.router, prefix="/api/checklist", tags=["Checklist"])

@app.get("/")
def root():
    return {"message": "Community Guardian API is running", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "healthy"}
