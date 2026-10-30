# Powerbank

Udalerriko powerbank-en alokairu-sistema: kargaguneak kontsultatu, erreserbak egin
eta administrazioa kudeatzeko web-aplikazioa.

## Egitura

```
ERRONKA1/
├── backend/              FastAPI + SQLAlchemy 2.0 + PostgreSQL (API-a)
├── administrazio_atala/  Angular 22 (administrazio-atalean)
├── web-publikoa/         HTML + JS + Bootstrap 5.3 (herritarrentzat)
└── NOLA-ABIARAZI.md      hiru atalak martxan jartzeko gida
```

## Azkar abiarazteko

```bash
# API-a
cd ERRONKA1/backend && uv run uvicorn main:app --reload

# Administrazioa
cd ERRONKA1/administrazio_atala && npm ci && npm start

# Web publikoa
cd ERRONKA1/web-publikoa && python3 -m http.server 5500
```

Xehetasunak, datu-basearen prestaketa eta proba-kontuak: **[ERRONKA1/NOLA-ABIARAZI.md](ERRONKA1/NOLA-ABIARAZI.md)**.
