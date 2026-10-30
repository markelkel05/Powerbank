# Web publikoa (HTML + JS + Bootstrap 5.3)

Herritar eta bisitarientzako atala: kargaguneak kontsultatu, kontua sortu eta
powerbank-ak erreserbatu. Angular administrazio-ataletik bereizita dago, eta ez
du eraikuntza-prozesurik behar (HTML, CSS eta JS hutsa).

## Nola abiarazi

```bash
cd ERRONKA1/web-publikoa
python3 -m http.server 5500
```

→ <http://localhost:5500>

Backend-a martxan egon behar da (<http://localhost:8000>). Helbidea `js/api.js`
fitxategiko `API_OINARRIA` konstantean alda daiteke.

## Orriak

| Fitxategia | Edukia |
| --- | --- |
| `index.html` | Kargaguneen zerrenda, bilaketa, xehetasunak (irudiak, postuak, erabilgarritasuna) |
| `erreserbak.html` | Erreserba berriaren formularioa + norberaren erreserbak (ezeztatu) |
| `kontua.html` | Saioa hasi, kontua sortu, norberaren datuak aldatu |

## Egitura

```
web-publikoa/
├── index.html
├── erreserbak.html
├── kontua.html
├── css/estiloak.css
└── js/
    ├── api.js          # API deialdiak, tokenaren kudeaketa, formatuak
    ├── nabigazioa.js   # goiburua eta mezuak
    ├── index.js        # kargaguneen zerrenda eta xehetasunak
    ├── erreserbak.js   # erreserbak
    └── kontua.js       # saioa / erregistroa / profila
```

## Erabiltzen diren endpoint-ak

| Funtzioa | Endpoint-a |
| --- | --- |
| Kargaguneen zerrenda | `GET /alokaziosistema/kargaguneak` |
| Xehetasunak + postuak | `GET /alokaziosistema/kargaguneak/{id}` |
| Tarte baterako erabilgarritasuna | `GET /alokaziosistema/kargaguneak/{id}/erabilgarritasuna` |
| Powerbank-ak (kargagunearen arabera) | `GET /alokaziosistema/powerbanks?id_takilla=` |
| Saioa hasi | `POST /alokaziosistema/auth/login` |
| Erregistratu | `POST /alokaziosistema/auth/erregistratu` |
| Nire datuak | `GET /alokaziosistema/auth/ni` |
| Datuen aldaketa | `PATCH /alokaziosistema/erabiltzaileak/{id}/eguneratu` |
| Erreserba berria | `POST /alokaziosistema/erreserbak/post` |
| Nire erreserbak | `GET /alokaziosistema/erreserbak/nireak` |
| Erreserba ezeztatu | `PATCH /alokaziosistema/erreserbak/{id}/ezeztatu` |

## Saioa eta tokenak

- Saioa hastean, backend-ak token bat itzultzen du (`access_token`).
- Tokena `localStorage`-ean gordetzen da (`kargagunea_tokena`) eta
  `Authorization: Bearer <tokena>` goiburuan bidaltzen da.
- Tokena 8 ordutan iraungitzen da; orduan saioa berriro hasi behar da.
- `kontua.html?next=erreserbak.html` erabil daiteke saioa hasi ondoren norabidea
  gordetzeko.

## Zer dago eginda eta zer ez

**Eginda**
- Kargaguneen zerrenda, bilaketa eta egoeraren araberako iragazkia.
- Kargagune bakoitzaren xehetasunak: irudiak (miniaturekin), postuen egoera eta
  powerbank-aren karga.
- Tarte jakin baterako erabilgarritasunaren egiaztapena.
- Erregistroa, saioa hasi/amaitu, datuak aldatu.
- Erreserba berria egitea eta etorkizuneko erreserbak ezeztatzea.
- Diseinu responsiboa (mugikorrean ere ondo ikusten da).

**Gerokoak (2. fasea)**
- Kargaguneen mapa interaktiboa (Leaflet + OpenStreetMap).
- Udalerri anitzeko hautatzailea.
- Erreserbaren QR irakurketa (takilaren irekiera).

## Lizentziak

- **Bootstrap 5.3** — MIT lizentzia (<https://getbootstrap.com>), CDN bidez kargatua.
- **Bootstrap Icons 1.11** — MIT lizentzia (<https://icons.getbootstrap.com>).
- Irudiak: kargaguneen argazkiak datu-basetik datoz (`/uploads/...` edo kanpoko URL).
  Kanpoko irudirik erabiltzen bada, haien lizentzia eta jatorria egiaztatu behar dira.
