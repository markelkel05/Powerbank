from fastapi import HTTPException, status
from models import models
from schemas import schemas
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session


def get_all_erabiltzaileak(db: Session):
    try:
        stmt = select(models.Erabiltzaileak).order_by(models.Erabiltzaileak.id_erab)
        return db.scalars(stmt).all()
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail="Errorea erabiltzaileak ekartzen") from e

def get_erabiltzaile_id(id: int, db: Session):
    erabiltzaile = db.get(models.Erabiltzaileak, id,)
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
            detail="Erabiltzailea ezin da ezabatu, erreserbak lotuta dauzka.",
        ) from e


def post_erabiltzaile(db: Session, erabiltzaile: schemas.CreateErabiltzaile):
    db_erabiltzaile = models.Erabiltzaileak(**erabiltzaile.model_dump(), activo=True)
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
    
    
def list_erreserbak(db: Session):
    try:
        stmt = select(models.Erreserbak).order_by(models.Erreserbak.id_erreserba)
        return db.scalars(stmt).all()
    except SQLAlchemyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Errorea erreserbak ekartzen") from e
    
def patch_erabiltzailea(db: Session, id: int, erabiltzaile: schemas.CreateErabiltzaile):
    db_erabiltzaile = db.get(models.Erabiltzaileak, id)
    if not db_erabiltzaile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ez da existitzen")
    
    for field, value in erabiltzaile.model_dump(exclude_unset=True).items():
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
    
    db_erabiltzaile.id_rol = rola
    
    try:
        db.commit()
        db.refresh(db_erabiltzaile)
        return db_erabiltzaile
    except IntegrityError as e:
        raise HTTPException(status_code=status.HTTP_400, detail="Errorea") from e
    
def list_erabiltzaile_erreserba(db: Session, id: int):
    db_erabiltzaile = db.get(models.Erabiltzaileak, id)
    if not db_erabiltzaile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ez da erabiltzailea aurkitu")

    stmt = select(models.Erreserbak).where(models.Erreserbak.id_erab == id)
    
    return db.scalars(stmt).all()  
    
def create_takilla(db: Session, takilla: schemas.CreateTakilla):
    db_takilla = models.Takillak(**takilla.model_dump())
    try:
        db.add(db_takilla)
        db.commit()
        db.refresh(db_takilla)
        return db_takilla
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Errorea sortzen") from e    
    
def patch_takilla(db: Session, id: int, takilla: schemas.CreateTakilla):
    db_takilla = db.get(models.Takillak, id)
    if not db_takilla:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ez da existitzen")
    
    for field, value in takilla.model_dump(exclude_unset=True).items():
        setattr(db_takilla, field, value)
    
    try:
        db.commit()
        db.refresh(db_takilla)
        return db_takilla
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Errorea") from e
    
def delete_takilla(db: Session, id: int):
    db_takilla = db.get(models.Takillak, id)
    if not db_takilla:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ez da aurkitu takilla")
    
    try:
        db.delete(db_takilla)
        db.commit()
        return { "message": "Takilla ondo ezabatu da", "id": id }
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Errorea") from e
    
def post_irudia(db: Session, id_takilla: int, irudia: schemas.TakillaIrudiaCreate):
    db_takilla = db.get(models.Takillak, id_takilla)
    if not db_takilla:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ez da takilla aurkitu")
    
    db_irudia = models.TakillakIrudiak(id_takilla=id_takilla, url=irudia.url)
    
    try:
        db.add(db_irudia)
        db.commit()
        db.refresh(db_irudia)
        return db_irudia
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Errorea irudia gordetzean") from e
    
def patch_irudia(db: Session, id_irudi: int, irudia: schemas.TakillaIrudiaUpdate):
    db_irudia = db.get(models.TakillakIrudiak, id_irudi)
    if not db_irudia:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ez da irudia aurkitu")
    
    for field, value in irudia.model_dump(exclude_unset=True).items():
        setattr(db_irudia, field, value)
    
    try:
        db.commit()
        db.refresh(db_irudia)
        return db_irudia
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Errorea irudia eguneratzean") from e
    
def create_powerbank(db: Session, powerbank: schemas.CreatePowerbank):
    db_powerbank = models.Powerbank(**powerbank.model_dump())
    try:
        db.add(db_powerbank)
        db.commit()
        db.refresh(db_powerbank)
        return db_powerbank
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Errorea powerbank-a sortzen") from e
    
def patch_powerbank_position(db: Session, id_power: int, powerbank: schemas.PowerbankTokiaPatch):
    db_powerbank = db.get(models.Powerbank, id_power)
    if not db_powerbank:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ez da powerbank-a aurkitu")
    
    for field, value in powerbank.model_dump(exclude_unset=True).items():
        setattr(db_powerbank, field, value)
        
    try:
        db.commit()
        db.refresh(db_powerbank)
        return db_powerbank
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Errorea powerbankaren tokia aldatzen") from e