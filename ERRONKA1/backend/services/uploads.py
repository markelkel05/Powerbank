"""Kargaguneen irudiak zerbitzarian gordetzeko laguntzaileak."""

import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

# Irudiak backend/uploads karpetan gordeko dira eta /uploads/... bidez zerbitzatuko
UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

EXTENTSIO_ONARTUAK = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
GEHIENEZKO_TAMAINA = 5 * 1024 * 1024  # 5 MB


async def gorde_irudia(fitxategia: UploadFile) -> str:
    """Igotako fitxategia gorde eta zerbitzatzeko URL erlatiboa itzuli."""
    if not fitxategia.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Fitxategiaren izena falta da"
        )

    extentsioa = Path(fitxategia.filename).suffix.lower()
    if extentsioa not in EXTENTSIO_ONARTUAK:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Irudi formatua ez da onartzen (jpg, jpeg, png, webp edo gif).",
        )

    edukia = await fitxategia.read()
    if len(edukia) > GEHIENEZKO_TAMAINA:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="Irudia handiegia da (gehienez 5 MB).",
        )
    if not edukia:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Fitxategia hutsik dago"
        )

    izena = f"{uuid.uuid4().hex}{extentsioa}"
    (UPLOAD_DIR / izena).write_bytes(edukia)

    return f"/uploads/{izena}"
