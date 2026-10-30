"""Negozio-logika osoa hemen dago. Routerrek ez dute coderik izango."""

from datetime import datetime, timezone

from fastapi import HTTPException, status
from models import models
from schemas import schemas
from services import auth
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

# ---------------------------------------------------------------------------
# LAGUNTZAILEAK
# ---------------------------------------------------------------------------


def _orain() -> datetime:
    """Oraingo unea UTC-n."""
    return datetime.now(timezone.utc)


def _utc(data: datetime | None) -> datetime | None:
    """Data bat UTC-ra pasatzen du.

    Angularretik ``datetime-local`` erabiltzen denez, ordua zonarik gabe
    iristen da. Kasu horretan zerbitzariaren ordu-zona berekoa dela suposatzen
    da eta UTC-ra aldatzen da, datu basean dena UTC gordetzeko.
    """
    if data is None:
        return None
    if data.tzinfo is None:
        data = data.replace(tzinfo=datetime.now().astimezone().tzinfo)
    return data.astimezone(timezone.utc)


def _eguneratu_duen_erabiltzailea(
    erreserba: models.Erreserbak, id_erab: int | None, admin: bool
) -> None:
    """Negozio-araua: erabiltzaileek beren erreserbak bakarrik alda ditzakete."""
    if id_erab is not None and not admin and erreserba.id_erab != id_erab:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ezin duzu beste erabiltzaile baten erreserba aldatu.",
        )


# ---------------------------------------------------------------------------
# ERABILTZAILEAK
# ---------------------------------------------------------------------------


def get_all_erabiltzaileak(db: Session):
    try:
        stmt = select(models.Erabiltzaileak).order_by(models.Erabiltzaileak.id_erab)
        return db.scalars(stmt).all()
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail="Errorea erabiltzaileak ekartzen") from e


def get_erabiltzaile_id(id: int, db: Session):
    erabiltzaile = db.get(models.Erabiltzaileak, id)
    if erabiltzaile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ez da existitzen")
    return erabiltzaile


def delete_erabiltzaile(db: Session, id: int):
    erabiltzaile = db.get(models.Erabiltzaileak, id)
    if erabiltzaile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ez da erabiltzailea aurkitu")

    try:
        db.delete(erabiltzaile)
        db.commit()
        return {"message": "Erabiltzailea ondo ezabatu da", "id": id}
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Erabiltzailea ezin da ezabatu, erreserbak lotuta dauzka. Desaktibatu ezazu.",
        ) from e


def post_erabiltzaile(db: Session, erabiltzaile: schemas.CreateErabiltzaile):
    datuak = erabiltzaile.model_dump()
    # Pasahitzak ez dira inoiz testu lauan gordetzen
    datuak["pasahitza"] = auth.prestatu_pasahitza(datuak["pasahitza"])
    db_erabiltzaile = models.Erabiltzaileak(**datuak, activo=True)
    try:
        db.add(db_erabiltzaile)
        db.commit()
        db.refresh(db_erabiltzaile)
        return db_erabiltzaile
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ezin da erabiltzailea gorde: NANa edo emaila dagoeneko erregistratuta egon daiteke, edo hautatutako rola ez da baliozkoa.",
        ) from e


def patch_erabiltzailea(db: Session, id: int, erabiltzaile: schemas.PatchErabiltzaile):
    db_erabiltzaile = db.get(models.Erabiltzaileak, id)
    if not db_erabiltzaile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ez da existitzen")

    datuak = erabiltzaile.model_dump(exclude_unset=True)
    if datuak.get("pasahitza"):
        datuak["pasahitza"] = auth.prestatu_pasahitza(datuak["pasahitza"])

    for field, value in datuak.items():
        setattr(db_erabiltzaile, field, value)

    try:
        db.commit()
        db.refresh(db_erabiltzaile)
        return db_erabiltzaile
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Errorea") from e


def update_rola(db: Session, id: int, rola: int):
    db_erabiltzaile = db.get(models.Erabiltzaileak, id)
    if not db_erabiltzaile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ez da erabiltzailea aurkitu")

    if rola not in (1, 2):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rola ez da baliozkoa")

    db_erabiltzaile.id_rol = rola

    try:
        db.commit()
        db.refresh(db_erabiltzaile)
        return db_erabiltzaile
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Errorea") from e


def erregistratu_erabiltzailea(db: Session, datuak: schemas.Erregistroa):
    """Atal publikoko erregistroa: rola beti 2 (erabiltzaile arrunta)."""
    db_erabiltzailea = models.Erabiltzaileak(
        **datuak.model_dump(exclude={"pasahitza"}),
        pasahitza=auth.get_password_hash(datuak.pasahitza),
        id_rol=2,
        activo=True,
    )
    try:
        db.add(db_erabiltzailea)
        db.commit()
        db.refresh(db_erabiltzailea)
        return db_erabiltzailea
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Emaila edo NANa dagoeneko erregistratuta dago.",
        ) from e


def login_erabiltzailea(db: Session, datuak: schemas.ErabiltzaileLogin):
    erabiltzailea = db.scalar(
        select(models.Erabiltzaileak).where(
            func.lower(models.Erabiltzaileak.email) == datuak.email.strip().lower()
        )
    )

    if erabiltzailea is None or not auth.pasahitza_egiaztatu(
        datuak.pasahitza, erabiltzailea.pasahitza
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Emaila edo pasahitza okerra da.",
        )

    if erabiltzailea.activo is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Erabiltzaile hau desaktibatuta dago.",
        )

    # Oraindik testu lauan zegoen pasahitza bada, orain hash gisa gordetzen da
    if not auth.pasahitza_hash_a_da(erabiltzailea.pasahitza):
        erabiltzailea.pasahitza = auth.get_password_hash(datuak.pasahitza)
        db.commit()
        db.refresh(erabiltzailea)

    return {
        "access_token": auth.sortu_tokena(erabiltzailea.id_erab),
        "token_type": "bearer",
        "erabiltzailea": erabiltzailea,
    }


def list_erabiltzaile_erreserba(db: Session, id: int):
    db_erabiltzaile = db.get(models.Erabiltzaileak, id)
    if not db_erabiltzaile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ez da erabiltzailea aurkitu")

    stmt = (
        select(models.Erreserbak)
        .where(models.Erreserbak.id_erab == id)
        .order_by(models.Erreserbak.erreserba_hasiera.desc())
    )
    return db.scalars(stmt).all()


# ---------------------------------------------------------------------------
# KARGAGUNEAK (takillak)
# ---------------------------------------------------------------------------


def _kargagune_datuak(db: Session, takillak: list[models.Takillak]) -> list[dict]:
    """Kargaguneen zerrenda, taulan erakusteko kontagailuekin."""
    ids = [t.id_takilla for t in takillak]
    if not ids:
        return []

    orain = _orain()
    erreserbak_stmt = (
        select(models.Erreserbak.id_hasiera_takilla, func.count())
        .where(
            models.Erreserbak.id_hasiera_takilla.in_(ids),
            models.Erreserbak.egoera == models.ErreserbakEgoeraEnum.aktiboa,
        )
        .group_by(models.Erreserbak.id_hasiera_takilla)
    )
    erreserbak_kopurua = dict(db.execute(erreserbak_stmt).all())

    # Orain bertan erreserbatuta dauden postuak (une honetan okupatuta)
    une_okupatuta_stmt = (
        select(models.Erreserbak.id_hasiera_takilla, func.count())
        .where(
            models.Erreserbak.id_hasiera_takilla.in_(ids),
            models.Erreserbak.egoera == models.ErreserbakEgoeraEnum.aktiboa,
            models.Erreserbak.erreserba_hasiera <= orain,
            models.Erreserbak.erreserba_bukaera > orain,
        )
        .group_by(models.Erreserbak.id_hasiera_takilla)
    )
    une_okupatuta = dict(db.execute(une_okupatuta_stmt).all())

    powerbank_stmt = (
        select(models.Powerbank.id_takilla, func.count())
        .where(models.Powerbank.id_takilla.in_(ids))
        .group_by(models.Powerbank.id_takilla)
    )
    powerbank_kopurua = dict(db.execute(powerbank_stmt).all())

    return [
        {
            "id_takilla": t.id_takilla,
            "izena": t.izena,
            "helbidea": t.helbidea,
            "egoera": t.egoera,
            "irudiak": [irudi.url for irudi in t.irudiak],
            "postuak_kopurua": len(t.postuak),
            "postu_libreak": max(
                len(t.postuak) - une_okupatuta.get(t.id_takilla, 0), 0
            ),
            "powerbank_kopurua": powerbank_kopurua.get(t.id_takilla, 0),
            "erreserba_aktiboak": erreserbak_kopurua.get(t.id_takilla, 0),
        }
        for t in takillak
    ]


def _postu_libreak(db: Session, id_takilla: int, hasiera: datetime, bukaera: datetime) -> set[int]:
    """Tarte horretan erreserba aktiborik ez duten karga-postuen id-ak."""
    stmt = select(models.Erreserbak.id_hasiera_postua).where(
        models.Erreserbak.id_hasiera_takilla == id_takilla,
        models.Erreserbak.egoera == models.ErreserbakEgoeraEnum.aktiboa,
        models.Erreserbak.erreserba_hasiera < bukaera,
        models.Erreserbak.erreserba_bukaera > hasiera,
    )
    return set(db.scalars(stmt).all())


def _kargagune_xehetasuna(
    db: Session,
    takilla: models.Takillak,
    hasiera: datetime | None = None,
    bukaera: datetime | None = None,
) -> dict:
    hasiera = hasiera or _orain()
    bukaera = bukaera or hasiera

    okupatuta = _postu_libreak(db, takilla.id_takilla, hasiera, bukaera)

    oinarria = _kargagune_datuak(db, [takilla])[0]
    oinarria["irudien_xehetasuna"] = [
        {"id_irudi": irudi.id_irudi, "id_takilla": irudi.id_takilla, "url": irudi.url}
        for irudi in sorted(takilla.irudiak, key=lambda i: i.id_irudi)
    ]
    oinarria["postuak"] = [
        {
            "id_postu": postua.id_postu,
            "id_takilla": postua.id_takilla,
            "egoera": postua.egoera,
            "libre": postua.id_postu not in okupatuta,
            "powerbank": (
                {
                    "id_power": postua.powerbank.id_power,
                    "karga": postua.powerbank.karga,
                    "id_postu": postua.powerbank.id_postu,
                    "id_takilla": postua.powerbank.id_takilla,
                }
                if postua.powerbank
                else None
            ),
        }
        for postua in sorted(takilla.postuak, key=lambda p: p.id_postu)
    ]
    return oinarria


def _kargagunea_lortu(db: Session, id_takilla: int) -> models.Takillak:
    takilla = db.get(models.Takillak, id_takilla)
    if takilla is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ez da kargagunea aurkitu"
        )
    return takilla


def list_kargaguneak(
    db: Session,
    bilaketa: str | None = None,
    egoera: models.TakillakEgoeraEnum | None = None,
):
    stmt = (
        select(models.Takillak)
        .options(
            selectinload(models.Takillak.irudiak),
            selectinload(models.Takillak.postuak).selectinload(models.Postuak.powerbank),
        )
        .order_by(models.Takillak.id_takilla)
    )
    if egoera is not None:
        stmt = stmt.where(models.Takillak.egoera == egoera)
    if bilaketa:
        stmt = stmt.where(
            models.Takillak.izena.ilike(f"%{bilaketa}%")
            | models.Takillak.helbidea.ilike(f"%{bilaketa}%")
        )

    try:
        takillak = db.scalars(stmt).all()
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errorea kargaguneak ekartzen",
        ) from e

    return _kargagune_datuak(db, list(takillak))


def get_kargagunea(
    db: Session,
    id_takilla: int,
    hasiera: datetime | None = None,
    bukaera: datetime | None = None,
):
    takilla = _kargagunea_lortu(db, id_takilla)
    return _kargagune_xehetasuna(db, takilla, _utc(hasiera), _utc(bukaera))


def create_takilla(db: Session, takilla: schemas.CreateTakilla):
    """Kargagune berria sortu."""
    db_takilla = models.Takillak(**takilla.model_dump())
    try:
        db.add(db_takilla)
        db.commit()
        db.refresh(db_takilla)
        return _kargagune_xehetasuna(db, db_takilla)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Errorea kargagunea sortzen"
        ) from e


def patch_takilla(db: Session, id: int, takilla: schemas.PatchTakilla):
    db_takilla = _kargagunea_lortu(db, id)

    for field, value in takilla.model_dump(exclude_unset=True).items():
        setattr(db_takilla, field, value)

    try:
        db.commit()
        db.refresh(db_takilla)
        return _kargagune_xehetasuna(db, db_takilla)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Errorea") from e


def desaktibatu_kargagunea(db: Session, id: int):
    """Negozio-araua: erlazioak dituen kargagunea ez da ezabatu, desaktibatu egiten da."""
    db_takilla = _kargagunea_lortu(db, id)
    db_takilla.egoera = models.TakillakEgoeraEnum.zerbitzuz_kanpo
    try:
        db.commit()
        db.refresh(db_takilla)
        return _kargagune_xehetasuna(db, db_takilla)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Errorea") from e


def delete_takilla(db: Session, id: int):
    db_takilla = _kargagunea_lortu(db, id)

    postuak = db.scalar(
        select(func.count())
        .select_from(models.Postuak)
        .where(models.Postuak.id_takilla == id)
    )
    erreserbak = db.scalar(
        select(func.count())
        .select_from(models.Erreserbak)
        .where(
            (models.Erreserbak.id_hasiera_takilla == id)
            | (models.Erreserbak.id_bukaera_takilla == id)
        )
    )

    if postuak or erreserbak:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Kargaguneak karga-postuak edo erreserbak ditu lotuta. "
                "Ezin da ezabatu: desaktibatu ezazu."
            ),
        )

    try:
        db.delete(db_takilla)
        db.commit()
        return {"message": "Kargagunea ondo ezabatu da", "id": id}
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Kargagunea ezin da ezabatu, beste datu batzuekin lotuta dago.",
        ) from e


def post_irudia(db: Session, id_takilla: int, irudia: schemas.TakillaIrudiaCreate):
    db_takilla = _kargagunea_lortu(db, id_takilla)

    db_irudia = models.TakillakIrudiak(id_takilla=id_takilla, url=irudia.url)
    try:
        db.add(db_irudia)
        db.commit()
        db.refresh(db_irudia)
        return db_irudia
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Errorea irudia gordetzean",
        ) from e


def patch_irudia(db: Session, id_takilla: int, irudia: schemas.TakillaIrudiaUpdate):
    """Kargagune baten irudia aldatu (lehenengoa badago) edo berria sortu."""
    db_takilla = _kargagunea_lortu(db, id_takilla)
    url = (irudia.url or "").strip()
    if not url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Irudiaren URLa beharrezkoa da"
        )

    db_irudia = db.scalar(
        select(models.TakillakIrudiak)
        .where(models.TakillakIrudiak.id_takilla == db_takilla.id_takilla)
        .order_by(models.TakillakIrudiak.id_irudi)
    )
    if db_irudia is None:
        db_irudia = models.TakillakIrudiak(id_takilla=db_takilla.id_takilla, url=url)
        db.add(db_irudia)
    else:
        db_irudia.url = url

    try:
        db.commit()
        db.refresh(db_irudia)
        return db_irudia
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Errorea irudia eguneratzean",
        ) from e


def patch_irudia_id(db: Session, id_irudi: int, irudia: schemas.TakillaIrudiaUpdate):
    """Irudi jakin baten URLa aldatu."""
    db_irudia = db.get(models.TakillakIrudiak, id_irudi)
    if db_irudia is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ez da irudia aurkitu"
        )

    for field, value in irudia.model_dump(exclude_unset=True).items():
        setattr(db_irudia, field, value)

    try:
        db.commit()
        db.refresh(db_irudia)
        return db_irudia
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Errorea irudia eguneratzean",
        ) from e


def delete_irudia(db: Session, id_irudi: int):
    db_irudia = db.get(models.TakillakIrudiak, id_irudi)
    if db_irudia is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ez da irudia aurkitu"
        )
    db.delete(db_irudia)
    db.commit()
    return {"message": "Irudia ondo ezabatu da", "id": id_irudi}


# ---------------------------------------------------------------------------
# KARGA-POSTUAK (postuak)
# ---------------------------------------------------------------------------


def _postua_datuak(postua: models.Postuak, okupatuta: set[int] | None = None) -> dict:
    return {
        "id_postu": postua.id_postu,
        "id_takilla": postua.id_takilla,
        "egoera": postua.egoera,
        "libre": postua.id_postu not in (okupatuta or set()),
        "powerbank": (
            {
                "id_power": postua.powerbank.id_power,
                "karga": postua.powerbank.karga,
                "id_postu": postua.powerbank.id_postu,
                "id_takilla": postua.powerbank.id_takilla,
            }
            if postua.powerbank
            else None
        ),
    }


def list_postuak(
    db: Session,
    id_takilla: int | None = None,
    egoera: models.PostuakEgoeraEnum | None = None,
):
    stmt = (
        select(models.Postuak)
        .options(selectinload(models.Postuak.powerbank))
        .order_by(models.Postuak.id_postu)
    )
    if id_takilla is not None:
        stmt = stmt.where(models.Postuak.id_takilla == id_takilla)
    if egoera is not None:
        stmt = stmt.where(models.Postuak.egoera == egoera)

    postuak = db.scalars(stmt).all()
    return [_postua_datuak(postua) for postua in postuak]


def create_postua(db: Session, postua: schemas.PostuaSortu):
    _kargagunea_lortu(db, postua.id_takilla)

    db_postua = models.Postuak(**postua.model_dump())
    try:
        db.add(db_postua)
        db.commit()
        db.refresh(db_postua)
        return _postua_datuak(db_postua)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Errorea karga-postua sortzen"
        ) from e


def patch_postua(db: Session, id_postu: int, postua: schemas.PostuaEguneratu):
    db_postua = db.get(models.Postuak, id_postu)
    if db_postua is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ez da karga-postua aurkitu"
        )

    datuak = postua.model_dump(exclude_unset=True)

    if "id_takilla" in datuak and datuak["id_takilla"] != db_postua.id_takilla:
        if db_postua.powerbank is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Karga-postuak powerbank bat dauka: ezin da beste kargagune batera aldatu.",
            )
        _kargagunea_lortu(db, datuak["id_takilla"])

    for field, value in datuak.items():
        setattr(db_postua, field, value)

    try:
        db.commit()
        db.refresh(db_postua)
        return _postua_datuak(db_postua)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Errorea") from e


def delete_postua(db: Session, id_postu: int):
    db_postua = db.get(models.Postuak, id_postu)
    if db_postua is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ez da karga-postua aurkitu"
        )

    erreserbak = db.scalar(
        select(func.count())
        .select_from(models.Erreserbak)
        .where(
            (models.Erreserbak.id_hasiera_postua == id_postu)
            | (models.Erreserbak.id_bukaera_postua == id_postu)
        )
    )
    if db_postua.powerbank is not None or erreserbak:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Karga-postuak powerbanka edo erreserbak ditu lotuta: ezin da ezabatu.",
        )

    try:
        db.delete(db_postua)
        db.commit()
        return {"message": "Karga-postua ondo ezabatu da", "id": id_postu}
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Karga-postua ezin da ezabatu, beste datu batzuekin lotuta dago.",
        ) from e


# ---------------------------------------------------------------------------
# POWERBANK-AK (irakurketa eta sorkuntza; kudeaketa osoa Urkoren atala da)
# ---------------------------------------------------------------------------


def list_powerbankak(db: Session, id_takilla: int | None = None):
    stmt = select(models.Powerbank).order_by(models.Powerbank.id_power)
    if id_takilla is not None:
        stmt = stmt.where(models.Powerbank.id_takilla == id_takilla)
    return db.scalars(stmt).all()


def create_powerbank(db: Session, powerbank: schemas.CreatePowerbank):
    if powerbank.id_postu is not None:
        postua = db.get(models.Postuak, powerbank.id_postu)
        if postua is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Ez da karga-postua aurkitu"
            )
        if powerbank.id_takilla is not None and postua.id_takilla != powerbank.id_takilla:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Karga-postua ez da adierazitako kargagunearena.",
            )
    if powerbank.id_takilla is not None:
        _kargagunea_lortu(db, powerbank.id_takilla)

    db_powerbank = models.Powerbank(**powerbank.model_dump())
    try:
        db.add(db_powerbank)
        db.commit()
        db.refresh(db_powerbank)
        return db_powerbank
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Errorea powerbank-a sortzen (karga-postua okupatuta egon daiteke)",
        ) from e


def patch_powerbank_position(db: Session, id_power: int, powerbank: schemas.PowerbankTokiaPatch):
    db_powerbank = db.get(models.Powerbank, id_power)
    if not db_powerbank:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ez da powerbank-a aurkitu"
        )

    datuak = powerbank.model_dump(exclude_unset=True)

    if datuak.get("id_postu") is not None:
        postua = db.get(models.Postuak, datuak["id_postu"])
        if postua is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Ez da karga-postua aurkitu"
            )
        if datuak.get("id_takilla") is not None and postua.id_takilla != datuak["id_takilla"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Karga-postua ez da adierazitako kargagunearena.",
            )
        datuak.setdefault("id_takilla", postua.id_takilla)

    for field, value in datuak.items():
        setattr(db_powerbank, field, value)

    try:
        db.commit()
        db.refresh(db_powerbank)
        return db_powerbank
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Errorea powerbankaren tokia aldatzen",
        ) from e


# ---------------------------------------------------------------------------
# ERRESERBAK
# ---------------------------------------------------------------------------


def list_erreserbak(db: Session):
    try:
        stmt = select(models.Erreserbak).order_by(models.Erreserbak.id_erreserba)
        return db.scalars(stmt).all()
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errorea erreserbak ekartzen",
        ) from e


def _erreserba_xehetasunak(erreserba: models.Erreserbak) -> dict:
    return {
        "id_erreserba": erreserba.id_erreserba,
        "id_erab": erreserba.id_erab,
        "id_power": erreserba.id_power,
        "erreserba_hasiera": erreserba.erreserba_hasiera,
        "erreserba_bukaera": erreserba.erreserba_bukaera,
        "id_hasiera_takilla": erreserba.id_hasiera_takilla,
        "id_hasiera_postua": erreserba.id_hasiera_postua,
        "egoera": erreserba.egoera,
        "erabiltzaile_izena": (
            f"{erreserba.erabiltzailea.izena} {erreserba.erabiltzailea.abizenak}"
            if erreserba.erabiltzailea
            else ""
        ),
        "erabiltzaile_email": erreserba.erabiltzailea.email if erreserba.erabiltzailea else "",
        "kargagune_izena": erreserba.hasiera_takilla.izena if erreserba.hasiera_takilla else "",
        "kargagune_helbidea": erreserba.hasiera_takilla.helbidea if erreserba.hasiera_takilla else "",
        "powerbank_karga": erreserba.powerbank.karga if erreserba.powerbank else 0,
        "bukaera_kargagune_izena": (
            erreserba.bukaera_takilla.izena if erreserba.bukaera_takilla else None
        ),
        "erabilera_hasiera": erreserba.erabilera_hasiera,
        "erabilera_bukaera": erreserba.erabilera_bukaera,
    }


def list_erreserbak_filtroekin(
    db: Session,
    id_erab: int | None = None,
    id_takilla: int | None = None,
    id_power: int | None = None,
    hasiera: datetime | None = None,
    bukaera: datetime | None = None,
    egoera: models.ErreserbakEgoeraEnum | None = None,
):
    """Administrazio-taulako zerrenda: iragazkiak + erlazionatutako izenak."""
    stmt = (
        select(models.Erreserbak)
        .options(
            selectinload(models.Erreserbak.erabiltzailea),
            selectinload(models.Erreserbak.powerbank),
            selectinload(models.Erreserbak.hasiera_takilla),
            selectinload(models.Erreserbak.bukaera_takilla),
        )
        .order_by(models.Erreserbak.erreserba_hasiera.desc())
    )

    if id_erab is not None:
        stmt = stmt.where(models.Erreserbak.id_erab == id_erab)
    if id_takilla is not None:
        stmt = stmt.where(models.Erreserbak.id_hasiera_takilla == id_takilla)
    if id_power is not None:
        stmt = stmt.where(models.Erreserbak.id_power == id_power)
    if egoera is not None:
        stmt = stmt.where(models.Erreserbak.egoera == egoera)
    if hasiera is not None:
        stmt = stmt.where(models.Erreserbak.erreserba_bukaera >= _utc(hasiera))
    if bukaera is not None:
        stmt = stmt.where(models.Erreserbak.erreserba_hasiera <= _utc(bukaera))

    erreserbak = db.scalars(stmt).all()
    return [_erreserba_xehetasunak(erreserba) for erreserba in erreserbak]


def nire_erreserbak(db: Session, id_erab: int):
    """Saioa hasita dagoen erabiltzailearen erreserbak."""
    return list_erreserbak_filtroekin(db, id_erab=id_erab)


def get_erreserba(db: Session, id_erreserba: int) -> models.Erreserbak:
    erreserba = db.get(models.Erreserbak, id_erreserba)
    if erreserba is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ez da erreserba aurkitu"
        )
    return erreserba


def _gainjartzeak_egiaztatu(
    db: Session,
    id_hasiera_postua: int,
    id_power: int,
    hasiera: datetime,
    bukaera: datetime,
    id_erreserba: int | None = None,
) -> None:
    """4. negozio-araua: ezin dira tartean gainjartzen diren erreserba aktiboak egon."""
    oinarrizko_baldintzak = [
        models.Erreserbak.egoera == models.ErreserbakEgoeraEnum.aktiboa,
        models.Erreserbak.erreserba_hasiera < bukaera,
        models.Erreserbak.erreserba_bukaera > hasiera,
    ]
    if id_erreserba is not None:
        oinarrizko_baldintzak.append(models.Erreserbak.id_erreserba != id_erreserba)

    postua = db.scalar(
        select(models.Erreserbak.id_erreserba).where(
            models.Erreserbak.id_hasiera_postua == id_hasiera_postua,
            *oinarrizko_baldintzak,
        )
    )
    if postua is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Karga-postu honek erreserba aktibo bat dauka tarte horretan.",
        )

    powerbanka = db.scalar(
        select(models.Erreserbak.id_erreserba).where(
            models.Erreserbak.id_power == id_power,
            *oinarrizko_baldintzak,
        )
    )
    if powerbanka is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Powerbank honek erreserba aktibo bat dauka tarte horretan.",
        )


def _erreserba_balioztatu(
    db: Session,
    id_erab: int,
    id_power: int,
    id_hasiera_takilla: int,
    id_hasiera_postua: int,
    hasiera: datetime,
    bukaera: datetime,
    id_erreserba: int | None = None,
    iragana_egiaztatu: bool = True,
) -> None:
    """Erreserben negozio-arau guztiak (zerbitzariaren aldean)."""
    # 2. araua: hasiera-bukaera baino lehenago
    if hasiera >= bukaera:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hasiera data ezin da amaiera data edo geroagokoa izan.",
        )

    # 3. araua: ezin da iraganeko datarako erreserbarik egin
    if iragana_egiaztatu and hasiera < _orain():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ezin da iraganeko datarako erreserbarik egin.",
        )

    erabiltzailea = db.get(models.Erabiltzaileak, id_erab)
    if erabiltzailea is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ez da erabiltzailea aurkitu"
        )
    if erabiltzailea.activo is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erabiltzaile desaktibatua: ezin du erreserbarik egin.",
        )

    takilla = db.get(models.Takillak, id_hasiera_takilla)
    if takilla is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ez da kargagunea aurkitu"
        )

    postua = db.get(models.Postuak, id_hasiera_postua)
    if postua is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ez da karga-postua aurkitu"
        )

    if postua.id_takilla != takilla.id_takilla:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Karga-postua ez da adierazitako kargagunearena.",
        )

    # 4. araua: mantentze-lanetan edo zerbitzuz kanpo dauden kargaguneak ezin dira erreserbatu
    if takilla.egoera != models.TakillakEgoeraEnum.erabilgarri:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Kargagunea ez dago erabilgarri (mantentze-lanetan edo zerbitzuz kanpo).",
        )

    powerbank = db.get(models.Powerbank, id_power)
    if powerbank is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ez da powerbank-a aurkitu"
        )
    if powerbank.id_takilla is not None and powerbank.id_takilla != takilla.id_takilla:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Powerbank-a ez dago kargagune horretan.",
        )

    # 1. araua: gainjartzen diren erreserba aktiboak
    _gainjartzeak_egiaztatu(
        db, id_hasiera_postua, id_power, hasiera, bukaera, id_erreserba
    )


def sortu_erreserba(db: Session, erreserba: schemas.ErreserbaSortu):
    hasiera = _utc(erreserba.erreserba_hasiera)
    bukaera = _utc(erreserba.erreserba_bukaera)

    _erreserba_balioztatu(
        db,
        erreserba.id_erab,
        erreserba.id_power,
        erreserba.id_hasiera_takilla,
        erreserba.id_hasiera_postua,
        hasiera,
        bukaera,
    )

    db_erreserba = models.Erreserbak(
        id_erab=erreserba.id_erab,
        id_power=erreserba.id_power,
        erreserba_hasiera=hasiera,
        erreserba_bukaera=bukaera,
        id_hasiera_takilla=erreserba.id_hasiera_takilla,
        id_hasiera_postua=erreserba.id_hasiera_postua,
        egoera=models.ErreserbakEgoeraEnum.aktiboa,
    )

    try:
        db.add(db_erreserba)
        db.commit()
        db.refresh(db_erreserba)
        return db_erreserba
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Errorea erreserba gordetzean (erlazionatutako datuak ez dira baliozkoak).",
        ) from e


def eguneratu_erreserba(
    db: Session, id_erreserba: int, aldaketak: schemas.ErreserbaEguneratu
):
    db_erreserba = get_erreserba(db, id_erreserba)

    if db_erreserba.egoera != models.ErreserbakEgoeraEnum.aktiboa:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Erreserba soilik aktiboa dagoenean alda daiteke.",
        )

    datuak = aldaketak.model_dump(exclude_unset=True)

    id_power = datuak.get("id_power", db_erreserba.id_power)
    id_hasiera_takilla = datuak.get("id_hasiera_takilla", db_erreserba.id_hasiera_takilla)
    id_hasiera_postua = datuak.get("id_hasiera_postua", db_erreserba.id_hasiera_postua)
    hasiera = _utc(datuak.get("erreserba_hasiera", db_erreserba.erreserba_hasiera))
    bukaera = _utc(datuak.get("erreserba_bukaera", db_erreserba.erreserba_bukaera))

    _erreserba_balioztatu(
        db,
        db_erreserba.id_erab,
        id_power,
        id_hasiera_takilla,
        id_hasiera_postua,
        hasiera,
        bukaera,
        id_erreserba=id_erreserba,
        iragana_egiaztatu=False,
    )

    db_erreserba.id_power = id_power
    db_erreserba.id_hasiera_takilla = id_hasiera_takilla
    db_erreserba.id_hasiera_postua = id_hasiera_postua
    db_erreserba.erreserba_hasiera = hasiera
    db_erreserba.erreserba_bukaera = bukaera

    try:
        db.commit()
        db.refresh(db_erreserba)
        return db_erreserba
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Errorea erreserba eguneratzean"
        ) from e


def ezeztatu_erreserba(
    db: Session, id_erreserba: int, id_erab: int | None = None, admin: bool = False
):
    """7. araua: ezeztatutako erreserbek ez dute karga-postua blokeatuko."""
    db_erreserba = get_erreserba(db, id_erreserba)
    _eguneratu_duen_erabiltzailea(db_erreserba, id_erab, admin)

    if db_erreserba.egoera != models.ErreserbakEgoeraEnum.aktiboa:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Erreserba ez dago aktibo: ezin da ezeztatu.",
        )

    db_erreserba.egoera = models.ErreserbakEgoeraEnum.ezeztatuta
    try:
        db.commit()
        db.refresh(db_erreserba)
        return db_erreserba
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Errorea erreserba ezeztatzean"
        ) from e


def aldatu_erreserba_egoera(
    db: Session,
    id_erreserba: int,
    egoera: models.ErreserbakEgoeraEnum,
    id_erab: int | None = None,
    admin: bool = False,
):
    db_erreserba = get_erreserba(db, id_erreserba)
    _eguneratu_duen_erabiltzailea(db_erreserba, id_erab, admin)

    if egoera == db_erreserba.egoera:
        return db_erreserba

    # Berriro aktibatzea bada, negozio-arauak berriz egiaztatu behar dira
    if egoera == models.ErreserbakEgoeraEnum.aktiboa:
        if _utc(db_erreserba.erreserba_hasiera) < _orain():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ezin da iraganeko erreserba bat berriro aktibatu.",
            )
        _gainjartzeak_egiaztatu(
            db,
            db_erreserba.id_hasiera_postua,
            db_erreserba.id_power,
            _utc(db_erreserba.erreserba_hasiera),
            _utc(db_erreserba.erreserba_bukaera),
            id_erreserba=id_erreserba,
        )

    db_erreserba.egoera = egoera
    if egoera == models.ErreserbakEgoeraEnum.amaituta and db_erreserba.erabilera_bukaera is None:
        db_erreserba.erabilera_bukaera = _orain()

    try:
        db.commit()
        db.refresh(db_erreserba)
        return db_erreserba
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Errorea erreserba eguneratzean"
        ) from e


def erregistratu_erabilera(
    db: Session, id_erreserba: int, erabilera: schemas.ErreserbaErabileraPatch
):
    """Powerbank-a noiz hartu eta non bueltatu den markatzeko (QR irakurgailua)."""
    db_erreserba = get_erreserba(db, id_erreserba)
    datuak = erabilera.model_dump(exclude_unset=True)

    if datuak.get("id_bukaera_postua") is not None:
        postua = db.get(models.Postuak, datuak["id_bukaera_postua"])
        if postua is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Ez da bukaerako karga-postua aurkitu"
            )
        db_erreserba.id_bukaera_postua = postua.id_postu
        db_erreserba.id_bukaera_takilla = postua.id_takilla

    if datuak.get("erabilera_hasiera") is not None:
        db_erreserba.erabilera_hasiera = _utc(datuak["erabilera_hasiera"])
    if datuak.get("erabilera_bukaera") is not None:
        db_erreserba.erabilera_bukaera = _utc(datuak["erabilera_bukaera"])
        db_erreserba.egoera = models.ErreserbakEgoeraEnum.amaituta

    try:
        db.commit()
        db.refresh(db_erreserba)
        return db_erreserba
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Errorea erabilera gordetzean"
        ) from e
