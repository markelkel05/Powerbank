"""Pasahitzen hasheoa eta saioa hasteko tokenak.

Oharra: tokenak JWT itxurakoak dira (header.payload.signature) baina
kanpo-libururik gabe sinatzen dira (HMAC-SHA256 stdlib-ekin), proiektuan
menpekotasun gehigarririk ez sartzeko.
"""

import base64
import hashlib
import hmac
import json
import os
import time

from fastapi import HTTPException, status
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# EKOIZPENEAN aldatu behar da: SECRET_KEY ingurune-aldagaia erabili
SECRET_KEY = os.getenv("SECRET_KEY", "garapenerako-giltza-aldatu-ekoizpenean")
TOKEN_BIZITZA_SEGUNDOAK = 8 * 60 * 60  # 8 ordu


# ---------------------------------------------------------------------------
# PASAHITZAK
# ---------------------------------------------------------------------------


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def pasahitza_hash_a_da(pasahitza: str) -> bool:
    """bcrypt hash bat den ala testu laua den bereizteko."""
    return bool(pasahitza) and pasahitza.startswith(("$2a$", "$2b$", "$2y$"))


def prestatu_pasahitza(pasahitza: str) -> str:
    """Pasahitza beti hash gisa gordetzeko (dagoeneko hasha bada, ez du ukitzen)."""
    return pasahitza if pasahitza_hash_a_da(pasahitza) else get_password_hash(pasahitza)


def pasahitza_egiaztatu(sarrera: str, gordea: str) -> bool:
    """Hash-a zein oraindik testu lauan dagoen pasahitza onartzen ditu."""
    if pasahitza_hash_a_da(gordea):
        return verify_password(sarrera, gordea)
    return hmac.compare_digest(sarrera, gordea)


# ---------------------------------------------------------------------------
# TOKENAK
# ---------------------------------------------------------------------------


def _b64(edukia: bytes) -> str:
    return base64.urlsafe_b64encode(edukia).rstrip(b"=").decode()


def _b64_ireki(edukia: str) -> bytes:
    return base64.urlsafe_b64decode(edukia + "=" * (-len(edukia) % 4))


def _sinatu(mezua: str) -> str:
    return _b64(
        hmac.new(SECRET_KEY.encode(), mezua.encode(), hashlib.sha256).digest()
    )


def sortu_tokena(id_erab: int) -> str:
    header = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = _b64(
        json.dumps(
            {"sub": id_erab, "exp": int(time.time()) + TOKEN_BIZITZA_SEGUNDOAK}
        ).encode()
    )
    mezua = f"{header}.{payload}"
    return f"{mezua}.{_sinatu(mezua)}"


def irakurri_tokena(token: str) -> int:
    """Tokena egiaztatu eta erabiltzailearen id-a itzuli."""
    try:
        header, payload, sinadura = token.split(".")
    except ValueError as e:
        raise _token_errorea() from e

    if not hmac.compare_digest(_sinatu(f"{header}.{payload}"), sinadura):
        raise _token_errorea()

    try:
        datuak = json.loads(_b64_ireki(payload))
    except (ValueError, json.JSONDecodeError) as e:
        raise _token_errorea() from e

    if int(datuak.get("exp", 0)) < int(time.time()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Saioa iraungi da. Hasi saioa berriro.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return int(datuak["sub"])


def _token_errorea() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Tokena ez da baliozkoa.",
        headers={"WWW-Authenticate": "Bearer"},
    )
