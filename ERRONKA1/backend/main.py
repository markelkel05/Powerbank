from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from routers import routers

app = FastAPI(title="Powerbank Erreserba API")

app.include_router(routers.powerbank_router)

# Kargaguneen irudiak /uploads/... bidez zerbitzatzeko
UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

origins = [
    "http://localhost:4200",
    "http://127.0.0.1:4200",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["OSASUNA"])
def osasuna():
    """Zerbitzaria martxan dagoela egiaztatzeko."""
    return {"egoera": "ok", "mezua": "Powerbank API-a martxan dago"}
