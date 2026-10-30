# Nola abiarazi proiektua (backend + administrazioa + web publikoa)

Gida hau hiru atalak martxan jartzeko da: **FastAPI backend-a**, **Angular
administrazio-atala** eta **web publikoa (JS + Bootstrap)**.

```
Powerbank/
└── ERRONKA1/
    ├── backend/              → FastAPI + SQLAlchemy (API-a)
    ├── administrazio_atala/  → Angular 22 (administrazioa)
    ├── web-publikoa/         → HTML + JS + Bootstrap 5.3 (herritarrentzat)
    └── NOLA-ABIARAZI.md      → fitxategi hau
```

---

## 0. Behar dena

| Tresna | Bertsioa | Oharra |
| --- | --- | --- |
| Python | 3.14 (edo ≥ 3.11) | proiektuak `>=3.14` eskatzen du `pyproject.toml`-ean |
| uv | edozein | `pip install uv` (edo erabili venv + pip) |
| Node.js | 22.x | Angular 22rako |
| PostgreSQL | 16+ | datu-basea |

---

## 1. Datu-basea prestatu

```bash
# Datu-basea sortu
createdb powerbank_erreserba
```

Urkok Drive-ko **Erronka1** karpetan utzitako `powerbank_erreserba.sql` dump-a inportatu:

```bash
psql -U postgres -d powerbank_erreserba -f powerbank_erreserba.sql
```

> ⚠️ Dump-a PostgreSQL 18rekin egin zen eta lehen lerroetan `\restrict` /
> `\unrestrict` aginduak ditu. Zure `psql` zaharragoa bada, agindu horiek kendu
> beharko dituzu (`invalid command \restrict` errorea ematen badu).

Gero rolak eta proba-datuak sartu (`seed.sql`, fitxategia `backend/database/`-n dago):

```bash
cd backend
psql -U postgres -d powerbank_erreserba -f database/seed.sql
```

`seed.sql` exekutatu daiteke hainbat aldiz: ez ditu erregistroak bikoizten.
Rolak derrigorrezkoak dira (`erabiltzaileak.id_rol` → `rolak` FK).

### 1.1. Markelen `Markel.sql` dump-a erabiltzen baduzu

Drive-ko `Markel.sql` fitxategiak **bi berezitasun** ditu, eta biek erroreak
eragiten dituzte lehenengoan:

**a) pg_dump-en formatu bitarra da (`PGDMP`), ez SQL testua.**
`psql -f Markel.sql` eginez gero `input is a PostgreSQL custom-format dump`
errorea ematen du. Horrela inportatu behar da:

```bash
pg_restore -U postgres -d powerbank_erreserba Markel.sql
# edo, SQL garbia nahi baduzu:
pg_restore -U postgres -f markel.sql Markel.sql && psql -U postgres -d powerbank_erreserba -f markel.sql
```

> Dumpa PostgreSQL **18.6**-rekin sortu zen (artxibo-formatu 1.16). `pg_restore`
> zaharrak `unsupported version (1.16) in file header` errorea emango du:
> erabili PostgreSQL 18ko `pg_restore`, edo eskatu dumpa SQL formatu hutsean
> (`pg_dump -Fp`).

**b) Eskema zaharra dauka (DATU BASEA.docx-ena), ez gaur egungo kodea erabiltzen duena.**
Horregatik API-ak 500 erroreak ematen ditu: `column "activo" ... does not exist`,
`relation "takillak_irudiak" does not exist`, `column "id_takilla" of relation
"powerbank" does not exist`, eta `invalid input value for enum egoera_takillak:
"mantentze_lanetan"`. Sintoma nagusia: **login-a eta erabiltzaileen zerrenda ez
dabiltza**, eta kargaguneak ezin dira egoeraz iragazi.

Konponbidea: migrazio-fitxategia exekutatu (datuak ez dira galtzen, irudiak beste
taula batera mugitzen dira):

```bash
pg_dump -U postgres -Fc -f babeskopia.dump powerbank_erreserba     # babeskopia
psql -U postgres -d powerbank_erreserba -f database/markel_eguneratu.sql
```

Migrazioak hau egiten du: `erabiltzaileak.activo` gehitzen du, `egoera_takillak`
enumaren balioak azpimarrarekin berrizendatzen ditu, `takillak.irudia` →
`takillak_irudiak` taulara mugitzen da, eta `powerbank.id_takilla` gehitzen du
(postutik abiatuta betetzen da). Behin baino gehiagotan exekuta daiteke.

> Oharra: dump horretan erabiltzaile bakarra dago, eta haren datuak placeholders
> dira (`nan = 'string'`, `email = 'string'`). Ez du pasahitz ezagunik, beraz
> proba-kontu bat sortu `seed.sql`-ekin edo `/auth/erregistratu` erabiliz.

---

## 2. Backend-a (FastAPI)

```bash
cd ERRONKA1/backend

# 2.1 Menpekotasunak
uv sync                       # uv-rekin
# edo: python -m venv .venv && source .venv/bin/activate && pip install -e .

# 2.2 Zerbitzaria
uv run uvicorn main:app --reload
```

- API-a: <http://localhost:8000>
- Swagger dokumentazioa: <http://localhost:8000/docs>
- Kargaguneen irudiak: `http://localhost:8000/uploads/<fitxategia>`

### Ingurune-aldagaiak (aukerakoak, baina gomendagarriak)

```bash
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/powerbank_erreserba"
export SECRET_KEY="zure-giltza-sekretua"
uv run uvicorn main:app --reload
```

- `DATABASE_URL`: datu-basearen konexioa (`database/database.py`).
- `SECRET_KEY`: saio-tokenak sinatzeko giltza (ez jarri kodean ekoizpenean).

### Proba funtzionalak (Postgres beharrik ez)

```bash
cd ERRONKA1/backend
DATABASE_URL="sqlite:///./_test.db" python tests/proba_funtzionalak.py
```

60 egiaztapen: CRUD-a, erreserben negozio-arau guztiak, iragazkiak, autentifikazioa
eta baimenak.

---

## 3. Administrazio-atala (Angular)

```bash
cd ERRONKA1/administrazio_atala
npm ci            # lehen aldian
npm start         # ng serve
```

- Administrazioa: <http://localhost:4200>
- Orriak: **Erabiltzaileak** (`/erabiltzaileZerrenda`), **Kargaguneak**
  (`/kargaguneak`) eta **Erreserbak** (`/erreserbak`).

API-aren helbidea bi fitxategitan dago:

- `src/app/api/powerbank-api.ts` → `API_OINARRIA`
- `src/app/erabiltzaileak-component/api-deiak.ts` → URLak

Backend-a `localhost:8000`-n badago, ez duzu ezer aldatu behar. CORS-ak
`localhost:4200` eta `localhost:5500` onartzen ditu (`backend/main.py`).

---

## 4. Web publikoa (JS + Bootstrap 5.3)

Ezin da `index.html` zuzenean ireki (`file://`): JS moduluek eta `fetch`-ek
zerbitzari bat behar dute. Aukerak:

```bash
cd ERRONKA1/web-publikoa
python3 -m http.server 5500
```

- Web publikoa: <http://localhost:5500>
- VS Code erabiltzen baduzu: *Live Server* luzapena ere balio du (5500 portua).

API-aren helbidea `js/api.js` fitxategian dago (`API_OINARRIA`).

> CORS: `backend/main.py`-ko `origins` zerrendan `http://localhost:5500` eta
> `http://127.0.0.1:5500` daude. Beste portu bat erabiltzen baduzu, gehitu.

---

## 5. Proba-kontuak

Dump-ak baditu erabiltzaileak. Pasahitzak testu lauan daude hasieran, baina
**lehen login-a egitean automatikoki hash bihurtzen dira** (bcrypt).

| Rola | Emaila | Pasahitza |
| --- | --- | --- |
| Administratzailea | `post@post.com` | `postpass` |
| Erabiltzailea | `ikumendibe25@lhusurbil.eus` | `123456` |
| Erabiltzailea (seed) | `ane@adibide.eus` | `123456` |

Web publikotik kontu berria ere sor dezakezu (*Kontua sortu*): rol arrunta ematen
zaio automatikoki.

---

## 6. Guztia batera (3 terminal)

```bash
# 1. terminala → API-a
cd ERRONKA1/backend && uv run uvicorn main:app --reload

# 2. terminala → administrazioa
cd ERRONKA1/administrazio_atala && npm start

# 3. terminala → web publikoa
cd ERRONKA1/web-publikoa && python3 -m http.server 5500
```

---

## 7. Arazo arruntak

| Arazoa | Konponbidea |
| --- | --- |
| `500` erabiltzailea edo erreserba sortzean | `rolak` taula hutsik dago → exekutatu `database/seed.sql` |
| `500` login egitean edo erabiltzaileen zerrendan | eskema zaharra (`Markel.sql`): exekutatu `database/markel_eguneratu.sql` |
| `column "activo" ... does not exist` | dump zaharra: `database/markel_eguneratu.sql` |
| `relation "takillak_irudiak" does not exist` | dump zaharra: `database/markel_eguneratu.sql` |
| `invalid input value for enum egoera_takillak` | dump zaharra: `database/markel_eguneratu.sql` |
| `input is a PostgreSQL custom-format dump` | `Markel.sql` ez da SQL testua: `pg_restore -d ... Markel.sql` |
| `invalid command \restrict` dump-a inportatzean | kendu `\restrict`/`\unrestrict` lerroak edo erabili `psql` berria |
| Web publikotik `Failed to fetch` | backend itzalita, edo portua ez dago CORS zerrendan |
| `401 Saioa iraungi da` | tokena 8 ordukoa da: hasi saioa berriro |
| Angularrak `Node.js version` errorea | Node 22.x erabili (`node -v`) |
| `address already in use` | portua okupatuta: `lsof -i :8000` eta prozesua itxi |
| Irudia igotzean `413` | gehienez 5 MB eta jpg/png/webp/gif |

---

## 8. Argi izan beharrekoak

- **Pasahitzak**: erabiltzaileak sortzean/aldatzean zerbitzariak hash egiten ditu
  (bcrypt). Oraindik testu lauan dauden erregistro zaharrak login egitean
  migratzen dira automatikoki.
- **Tokenak**: `Authorization: Bearer <token>` goiburua erabiltzen da. Endpoint
  zaharrek ez dute tokenik behar (bateragarritasuna), baina tokena badator
  nortasuna eta baimenak tokenetik hartzen dira.
- **Dokumentazio teknikoa**: entrega egiteko PDFa taldeak berak idatzi behar du
  (erronkaren oharra: ez da IA bidez sortutako dokumentazioa onartzen).
