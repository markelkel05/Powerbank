# Powerbank — Backend (FastAPI + SQLAlchemy 2.0)

Kargaguneen, karga-postuen, powerbanken eta erreserben API-a.
Datu-basea PostgreSQL da eta eredua Urkoren dump-aren (`powerbank_erreserba.sql`)
arabera egokituta dago.

## Nola abiarazi

```bash
cd ERRONKA1/backend

# 1) Datu-basea sortu (Drive-ko Erronka1 karpetako powerbank_erreserba.sql dump-a)
createdb powerbank_erreserba
psql -U postgres -d powerbank_erreserba -f powerbank_erreserba.sql

# 2) Rolak eta proba-datuak sartu (beharrezkoa da gutxienez rolak)
psql -U postgres -d powerbank_erreserba -f database/seed.sql

# 3) Ingurune birtuala eta menpekotasunak
uv sync            # edo: python -m venv .venv && pip install -e .

# 4) Zerbitzaria
uv run uvicorn main:app --reload
```

- API-a: <http://localhost:8000>
- Dokumentazio automatikoa: <http://localhost:8000/docs>
- Kargaguneen irudiak: `http://localhost:8000/uploads/<fitxategia>`

Konexio-katea `DATABASE_URL` ingurune-aldagaiarekin alda daiteke (adibidez probetarako):

```bash
DATABASE_URL="postgresql://erabiltzailea:pasahitza@localhost:5432/powerbank_erreserba" \
  uvicorn main:app --reload
```

## Egitura

```
backend/
├── main.py               # FastAPI aplikazioa, CORS eta /uploads
├── database/             # engine, SessionLocal, seed.sql
├── models/models.py      # SQLAlchemy 2.0 modeloak (Mapped / mapped_column)
├── schemas/schemas.py    # Pydantic eskema guztiak
├── routers/routers.py    # endpoint-ak (coderik gabe: dena services-era deitzen du)
├── services/
│   ├── services.py       # negozio-logika osoa
│   ├── auth.py           # pasahitzen hasheoa (bcrypt)
│   └── uploads.py        # irudien igoera
└── tests/
    └── proba_funtzionalak.py   # negozio-arauen proba automatikoa (sqlite-rekin)
```

## Endpoint nagusiak

### Kargaguneak (takillak)

| Metodoa | Bidea | Azalpena |
| --- | --- | --- |
| GET | `/alokaziosistema/kargaguneak?bilaketa=&egoera=` | Zerrenda iragazkiekin |
| GET | `/alokaziosistema/kargaguneak/{id}?hasiera=&bukaera=` | Xehetasunak + postuen erabilgarritasuna |
| GET | `/alokaziosistema/kargaguneak/{id}/erabilgarritasuna?hasiera=&bukaera=` | Tarte batean zein postu dauden libre |
| POST | `/alokaziosistema/kargaguneak/post` | Kargagune berria |
| PATCH | `/alokaziosistema/kargaguneak/{id}/eguneratu` | Datuak aldatu |
| PATCH | `/alokaziosistema/kargaguneak/{id}/desaktibatu` | Zerbitzuz kanpo utzi |
| DELETE | `/alokaziosistema/kargaguneak/{id}/ezabatu` | Ezabatu (erlazioak baditu → 409) |
| POST | `/alokaziosistema/kargaguneak/{id}/irudiak` | Irudia URL bidez gehitu |
| POST | `/alokaziosistema/kargaguneak/{id}/irudiak/igo` | Irudia fitxategi gisa igo (multipart) |
| PATCH | `/alokaziosistema/kargaguneak/{id}/irudiak/{id_irudi}` | Irudi baten URLa aldatu |
| DELETE | `/alokaziosistema/kargaguneak/{id}/irudiak/{id_irudi}` | Irudia ezabatu |

### Karga-postuak (postuak)

`GET /postuak`, `POST /postuak/post`, `PATCH /postuak/{id}/eguneratu`,
`DELETE /postuak/{id}/ezabatu`.

### Erreserbak

| Metodoa | Bidea | Azalpena |
| --- | --- | --- |
| GET | `/alokaziosistema/erreserbak/zerrenda?id_erab=&id_takilla=&id_power=&hasiera=&bukaera=&egoera=` | Administrazio-taulako zerrenda (izenekin) |
| GET | `/alokaziosistema/erreserbak` | Zerrenda soila |
| GET | `/alokaziosistema/erreserbak/{id}` | Erreserba bat |
| POST | `/alokaziosistema/erreserbak/post` | Erreserba berria (arau guztiak egiaztatuta) |
| PATCH | `/alokaziosistema/erreserbak/{id}/eguneratu` | Data/postua aldatu (arauak berriz egiaztatuta) |
| PATCH | `/alokaziosistema/erreserbak/{id}/ezeztatu?id_erab=&admin=` | Ezeztatu |
| PATCH | `/alokaziosistema/erreserbak/{id}/egoera` | Egoera aldatu (aktiboa/ezeztatuta/amaituta) |
| PATCH | `/alokaziosistema/erreserbak/{id}/erabilera` | Powerbank-a hartu/bueltatu markatu |

## Negozio-arauak (zerbitzarian)

1. Karga-postu berean ezin dira denboran gainjartzen diren erreserba aktiboak egon
   (ukitzen direnak onartuta: 10:00–11:30 eta 11:30–12:00).
2. Hasiera-data amaiera-data baino lehenagokoa izan behar da.
3. Ezin da iraganeko datarako erreserbarik egin.
4. Mantentze-lanetan edo zerbitzuz kanpo dauden kargaguneak ezin dira erreserbatu.
5. Erabiltzaileek beren erreserbak bakarrik alda ditzakete (`id_erab` parametroa).
6. Administratzaileek edozein erreserba kudeatu dezakete (`admin=true`).
7. Ezeztatutako erreserbak ez du karga-postua blokeatzen.
8. Erreserbak edo postuak dauzkaten kargaguneak ezin dira ezabatu: desaktibatu.
9. Powerbank berak ezin du bi erreserba aktibo gainjarri.

Era berean egiaztatzen da karga-postua adierazitako kargagunearena dela, eta
powerbank-a kargagune horretakoa dela.

## Probak

```bash
cd ERRONKA1/backend
DATABASE_URL="sqlite:///./_test.db" python tests/proba_funtzionalak.py
```

41 egiaztapen: CRUD-a, erreserben arau guztiak, iragazkiak, ezabaketa/desaktibazioa
eta erabilgarritasuna.

## Ezagutzekoak / hurrengo pausoak

- **Autentifikazioa**: `services/auth.py` prestatuta dago (bcrypt), baina oraindik ez
  dago login/JWT endpoint-ik. Bitartean, baimenak `id_erab` / `admin` parametroen
  bidez egiaztatzen dira. Benetako segurtasunerako token bidezko saioa falta da, eta
  datu-baseko pasahitzak hash bihurtu behar dira.
- **Powerbanken kudeaketa osoa**: Urkoren atala da; hemen irakurketa (`GET /powerbanks`)
  eta sorkuntza soilik gehitu dira, erreserba-formularioak behar duelako.
- **Atal publikoa (JS + Bootstrap)**: oraindik ez da egin (Ikerren atala).
- Endpoint zaharrak ez dira ezabatu: `/takillak/*` eta `/erabiltzaileak/*` mantentzen
  dira, eta aldamenean `/kargaguneak/*` berriak daude.
