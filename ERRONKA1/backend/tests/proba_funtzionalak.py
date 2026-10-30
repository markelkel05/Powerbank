"""Erreserba eta kargaguneen negozio-arauen proba automatikoa.

Exekutatzeko (sqlite erabiliz, ez du Postgres behar):

    cd ERRONKA1/backend
    DATABASE_URL="sqlite:///./_test.db" python tests/proba_funtzionalak.py
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DATABASE_URL", "sqlite:///./_test.db")

from database.database import Base, SessionLocal, engine  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from main import app  # noqa: E402
from models import models  # noqa: E402

Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)

BASE = "/alokaziosistema"
orain = datetime.now(timezone.utc).replace(microsecond=0)

with SessionLocal() as db:
    db.add_all([
        models.Rol(id_rol=1, rol_izena="Admin"),
        models.Rol(id_rol=2, rol_izena="Erabiltzaile"),
        models.Erabiltzaileak(
            id_erab=1, nan="11111111A", izena="Ane", abizenak="Adibide",
            email="ane@adibide.eus", pasahitza="123456", helbidea="Kale Nagusia 1", id_rol=2,
        ),
        models.Erabiltzaileak(
            id_erab=2, nan="22222222B", izena="Jon", abizenak="Beste",
            email="jon@adibide.eus", pasahitza="123456", helbidea="Kale Nagusia 2", id_rol=2,
        ),
        models.Takillak(id_takilla=1, izena="Plaza", helbidea="Plaza 1", egoera="erabilgarri"),
        models.Takillak(id_takilla=2, izena="Geltokia", helbidea="Geltoki 2", egoera="mantentze_lanetan"),
        models.Postuak(id_postu=1, id_takilla=1, egoera="hutsa"),
        models.Postuak(id_postu=2, id_takilla=1, egoera="hutsa"),
        models.Postuak(id_postu=3, id_takilla=2, egoera="hutsa"),
        models.Powerbank(id_power=1, id_postu=1, karga=100, id_takilla=1),
        models.Powerbank(id_power=2, id_postu=2, karga=80, id_takilla=1),
        models.Powerbank(id_power=3, id_postu=3, karga=50, id_takilla=2),
    ])
    db.commit()

client = TestClient(app)
emaitzak: list[tuple[bool, str]] = []


def egiaztatu(izena: str, baldintza: bool, xehetasuna: str = "") -> None:
    emaitzak.append((baldintza, izena))
    ikurra = "PASS" if baldintza else "FAIL"
    print(f"[{ikurra}] {izena} {xehetasuna}")


def iso(data: datetime) -> str:
    return data.isoformat()


# ---------------------------------------------------------------- kargaguneak
r = client.get(f"{BASE}/kargaguneak")
egiaztatu("GET /kargaguneak", r.status_code == 200 and len(r.json()) == 2, str(r.text[:120]))
egiaztatu(
    "kargaguneak kontagailuak",
    r.json()[0]["postuak_kopurua"] == 2 and r.json()[0]["powerbank_kopurua"] == 2,
    str(r.json()[0]),
)

r = client.post(f"{BASE}/kargaguneak/post", json={"izena": "Unibertsitatea", "helbidea": "Campus 3"})
egiaztatu("POST kargagune berria", r.status_code == 201 and r.json()["egoera"] == "erabilgarri", str(r.text[:200]))
kargagune_berria = r.json()["id_takilla"]

r = client.post(f"{BASE}/kargaguneak/{kargagune_berria}/irudiak", json={"url": "https://adibide.eus/irudia.png"})
egiaztatu("POST kargagune irudia", r.status_code == 201, str(r.text[:200]))

r = client.patch(f"{BASE}/kargaguneak/{kargagune_berria}/eguneratu", json={"izena": "Unibertsitatea (berria)"})
egiaztatu("PATCH kargagunea", r.status_code == 200 and r.json()["izena"].endswith("(berria)"), str(r.text[:200]))

r = client.post(f"{BASE}/postuak/post", json={"id_takilla": kargagune_berria, "egoera": "kargatzen"})
egiaztatu("POST karga-postua", r.status_code == 201, str(r.text[:200]))
postu_berria = r.json()["id_postu"]

r = client.patch(f"{BASE}/postuak/{postu_berria}/eguneratu", json={"egoera": "hutsa"})
egiaztatu("PATCH karga-postua", r.status_code == 200 and r.json()["egoera"] == "hutsa", str(r.text[:200]))

r = client.get(f"{BASE}/kargaguneak/1")
egiaztatu(
    "GET kargagune xehetasuna",
    r.status_code == 200 and [p["id_postu"] for p in r.json()["postuak"]] == [1, 2],
    str(r.text[:200]),
)

# ---------------------------------------------------------------- erreserbak
hasiera = orain + timedelta(days=1)
bukaera = hasiera + timedelta(hours=1, minutes=30)

erreserba = {
    "id_erab": 1,
    "id_power": 1,
    "erreserba_hasiera": iso(hasiera),
    "erreserba_bukaera": iso(bukaera),
    "id_hasiera_takilla": 1,
    "id_hasiera_postua": 1,
}

r = client.post(f"{BASE}/erreserbak/post", json=erreserba)
egiaztatu("POST erreserba baliozkoa", r.status_code == 201 and r.json()["egoera"] == "aktiboa", str(r.text[:250]))
lehen_erreserba = r.json().get("id_erreserba") if r.status_code == 201 else None

r = client.post(
    f"{BASE}/erreserbak/post",
    json={**erreserba, "id_power": 2, "erreserba_hasiera": iso(hasiera + timedelta(minutes=30)),
          "erreserba_bukaera": iso(bukaera + timedelta(minutes=30))},
)
egiaztatu("Araua 1: postu berean gainjartzea debekatuta (409)", r.status_code == 409, str(r.text[:200]))

r = client.post(
    f"{BASE}/erreserbak/post",
    json={**erreserba, "id_power": 2, "erreserba_hasiera": iso(bukaera),
          "erreserba_bukaera": iso(bukaera + timedelta(hours=1))},
)
egiaztatu("Araua 1: erreserba ukitzailea onartuta", r.status_code == 201, str(r.text[:250]))
bigarren_erreserba = r.json().get("id_erreserba") if r.status_code == 201 else None

r = client.post(
    f"{BASE}/erreserbak/post",
    json={**erreserba, "id_hasiera_postua": 2, "erreserba_hasiera": iso(hasiera),
          "erreserba_bukaera": iso(bukaera)},
)
egiaztatu("Powerbank bera bi erreserba gainjarritan debekatuta (409)", r.status_code == 409, str(r.text[:200]))

r = client.post(
    f"{BASE}/erreserbak/post",
    json={**erreserba, "id_hasiera_postua": 2,
          "erreserba_bukaera": iso(hasiera - timedelta(minutes=10))},
)
egiaztatu("Araua 2: hasiera ez da bukaera baino geroagokoa (400)", r.status_code == 400, str(r.text[:200]))

r = client.post(
    f"{BASE}/erreserbak/post",
    json={**erreserba, "id_hasiera_postua": 2, "id_power": 2,
          "erreserba_hasiera": iso(orain - timedelta(hours=2)),
          "erreserba_bukaera": iso(orain - timedelta(hours=1))},
)
egiaztatu("Araua 3: iraganeko erreserba debekatuta (400)", r.status_code == 400, str(r.text[:200]))

r = client.post(
    f"{BASE}/erreserbak/post",
    json={**erreserba, "id_power": 3, "id_hasiera_takilla": 2, "id_hasiera_postua": 3,
          "erreserba_hasiera": iso(hasiera), "erreserba_bukaera": iso(bukaera)},
)
egiaztatu("Araua 4: mantentze-lanetan dagoen kargagunea debekatuta (409)", r.status_code == 409, str(r.text[:200]))

r = client.post(
    f"{BASE}/erreserbak/post",
    json={**erreserba, "id_power": 3, "id_hasiera_postua": 2,
          "erreserba_hasiera": iso(hasiera + timedelta(days=2)),
          "erreserba_bukaera": iso(hasiera + timedelta(days=2, hours=1))},
)
egiaztatu("Powerbank-a beste kargagune batekoa: debekatuta (400)", r.status_code == 400, str(r.text[:200]))

r = client.post(
    f"{BASE}/erreserbak/post",
    json={**erreserba, "id_hasiera_takilla": 2, "id_hasiera_postua": 2,
          "erreserba_hasiera": iso(hasiera + timedelta(days=2)),
          "erreserba_bukaera": iso(hasiera + timedelta(days=2, hours=1))},
)
egiaztatu("Postua ez da adierazitako kargagunearena (400)", r.status_code == 400, str(r.text[:200]))

# ---------------------------------------------------------------- zerrenda eta iragazkiak
r = client.get(f"{BASE}/erreserbak/zerrenda")
egiaztatu("GET erreserbak/zerrenda", r.status_code == 200 and len(r.json()) == 2, str(r.text[:200]))
egiaztatu(
    "Zerrendak erabiltzailearen izena dakar",
    r.json()[0]["erabiltzaile_izena"] == "Ane Adibide",
    str(r.json()[0] if r.json() else ""),
)

r = client.get(f"{BASE}/erreserbak/zerrenda", params={"id_erab": 2})
egiaztatu("Iragazkia erabiltzailearen arabera", r.status_code == 200 and r.json() == [], str(r.text[:150]))

r = client.get(f"{BASE}/erreserbak/zerrenda", params={"id_takilla": 1, "egoera": "aktiboa"})
egiaztatu("Iragazkia kargagunearen eta egoeraren arabera", r.status_code == 200 and len(r.json()) == 2, str(r.text[:150]))

r = client.get(f"{BASE}/erreserbak/zerrenda", params={"hasiera": iso(hasiera + timedelta(days=3)),
                                                      "bukaera": iso(hasiera + timedelta(days=4))})
egiaztatu("Iragazkia dataren arabera", r.status_code == 200 and r.json() == [], str(r.text[:150]))

# ---------------------------------------------------------------- egoera-aldaketak
r = client.patch(f"{BASE}/erreserbak/{bigarren_erreserba}/ezeztatu", params={"id_erab": 2})
egiaztatu("Araua 5: beste erabiltzaile baten erreserba ezin da ezeztatu (403)", r.status_code == 403, str(r.text[:200]))

r = client.patch(f"{BASE}/erreserbak/{bigarren_erreserba}/ezeztatu", params={"id_erab": 1})
egiaztatu("Erreserba ezeztatzea", r.status_code == 200 and r.json()["egoera"] == "ezeztatuta", str(r.text[:200]))

r = client.post(
    f"{BASE}/erreserbak/post",
    json={**erreserba, "id_power": 2, "erreserba_hasiera": iso(bukaera),
          "erreserba_bukaera": iso(bukaera + timedelta(minutes=30))},
)
egiaztatu("Araua 7: ezeztatutako erreserbak ez du blokeatzen", r.status_code == 201, str(r.text[:250]))
hirugarren_erreserba = r.json().get("id_erreserba") if r.status_code == 201 else None

r = client.patch(f"{BASE}/erreserbak/{bigarren_erreserba}/ezeztatu", params={"admin": "true"})
egiaztatu("Ezeztatutako erreserba ezin da berriro ezeztatu (409)", r.status_code == 409, str(r.text[:200]))

r = client.patch(f"{BASE}/erreserbak/{bigarren_erreserba}/egoera", json={"egoera": "aktiboa"}, params={"admin": "true"})
egiaztatu("Berriro aktibatzean gainjartzea egiaztatzen da (409)", r.status_code == 409, str(r.text[:200]))

r = client.patch(f"{BASE}/erreserbak/{lehen_erreserba}/eguneratu",
                 json={"erreserba_bukaera": iso(hasiera + timedelta(hours=1))})
egiaztatu("Erreserba eguneratzea", r.status_code == 200, str(r.text[:200]))

r = client.patch(f"{BASE}/erreserbak/{lehen_erreserba}/eguneratu",
                 json={"erreserba_bukaera": iso(bukaera + timedelta(hours=2))})
egiaztatu("Eguneratzeak gainjartzea egiaztatzen du (409)", r.status_code == 409, str(r.text[:200]))

r = client.patch(f"{BASE}/erreserbak/{lehen_erreserba}/ezeztatu", params={"id_erab": 1})
r = client.patch(f"{BASE}/erreserbak/{lehen_erreserba}/eguneratu",
                 json={"erreserba_bukaera": iso(bukaera + timedelta(hours=3))})
egiaztatu("Ezeztatutako erreserba ezin da aldatu (409)", r.status_code == 409, str(r.text[:200]))

r = client.patch(f"{BASE}/erreserbak/{hirugarren_erreserba}/erabilera",
                 json={"erabilera_hasiera": iso(bukaera), "erabilera_bukaera": iso(bukaera + timedelta(minutes=40)),
                       "id_bukaera_postua": 2})
egiaztatu("Erabilera erregistratzea (amaituta)", r.status_code == 200 and r.json()["egoera"] == "amaituta", str(r.text[:250]))

# ---------------------------------------------------------------- ezabaketa/desaktibazioa
r = client.delete(f"{BASE}/kargaguneak/1/ezabatu")
egiaztatu("Araua 8: erlazioak dituen kargagunea ezin da ezabatu (409)", r.status_code == 409, str(r.text[:200]))

r = client.patch(f"{BASE}/kargaguneak/{kargagune_berria}/desaktibatu")
egiaztatu("Kargagunea desaktibatzea", r.status_code == 200 and r.json()["egoera"] == "zerbitzuz_kanpo", str(r.text[:200]))

r = client.delete(f"{BASE}/postuak/1/ezabatu")
egiaztatu("Powerbanka duen karga-postua ezin da ezabatu (409)", r.status_code == 409, str(r.text[:200]))

r = client.delete(f"{BASE}/postuak/{postu_berria}/ezabatu")
egiaztatu("Karga-postu hutsa ezabatzea", r.status_code == 200, str(r.text[:200]))

r = client.delete(f"{BASE}/kargaguneak/{kargagune_berria}/ezabatu")
egiaztatu("Kargagune hutsa ezabatzea", r.status_code == 200, str(r.text[:200]))

# ---------------------------------------------------------------- erabilgarritasuna
r = client.get(f"{BASE}/kargaguneak/1/erabilgarritasuna",
               params={"hasiera": iso(hasiera + timedelta(days=5)), "bukaera": iso(hasiera + timedelta(days=5, hours=1))})
egiaztatu("Erabilgarritasuna: postu guztiak libre", r.status_code == 200 and all(p["libre"] for p in r.json()["postuak"]), str(r.text[:200]))

# ---------------------------------------------------------------- gainerako endpointak
r = client.get(f"{BASE}/powerbanks")
egiaztatu("GET /powerbanks", r.status_code == 200 and len(r.json()) == 3, str(r.text[:200]))

r = client.get(f"{BASE}/erabiltzaileak")
egiaztatu("GET /erabiltzaileak (Urkoren endpointa)", r.status_code == 200 and len(r.json()) == 2, str(r.text[:200]))

r = client.get(f"{BASE}/erabiltzaileak/1/erreserbak")
egiaztatu("GET erabiltzailearen erreserbak", r.status_code == 200, str(r.text[:200]))

r = client.get(f"{BASE}/takillak/1/postIrudia")
r = client.post(f"{BASE}/takillak/1/postIrudia", json={"url": "https://adibide.eus/beste.png"})
egiaztatu("POST /takillak/{id}/postIrudia (Urkorena)", r.status_code == 201, str(r.text[:200]))

# ---------------------------------------------------------------- autentifikazioa
erregistroa = {
    "nan": "33333333C",
    "izena": "Maite",
    "abizenak": "Erregistro",
    "email": "maite@adibide.eus",
    "pasahitza": "sekretua123",
    "helbidea": "Kale Berria 3",
}

r = client.post(f"{BASE}/auth/erregistratu", json=erregistroa)
egiaztatu("POST /auth/erregistratu", r.status_code == 201 and r.json()["access_token"], str(r.text[:200]))
token_maite = r.json().get("access_token") if r.status_code == 201 else ""
id_maite = r.json().get("erabiltzailea", {}).get("id_erab") if r.status_code == 201 else None

r = client.post(f"{BASE}/auth/erregistratu", json=erregistroa)
egiaztatu("Erregistro bikoiztua ez da onartzen (409)", r.status_code == 409, str(r.text[:200]))

r = client.post(f"{BASE}/auth/login", json={"email": "maite@adibide.eus", "pasahitza": "sekretua123"})
egiaztatu("Login zuzena (pasahitz hasheaduna)", r.status_code == 200, str(r.text[:200]))

r = client.post(f"{BASE}/auth/login", json={"email": "maite@adibide.eus", "pasahitza": "oker"})
egiaztatu("Login okerra (401)", r.status_code == 401, str(r.text[:200]))

# Hasieran testu lauan zegoen pasahitza: login egitean hash bihurtzen da
r = client.post(f"{BASE}/auth/login", json={"email": "ane@adibide.eus", "pasahitza": "123456"})
egiaztatu("Testu lauko pasahitz zaharra onartzen da", r.status_code == 200, str(r.text[:200]))
token_ane = r.json().get("access_token") if r.status_code == 200 else ""
with SessionLocal() as db:
    gordea = db.get(models.Erabiltzaileak, 1).pasahitza
egiaztatu("Loginaren ondoren pasahitza hashatuta dago", gordea.startswith("$2"), gordea[:12])

r = client.get(f"{BASE}/auth/ni", headers={"Authorization": f"Bearer {token_ane}"})
egiaztatu("GET /auth/ni tokenarekin", r.status_code == 200 and r.json()["id_erab"] == 1, str(r.text[:150]))
egiaztatu(
    "Erantzun publikoan ez da pasahitzik agertzen",
    "pasahitza" not in r.json(),
    str(sorted(r.json().keys())),
)

r = client.get(f"{BASE}/auth/ni")
egiaztatu("GET /auth/ni tokenik gabe (401)", r.status_code == 401, str(r.text[:150]))

r = client.get(f"{BASE}/auth/ni", headers={"Authorization": "Bearer tokenfaltsua"})
egiaztatu("Token faltsua baztertzen da (401)", r.status_code == 401, str(r.text[:150]))

# Maiteren erreserba propioa
hasiera_maite = orain + timedelta(days=6)
r = client.post(
    f"{BASE}/erreserbak/post",
    headers={"Authorization": f"Bearer {token_maite}"},
    json={"id_erab": id_maite, "id_power": 1,
          "erreserba_hasiera": iso(hasiera_maite),
          "erreserba_bukaera": iso(hasiera_maite + timedelta(hours=1)),
          "id_hasiera_takilla": 1, "id_hasiera_postua": 1},
)
egiaztatu("Erreserba tokenarekin (norberaren izenean)", r.status_code == 201, str(r.text[:200]))
erreserba_maite = r.json().get("id_erreserba") if r.status_code == 201 else None

r = client.post(
    f"{BASE}/erreserbak/post",
    headers={"Authorization": f"Bearer {token_maite}"},
    json={"id_erab": 1, "id_power": 1,
          "erreserba_hasiera": iso(hasiera_maite + timedelta(days=1)),
          "erreserba_bukaera": iso(hasiera_maite + timedelta(days=1, hours=1)),
          "id_hasiera_takilla": 1, "id_hasiera_postua": 1},
)
egiaztatu("Beste baten izenean erreserbatzea debekatuta (403)", r.status_code == 403, str(r.text[:200]))

r = client.get(f"{BASE}/erreserbak/nireak", headers={"Authorization": f"Bearer {token_maite}"})
egiaztatu(
    "GET /erreserbak/nireak erreserba propioak soilik",
    r.status_code == 200 and all(e["id_erab"] == id_maite for e in r.json()),
    str(r.text[:200]),
)

r = client.get(f"{BASE}/erreserbak/nireak")
egiaztatu("GET /erreserbak/nireak tokenik gabe (401)", r.status_code == 401, str(r.text[:150]))

r = client.patch(
    f"{BASE}/erreserbak/{erreserba_maite}/ezeztatu",
    headers={"Authorization": f"Bearer {token_ane}"},
)
egiaztatu("Beste baten erreserba ezeztatzea debekatuta (403)", r.status_code == 403, str(r.text[:200]))

r = client.patch(
    f"{BASE}/erreserbak/{erreserba_maite}/ezeztatu",
    headers={"Authorization": f"Bearer {token_maite}"},
)
egiaztatu("Norberaren erreserba ezeztatzea tokenarekin", r.status_code == 200 and r.json()["egoera"] == "ezeztatuta", str(r.text[:200]))

r = client.patch(
    f"{BASE}/erabiltzaileak/1/eguneratu",
    headers={"Authorization": f"Bearer {token_maite}"},
    json={"izena": "Lapur"},
)
egiaztatu("Beste baten datuak aldatzea debekatuta (403)", r.status_code == 403, str(r.text[:200]))

r = client.patch(
    f"{BASE}/erabiltzaileak/{id_maite}/eguneratu",
    headers={"Authorization": f"Bearer {token_maite}"},
    json={"helbidea": "Helbide berria 9"},
)
egiaztatu("Norberaren datuak aldatzea baimenduta", r.status_code == 200 and r.json()["helbidea"] == "Helbide berria 9", str(r.text[:200]))

with SessionLocal() as db:
    db.get(models.Erabiltzaileak, 2).activo = False
    db.commit()
r = client.post(f"{BASE}/auth/login", json={"email": "jon@adibide.eus", "pasahitza": "123456"})
egiaztatu("Erabiltzaile desaktibatuaren login-a debekatuta (403)", r.status_code == 403, str(r.text[:200]))

# ------------------------------- datu zaharrak: zerrendak ez dira apurtu behar
# Markelen dump zaharrean (Markel.sql) erabiltzaile bat "string" balioekin
# zegoen eta nan/email luzerak ez zituen betetzen. Erantzun-eskemek zorrotzak
# izanda, zerrenda osoa 500 errorearekin erortzen zen. Proba honek hori
# gertatzen ez dela bermatzen du.
with SessionLocal() as db:
    db.add(
        models.Erabiltzaileak(
            nan="string", izena="string", abizenak="string",
            email="string", pasahitza="string", helbidea="string", id_rol=1,
        )
    )
    db.add(models.Takillak(izena="X", helbidea="ab", egoera="zerbitzuz_kanpo"))
    db.commit()

r = client.get(f"{BASE}/erabiltzaileak")
egiaztatu(
    "Dump zaharretako erabiltzaileak ez du zerrenda apurtzen",
    r.status_code == 200 and any(e["email"] == "string" for e in r.json()),
    str(r.text[:200]),
)

r = client.get(f"{BASE}/kargaguneak")
egiaztatu(
    "Kargagune izen laburrak ez du zerrenda apurtzen",
    r.status_code == 200 and any(k["izena"] == "X" for k in r.json()),
    str(r.text[:200]),
)

# ---------------------------------------------------------------- laburpena
guztira = len(emaitzak)
ondo = sum(1 for emaitza, _ in emaitzak if emaitza)
print(f"\n{ondo}/{guztira} proba ondo pasa dira")
if ondo != guztira:
    print("HUTS EGIN DUTEN PROBAK:")
    for emaitza, izena in emaitzak:
        if not emaitza:
            print(" -", izena)
    sys.exit(1)
