from datetime import datetime
from typing import Annotated

from database import database
from fastapi import APIRouter, Depends, File, Header, HTTPException, Query, UploadFile, status
from models import models
from schemas import schemas
from services import auth, services, uploads
from sqlalchemy.orm import Session

DbSession = Annotated[Session, Depends(database.get_session)]


# ---------------------------------------------------------------------------
# AUTENTIFIKAZIOA: Authorization goiburua aukerakoa da (endpoint zaharrek ez
# dute tokenik behar), baina badator, nortasuna tokenetik hartzen da.
# ---------------------------------------------------------------------------


def erabiltzaile_korrontea(
    session: DbSession, authorization: Annotated[str | None, Header()] = None
) -> models.Erabiltzaileak | None:
    if not authorization:
        return None

    eskema, _, tokena = authorization.partition(" ")
    if eskema.lower() != "bearer" or not tokena.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization goiburuak 'Bearer <tokena>' formatua behar du.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    id_erab = auth.irakurri_tokena(tokena.strip())
    erabiltzailea = session.get(models.Erabiltzaileak, id_erab)
    if erabiltzailea is None or erabiltzailea.activo is False:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Erabiltzailea ez da existitzen edo desaktibatuta dago.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return erabiltzailea


def erabiltzaile_derrigorrezkoa(
    erabiltzailea: Annotated[models.Erabiltzaileak | None, Depends(erabiltzaile_korrontea)],
) -> models.Erabiltzaileak:
    if erabiltzailea is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Saioa hasi behar duzu.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return erabiltzailea


ErabiltzaileKorrontea = Annotated[
    models.Erabiltzaileak | None, Depends(erabiltzaile_korrontea)
]
DerrigorrezkoErabiltzailea = Annotated[
    models.Erabiltzaileak, Depends(erabiltzaile_derrigorrezkoa)
]


powerbank_router = APIRouter(prefix="/alokaziosistema", tags=["POWERBANKS"])

################# AUTENTIFIKAZIOA #################


@powerbank_router.post(
    "/auth/login", status_code=200, response_model=schemas.TokenResponse
)
def login(datuak: schemas.ErabiltzaileLogin, session: DbSession):
    """Emaila eta pasahitzarekin saioa hasi eta tokena lortu."""
    return services.login_erabiltzailea(session, datuak)


@powerbank_router.post(
    "/auth/erregistratu", status_code=201, response_model=schemas.TokenResponse
)
def erregistratu(datuak: schemas.Erregistroa, session: DbSession):
    """Atal publikoko erregistroa (rola beti erabiltzaile arrunta)."""
    erabiltzailea = services.erregistratu_erabiltzailea(session, datuak)
    return {
        "access_token": auth.sortu_tokena(erabiltzailea.id_erab),
        "token_type": "bearer",
        "erabiltzailea": erabiltzailea,
    }


@powerbank_router.get("/auth/ni", status_code=200, response_model=schemas.ErabiltzaileSegurua)
def ni(erabiltzailea: DerrigorrezkoErabiltzailea):
    """Saioa hasita dagoen erabiltzailearen datuak."""
    return erabiltzailea

################# GET ENDPOINTAK #################

# Erabiltzaile guztiak lortu
@powerbank_router.get("/erabiltzaileak", status_code=200, response_model=list[schemas.ListErabiltzaileak])
def get_all_participants(session: DbSession):
    return services.get_all_erabiltzaileak(session)


# Erabiltzaile bakarra lortu id bitartez
@powerbank_router.get("/erabiltzaileak/{id}", status_code=200, response_model=schemas.ListErabiltzaileak)
def get_by_id(id: int, session: DbSession):
    return services.get_erabiltzaile_id(id, session)


# Powerbank guztiak lortu (aukerako iragazkia: kargagunearen arabera)
@powerbank_router.get("/powerbanks", response_model=list[schemas.ListPowerbank])
def read_powerbanks(session: DbSession, id_takilla: int | None = None):
    return services.list_powerbankak(session, id_takilla)


# Erabiltzaile baten erreserba guztiak lortu
@powerbank_router.get("/erabiltzaileak/{id}/erreserbak", status_code=200, response_model=list[schemas.ListErreserbak])
def get_erreserbak_erabiltzaile(id: int, session: DbSession):
    return services.list_erabiltzaile_erreserba(session, id)


################### KARGAGUNEAK (takillak) ###################


@powerbank_router.get(
    "/kargaguneak", status_code=200, response_model=list[schemas.KargaguneResponse]
)
def get_kargaguneak(
    session: DbSession,
    bilaketa: str | None = None,
    egoera: models.TakillakEgoeraEnum | None = None,
):
    """Kargagune guztiak, bilaketa eta egoeraren araberako iragazkiekin."""
    return services.list_kargaguneak(session, bilaketa, egoera)


@powerbank_router.get(
    "/kargaguneak/{id}", status_code=200, response_model=schemas.KargaguneXehetasuna
)
def get_kargagunea(
    id: int,
    session: DbSession,
    hasiera: datetime | None = None,
    bukaera: datetime | None = None,
):
    """Kargagune baten xehetasunak: karga-postuak eta haien erabilgarritasuna."""
    return services.get_kargagunea(session, id, hasiera, bukaera)


@powerbank_router.get(
    "/kargaguneak/{id}/erabilgarritasuna",
    status_code=200,
    response_model=schemas.KargaguneXehetasuna,
)
def get_kargagune_erabilgarritasuna(
    id: int,
    session: DbSession,
    hasiera: datetime = Query(...),
    bukaera: datetime = Query(...),
):
    """Tarte jakin batean zein karga-postu dauden libre."""
    if hasiera >= bukaera:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hasiera data ezin da amaiera data edo geroagokoa izan.",
        )
    return services.get_kargagunea(session, id, hasiera, bukaera)


################### KARGA-POSTUAK (postuak) ###################


@powerbank_router.get(
    "/postuak", status_code=200, response_model=list[schemas.PostuaResponse]
)
def get_postuak(
    session: DbSession,
    id_takilla: int | None = None,
    egoera: models.PostuakEgoeraEnum | None = None,
):
    return services.list_postuak(session, id_takilla, egoera)


@powerbank_router.post(
    "/postuak/post", status_code=201, response_model=schemas.PostuaResponse
)
def create_postua(session: DbSession, postua: schemas.PostuaSortu):
    return services.create_postua(session, postua)


@powerbank_router.patch(
    "/postuak/{id}/eguneratu", status_code=200, response_model=schemas.PostuaResponse
)
def update_postua(id: int, postua: schemas.PostuaEguneratu, session: DbSession):
    return services.patch_postua(session, id, postua)


@powerbank_router.delete("/postuak/{id}/ezabatu", status_code=status.HTTP_200_OK)
def delete_postua(id: int, session: DbSession):
    return services.delete_postua(session, id)


################### ERRESERBAK ###################


@powerbank_router.get(
    "/erreserbak/zerrenda",
    status_code=200,
    response_model=list[schemas.ErreserbaXehetasuna],
)
def get_erreserbak_zerrenda(
    session: DbSession,
    id_erab: int | None = None,
    id_takilla: int | None = None,
    id_power: int | None = None,
    hasiera: datetime | None = None,
    bukaera: datetime | None = None,
    egoera: models.ErreserbakEgoeraEnum | None = None,
):
    """Administrazio-taulako erreserba zerrenda, iragazki guztiekin."""
    return services.list_erreserbak_filtroekin(
        session, id_erab, id_takilla, id_power, hasiera, bukaera, egoera
    )


@powerbank_router.get(
    "/erreserbak/nireak",
    status_code=200,
    response_model=list[schemas.ErreserbaXehetasuna],
)
def get_nire_erreserbak(session: DbSession, erabiltzailea: DerrigorrezkoErabiltzailea):
    """Saioa hasita dagoen erabiltzailearen erreserbak."""
    return services.nire_erreserbak(session, erabiltzailea.id_erab)


@powerbank_router.get(
    "/erreserbak", status_code=status.HTTP_200_OK, response_model=list[schemas.ErreserbaResponse]
)
def get_erreserbak(session: DbSession):
    return services.list_erreserbak(session)


@powerbank_router.get(
    "/erreserbak/{id}", status_code=200, response_model=schemas.ErreserbaResponse
)
def get_erreserba(id: int, session: DbSession):
    return services.get_erreserba(session, id)


################# POST ENDPOINTAK #################

@powerbank_router.post("/erabiltzaileak/post", status_code=201, response_model=schemas.ListErabiltzaileak)
def create_erabiltzaile(session: DbSession, erabiltzaile: schemas.CreateErabiltzaile):
    return services.post_erabiltzaile(session, erabiltzaile)


@powerbank_router.post("/takillak/post", status_code=201, response_model=schemas.KargaguneResponse)
def post_takilla(session: DbSession, takilla: schemas.CreateTakilla):
    return services.create_takilla(session, takilla)


@powerbank_router.post("/takillak/{id}/postIrudia", status_code=201, response_model=schemas.TakillaIrudiaResponse)
def post_irudia(session: DbSession, id: int, irudia: schemas.TakillaIrudiaCreate):
    return services.post_irudia(session, id, irudia)


@powerbank_router.post("/kargaguneak/post", status_code=201, response_model=schemas.KargaguneXehetasuna)
def create_kargagunea(session: DbSession, kargagunea: schemas.CreateTakilla):
    return services.create_takilla(session, kargagunea)


@powerbank_router.post(
    "/kargaguneak/{id}/irudiak", status_code=201, response_model=schemas.TakillaIrudiaResponse
)
def create_kargagune_irudia(
    id: int, irudia: schemas.TakillaIrudiaCreate, session: DbSession
):
    return services.post_irudia(session, id, irudia)


@powerbank_router.post(
    "/kargaguneak/{id}/irudiak/igo",
    status_code=201,
    response_model=schemas.TakillaIrudiaResponse,
)
async def upload_kargagune_irudia(
    id: int, session: DbSession, fitxategia: UploadFile = File(...)
):
    """Irudi bat fitxategi gisa igo (multipart/form-data)."""
    url = await uploads.gorde_irudia(fitxategia)
    return services.post_irudia(session, id, schemas.TakillaIrudiaCreate(url=url))


@powerbank_router.post("/powerbanks/post", status_code=201, response_model=schemas.ListPowerbank)
def create_powerbank(session: DbSession, powerbank: schemas.CreatePowerbank):
    return services.create_powerbank(session, powerbank)


@powerbank_router.post(
    "/erreserbak/post", status_code=201, response_model=schemas.ErreserbaResponse
)
def create_erreserba(
    session: DbSession,
    erreserba: schemas.ErreserbaSortu,
    erabiltzailea: ErabiltzaileKorrontea,
):
    """Erreserba berria: negozio-arau guztiak zerbitzarian egiaztatzen dira."""
    if (
        erabiltzailea is not None
        and erabiltzailea.id_rol != 1
        and erabiltzailea.id_erab != erreserba.id_erab
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ezin duzu beste erabiltzaile baten izenean erreserbarik egin.",
        )
    return services.sortu_erreserba(session, erreserba)


################# PATCH ENDPOINTAK #################

@powerbank_router.patch("/erabiltzaileak/{id}/eguneratu", status_code=200, response_model=schemas.ListErabiltzaileak)
def update_erabiltzaile(
    id: int,
    erabiltzaile: schemas.PatchErabiltzaile,
    session: DbSession,
    korrontea: ErabiltzaileKorrontea,
):
    if korrontea is not None and korrontea.id_rol != 1 and korrontea.id_erab != id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ezin dituzu beste erabiltzaile baten datuak aldatu.",
        )
    return services.patch_erabiltzailea(session, id, erabiltzaile)


@powerbank_router.patch("/erabiltzaileak/{id}/rola", status_code=200, response_model=schemas.ListErabiltzaileak)
def update_rola(id: int, rola: int, session: DbSession):
    return services.update_rola(session, id, rola)


@powerbank_router.patch("/takillak/{id}/eguneratu", status_code=200, response_model=schemas.KargaguneXehetasuna)
def update_takilla(id: int, takilla: schemas.PatchTakilla, session: DbSession):
    return services.patch_takilla(session, id, takilla)


@powerbank_router.patch("/takillak/{id}/aldatuIrudia", status_code=200, response_model=schemas.TakillaIrudiaResponse)
def pathc_irudia(session: DbSession, id: int, irudia: schemas.TakillaIrudiaUpdate):
    """Kargagune baten irudia aldatu (lehenengoa)."""
    return services.patch_irudia(session, id, irudia)


@powerbank_router.patch("/kargaguneak/{id}/eguneratu", status_code=200, response_model=schemas.KargaguneXehetasuna)
def update_kargagunea(id: int, kargagunea: schemas.PatchTakilla, session: DbSession):
    return services.patch_takilla(session, id, kargagunea)


@powerbank_router.patch("/kargaguneak/{id}/desaktibatu", status_code=200, response_model=schemas.KargaguneXehetasuna)
def desaktibatu_kargagunea(id: int, session: DbSession):
    return services.desaktibatu_kargagunea(session, id)


@powerbank_router.patch("/kargaguneak/{id}/irudiak/{id_irudi}", status_code=200, response_model=schemas.TakillaIrudiaResponse)
def update_irudia(id: int, id_irudi: int, irudia: schemas.TakillaIrudiaUpdate, session: DbSession):
    """Kargagune baten irudi jakin bat URL berri batekin aldatu."""
    services.get_kargagunea(session, id)
    return services.patch_irudia_id(session, id_irudi, irudia)


@powerbank_router.patch("/powerbanks/{id}/aldatuTokia", status_code=status.HTTP_200_OK, response_model=schemas.ListPowerbank)
def powerbank_tokia_aldatu(session: DbSession, id: int, powerbank: schemas.PowerbankTokiaPatch):
    return services.patch_powerbank_position(session, id, powerbank)


@powerbank_router.patch("/erreserbak/{id}/eguneratu", status_code=200, response_model=schemas.ErreserbaResponse)
def update_erreserba(
    id: int,
    erreserba: schemas.ErreserbaEguneratu,
    session: DbSession,
    erabiltzailea: ErabiltzaileKorrontea,
):
    if erabiltzailea is not None:
        db_erreserba = services.get_erreserba(session, id)
        if erabiltzailea.id_rol != 1 and db_erreserba.id_erab != erabiltzailea.id_erab:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Ezin duzu beste erabiltzaile baten erreserba aldatu.",
            )
    return services.eguneratu_erreserba(session, id, erreserba)


@powerbank_router.patch("/erreserbak/{id}/ezeztatu", status_code=200, response_model=schemas.ErreserbaResponse)
def ezeztatu_erreserba(
    id: int,
    session: DbSession,
    erabiltzailea: ErabiltzaileKorrontea,
    id_erab: int | None = None,
    admin: bool = False,
):
    """Erreserba ezeztatu.

    ``id_erab`` emanez gero, erreserba erabiltzaile horrena dela egiaztatzen da
    (5. negozio-araua). ``admin=true`` bada, administratzaileak edozein
    erreserba kudea dezake (6. negozio-araua).
    """
    if erabiltzailea is not None:
        id_erab = erabiltzailea.id_erab
        admin = erabiltzailea.id_rol == 1
    return services.ezeztatu_erreserba(session, id, id_erab, admin)


@powerbank_router.patch("/erreserbak/{id}/egoera", status_code=200, response_model=schemas.ErreserbaResponse)
def update_erreserba_egoera(
    id: int,
    egoera: schemas.ErreserbaEgoeraPatch,
    session: DbSession,
    erabiltzailea: ErabiltzaileKorrontea,
    id_erab: int | None = None,
    admin: bool = False,
):
    if erabiltzailea is not None:
        id_erab = erabiltzailea.id_erab
        admin = erabiltzailea.id_rol == 1
    return services.aldatu_erreserba_egoera(session, id, egoera.egoera, id_erab, admin)


@powerbank_router.patch("/erreserbak/{id}/erabilera", status_code=200, response_model=schemas.ErreserbaResponse)
def update_erreserba_erabilera(
    id: int, erabilera: schemas.ErreserbaErabileraPatch, session: DbSession
):
    return services.erregistratu_erabilera(session, id, erabilera)


################# DELETE ENDPOINTAK #################

@powerbank_router.delete("/takillak/{id}/delete", status_code=status.HTTP_200_OK)
def delete_takilla(id, session: DbSession):
    return services.delete_takilla(session, id)


@powerbank_router.delete("/kargaguneak/{id}/ezabatu", status_code=status.HTTP_200_OK)
def delete_kargagunea(id: int, session: DbSession):
    return services.delete_takilla(session, id)


@powerbank_router.delete("/kargaguneak/{id}/irudiak/{id_irudi}", status_code=status.HTTP_200_OK)
def delete_irudia(id: int, id_irudi: int, session: DbSession):
    return services.delete_irudia(session, id_irudi)


@powerbank_router.delete("/erabiltzaileak/{id}/ezabatu", status_code=status.HTTP_200_OK)
def delete_erabiltzaile(id: int, session: DbSession):
    return services.delete_erabiltzaile(session, id)


#### TODO (Markel): Endpoint zaharra, bateragarritasunerako mantenduta.
#### Atal publikotik /erreserbak/post erabiliko da. Honek id_erab=1 hartzen du.
@powerbank_router.post("/", response_model=schemas.ErreserbaResponse, status_code=status.HTTP_201_CREATED)
def create_powerbank_reservation(
    erreserba: schemas.ErreserbaCreate, db: DbSession, id_erab: int = 1
):
    return services.sortu_erreserba(
        db,
        schemas.ErreserbaSortu(
            id_erab=id_erab,
            id_power=erreserba.id_power,
            erreserba_hasiera=erreserba.erreserba_hasiera,
            erreserba_bukaera=erreserba.erreserba_bukaera,
            id_hasiera_takilla=erreserba.id_hasiera_takilla,
            id_hasiera_postua=erreserba.id_hasiera_postua,
        ),
    )
