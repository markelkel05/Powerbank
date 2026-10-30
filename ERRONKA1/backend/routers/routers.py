from typing import Annotated

from database import database
from fastapi import APIRouter, Depends, HTTPException, status
from models import models
from schemas import schemas
from services import services
from sqlalchemy.orm import Session

DbSession = Annotated[Session, Depends(database.get_session)]


powerbank_router = APIRouter(prefix="/alokaziosistema", tags=["POWERBANKS"])

################# GET ENDPOINTAK #################

# Erabiltzaile guztiak lortu
@powerbank_router.get("/erabiltzaileak", status_code=200, response_model=list[schemas.ListErabiltzaileak])
def get_all_participants(session: DbSession):
    return services.get_all_erabiltzaileak(session)


# Erabiltzaile bakarra lortu id bitartez
@powerbank_router.get("/erabiltzaileak/{id}", status_code=200, response_model=schemas.ListErabiltzaileak)
def get_by_id(id: int, session: DbSession):
    return services.get_erabiltzaile_id(id, session)


# Powerbank guztiak lortu
@powerbank_router.get("/powerbanks", response_model=list[schemas.ErreserbaResponse])
def read_powerbanks(session: DbSession):
    return services.list_erreserbak(session)


# Erabiltzaile baten erreserba guztiak lortu
@powerbank_router.get("/erabiltzaileak/{id}/erreserbak", status_code=200, response_model=list[schemas.ListErreserbak])
def get_erreserbak_erabiltzaile(id: int, session: DbSession):
    return services.list_erabiltzaile_erreserba(session, id)


@powerbank_router.get("/erreserbak", status_code=status.HTTP_200_OK, response_model=list[schemas.ErreserbaResponse])
def get_erreserbak(session: DbSession):
    return services.list_erreserbak(session)


################# POST ENDPOINTAK #################

@powerbank_router.post("/erabiltzaileak/post", status_code=201, response_model=schemas.ListErabiltzaileak)
def create_erabiltzaile(session: DbSession, erabiltzaile: schemas.CreateErabiltzaile):
    return services.post_erabiltzaile(session, erabiltzaile)


@powerbank_router.post("/takillak/post", status_code=201, response_model=schemas.TakillaResponse)
def post_takilla(session: DbSession, takilla: schemas.CreateTakilla):
    return services.create_takilla(session, takilla)


@powerbank_router.post("/takillak/{id}/postIrudia", status_code=201, response_model=schemas.TakillaIrudiaCreate)
def post_irudia(session: DbSession, id: int, irudia: schemas.TakillaIrudiaCreate):
    return services.post_irudia(session, id, irudia)


@powerbank_router.post("/powerbanks/post", status_code=201, response_model=schemas.CreatePowerbank)
def create_powerbank(session: DbSession, powerbank: schemas.CreatePowerbank):
    return services.create_powerbank(session, powerbank)

################# PATCH ENDPOINTAK #################

@powerbank_router.patch("/erabiltzaileak/{id}/eguneratu", status_code=200, response_model=schemas.ListErabiltzaileak)
def update_erabiltzaile(id: int, erabiltzaile: schemas.PatchErabiltzaile, session: DbSession):
    return services.patch_erabiltzailea(session, id, erabiltzaile)


@powerbank_router.patch("/erabiltzaileak/{id}/rola", status_code=200, response_model=schemas.ListErabiltzaileak)
def update_rola(id: int, rola: int, session: DbSession):
    return services.update_rola(session, id, rola)

@powerbank_router.patch("/takillak/{id}/eguneratu", status_code=200, response_model=schemas.TakillaResponse)
def update_takilla(id: int, takilla: schemas.PatchTakilla, session: DbSession):
    return services.patch_takilla(session, id, takilla)


@powerbank_router.patch("/takillak/{id}/aldatuIrudia", status_code=200, response_model=schemas.TakillaIrudiaCreate)
def pathc_irudia(session: DbSession, id: int, irudia: schemas.TakillaIrudiaCreate):
    return services.patch_irudia(session, id, irudia)


@powerbank_router.patch("/powerbanks/{id}/aldatuTokia", status_code=status.HTTP_200_OK, response_model=schemas.ListPowerbank)
def powerbank_tokia_aldatu(session: DbSession, id: int, powerbank: schemas.PowerbankTokiaPatch):
    return services.patch_powerbank_position(session, id, powerbank)

################# DELETE ENDPOINTAK #################

@powerbank_router.delete("/takillak/{id}/delete", status_code=status.HTTP_200_OK)
def delete_takilla(id, session: DbSession):
    return services.delete_takilla(session, id)


@powerbank_router.delete("/erabiltzaileak/{id}/ezabatu", status_code=status.HTTP_200_OK)
def delete_erabiltzaile(id: int, session: DbSession):
    return services.delete_erabiltzaile(session, id)

###TODO, HAU ALDATU EGIN BEHAR DA MIKELEK ESKATU DUEN MODUAN EGITEKO
@powerbank_router.post("/", response_model=schemas.ErreserbaResponse, status_code=status.HTTP_201_CREATED)
def create_powerbank_reservation(erreserba: schemas.ErreserbaCreate, db: DbSession):
    if erreserba.erreserba_hasiera >= erreserba.erreserba_bukaera:
        raise HTTPException(status_code=400, detail="Hasiera data ezin da amaiera data edo geroagokoa izan.")

    if erreserba.erreserba_hasiera.replace(tzinfo=None) < __import__("datetime").datetime.now():
        raise HTTPException(status_code=400, detail="Ezin da iraganeko datarako erreserbarik egin.")

    postua = db.query(models.Postuak).filter(models.Postuak.id_postu == erreserba.id_hasiera_postua).first()
    if not postua or postua.egoera  ==   'zerbitzuz kanpo':
        raise HTTPException(status_code=400, detail="Postu  hau ez dago erabilgarri.")

    overlap = db.query(models.Erreserbak).filter(
        models.Erreserbak.id_hasiera_postua == erreserba.id_hasiera_postua,
        models.Erreserbak.egoera == 'aktiboa',
        models.Erreserbak.erreserba_hasiera < erreserba.erreserba_bukaera,
        models.Erreserbak.erreserba_bukaera > erreserba.erreserba_hasiera,
    ).first()
    if overlap:
        raise HTTPException(status_code=409, detail="Karga - postu honek erreserba bat du tarte horretan.")

    nova = models.Erreserbak(
        id_erab=1,
        id_power=erreserba.id_power,
        erreserba_hasiera=erreserba.erreserba_hasiera,
        erreserba_bukaera=erreserba.erreserba_bukaera,
        id_hasiera_takilla=erreserba.id_hasiera_takilla,
        id_hasiera_postua=erreserba.id_hasiera_postua,
        egoera  = 'aktiboa',
    )
    db.add(nova)
    db.commit()
    db.refresh(nova)
    return nova


