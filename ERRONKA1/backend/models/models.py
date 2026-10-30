import enum

from database.database import Base
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column


class Rol(Base):
    __tablename__ = "rolak"
    
    id_rol: Mapped[int] = mapped_column(primary_key=True, index=True)
    izena: Mapped[str] = mapped_column(String(100))

class Erabiltzaileak(Base):
    __tablename__ = "erabiltzaileak"
    
    id_erab: Mapped[int] = mapped_column(primary_key=True, index=True)
    nan: Mapped[str] = mapped_column(String(9), nullable=False, unique=True)
    izena: Mapped[str] = mapped_column(String(100), nullable=False)
    abizenak: Mapped[str] = mapped_column(String(250), nullable=False)
    email: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    pasahitza: Mapped[str] = mapped_column(String(200), nullable=False)
    helbidea: Mapped[str] = mapped_column(String(250), nullable=False)
    id_rol: Mapped[int] = mapped_column(ForeignKey("rolak.id_rol"), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False)
    
class TakillakEgoeraEnum(str, enum.Enum):
    erabilgarri = "erabilgarri"
    mantentze_lanetan = "mantentze_lanetan"
    zerbitzuz_kanpo = "zerbitzuz_kanpo"
    
class Takillak(Base):
    __tablename__ = "takillak"
    
    id_takilla: Mapped[int] = mapped_column(primary_key=True, index=True)
    izena: Mapped[str] = mapped_column(String(200), nullable=False)
    helbidea: Mapped[str] = mapped_column(String(250), nullable=False)
    egoera: Mapped[TakillakEgoeraEnum] = mapped_column(Enum(TakillakEgoeraEnum, name="egoera_takillak", create_type=False), nullable=False)
    
class TakillakIrudiak(Base):
    __tablename__ = "takillak_irudiak"
    
    id_irudi: Mapped[int] = mapped_column(primary_key=True, index=True)
    id_takilla: Mapped[int] = mapped_column(ForeignKey("takillak.id_takilla"), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    
class Postuak(Base):
    __tablename__ = "postuak"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    id_postu: Mapped[int] = mapped_column(ForeignKey("takillak.id_takilla"), nullable=False)
    egoera: Mapped[str] = mapped_column(String(50), nullable=False)
    
class Powerbank(Base):
    __tablename__ = "powerbank"
    
    id_power: Mapped[int] = mapped_column(primary_key=True, index=True)
    id_postu: Mapped[int] = mapped_column(ForeignKey("postuak.id_postu"), nullable=False, unique=True)
    id_takilla: Mapped[int] = mapped_column(ForeignKey("takillak.id_takilla"), nullable=False)
    karga: Mapped[int] = mapped_column(Integer, CheckConstraint("karga >= 0 AND karga <= 100")) 
    
class Erreserbak(Base):
    __tablename__ = "erreserbak"
    
    id_erreserba: Mapped[int] = mapped_column(primary_key=True, index=True)
    id_erab: Mapped[int] = mapped_column(ForeignKey("erabiltzaileak.id_erab"), nullable=False)
    id_power: Mapped[int] = mapped_column(ForeignKey("powerbank.id_power"), nullable=False)
    erreserba_hasiera: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    erreserba_bukaera: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    erabilera_hasiera: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    erabilera_bukaera: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    id_hasiera_takilla: Mapped[int] = mapped_column(ForeignKey("takillak.id_takilla"), nullable=False)
    id_bukaera_takilla: Mapped[int] = mapped_column(ForeignKey("takillak.id_takilla"), nullable=True)
    id_hasiera_postua: Mapped[int] = mapped_column(ForeignKey("postuak.id_postu"), nullable=False)
    id_bukaera_postua: Mapped[int] = mapped_column(ForeignKey("postuak.id_postu"), nullable=True)
    egoera: Mapped[str] = mapped_column(String(50), nullable=False)