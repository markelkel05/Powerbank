import enum
from datetime import datetime

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
from sqlalchemy.orm import Mapped, mapped_column, relationship


# ---------------------------------------------------------------------------
# ERABILTZAILEAK
# ---------------------------------------------------------------------------


class Rol(Base):
    __tablename__ = "rolak"

    id_rol: Mapped[int] = mapped_column(primary_key=True, index=True)
    # DATU BASEA (Urkoren dump-a): zutabearen izena "rol_izena" da
    rol_izena: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)

    erabiltzaileak: Mapped[list["Erabiltzaileak"]] = relationship(back_populates="rola")


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
    activo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )

    rola: Mapped["Rol"] = relationship(back_populates="erabiltzaileak")
    erreserbak: Mapped[list["Erreserbak"]] = relationship(
        back_populates="erabiltzailea", foreign_keys="Erreserbak.id_erab"
    )


# ---------------------------------------------------------------------------
# KARGAGUNEAK (takillak) ETA KARGA-POSTUAK (postuak)
# ---------------------------------------------------------------------------


class TakillakEgoeraEnum(str, enum.Enum):
    """Kargagunearen egoera."""

    erabilgarri = "erabilgarri"
    mantentze_lanetan = "mantentze_lanetan"
    zerbitzuz_kanpo = "zerbitzuz_kanpo"


class PostuakEgoeraEnum(str, enum.Enum):
    """Karga-postuaren egoera."""

    hutsa = "hutsa"
    kargatuta = "kargatuta"
    kargatzen = "kargatzen"


class Takillak(Base):
    __tablename__ = "takillak"

    id_takilla: Mapped[int] = mapped_column(primary_key=True, index=True)
    izena: Mapped[str] = mapped_column(String(200), nullable=False)
    helbidea: Mapped[str] = mapped_column(String(250), nullable=False)
    egoera: Mapped[TakillakEgoeraEnum] = mapped_column(
        Enum(
            TakillakEgoeraEnum,
            name="egoera_takillak",
            create_type=False,
            values_callable=lambda enum_cls: [elem.value for elem in enum_cls],
        ),
        nullable=False,
        default=TakillakEgoeraEnum.erabilgarri,
    )

    irudiak: Mapped[list["TakillakIrudiak"]] = relationship(
        back_populates="takilla", cascade="all, delete-orphan"
    )
    postuak: Mapped[list["Postuak"]] = relationship(back_populates="takilla")


class TakillakIrudiak(Base):
    __tablename__ = "takillak_irudiak"

    id_irudi: Mapped[int] = mapped_column(primary_key=True, index=True)
    id_takilla: Mapped[int] = mapped_column(
        ForeignKey("takillak.id_takilla"), nullable=False
    )
    url: Mapped[str] = mapped_column(String(500), nullable=False)

    takilla: Mapped["Takillak"] = relationship(back_populates="irudiak")


class Postuak(Base):
    __tablename__ = "postuak"

    id_postu: Mapped[int] = mapped_column(primary_key=True, index=True)
    id_takilla: Mapped[int] = mapped_column(
        ForeignKey("takillak.id_takilla"), nullable=False
    )
    egoera: Mapped[PostuakEgoeraEnum] = mapped_column(
        Enum(
            PostuakEgoeraEnum,
            name="egoera_postuak",
            create_type=False,
            values_callable=lambda enum_cls: [elem.value for elem in enum_cls],
        ),
        nullable=False,
        default=PostuakEgoeraEnum.hutsa,
    )

    takilla: Mapped["Takillak"] = relationship(back_populates="postuak")
    powerbank: Mapped["Powerbank | None"] = relationship(
        back_populates="postua", foreign_keys="Powerbank.id_postu", uselist=False
    )


# ---------------------------------------------------------------------------
# POWERBANK-AK
# ---------------------------------------------------------------------------


class Powerbank(Base):
    __tablename__ = "powerbank"
    __table_args__ = (
        CheckConstraint("karga >= 0 AND karga <= 100", name="powerbank_karga_check"),
    )

    id_power: Mapped[int] = mapped_column(primary_key=True, index=True)
    id_postu: Mapped[int | None] = mapped_column(
        ForeignKey("postuak.id_postu"), nullable=True, unique=True
    )
    karga: Mapped[int] = mapped_column(Integer, nullable=False)
    id_takilla: Mapped[int | None] = mapped_column(
        ForeignKey("takillak.id_takilla"), nullable=True
    )

    postua: Mapped["Postuak | None"] = relationship(
        back_populates="powerbank", foreign_keys=[id_postu]
    )
    takilla: Mapped["Takillak | None"] = relationship(foreign_keys=[id_takilla])


# ---------------------------------------------------------------------------
# ERRESERBAK
# ---------------------------------------------------------------------------


class ErreserbakEgoeraEnum(str, enum.Enum):
    aktiboa = "aktiboa"
    ezeztatuta = "ezeztatuta"
    amaituta = "amaituta"


class Erreserbak(Base):
    __tablename__ = "erreserbak"

    id_erreserba: Mapped[int] = mapped_column(primary_key=True, index=True)
    id_erab: Mapped[int] = mapped_column(
        ForeignKey("erabiltzaileak.id_erab"), nullable=False
    )
    id_power: Mapped[int] = mapped_column(
        ForeignKey("powerbank.id_power"), nullable=False
    )
    erreserba_hasiera: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    erreserba_bukaera: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    erabilera_hasiera: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    erabilera_bukaera: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    id_hasiera_takilla: Mapped[int] = mapped_column(
        ForeignKey("takillak.id_takilla"), nullable=False
    )
    id_bukaera_takilla: Mapped[int | None] = mapped_column(
        ForeignKey("takillak.id_takilla"), nullable=True
    )
    id_hasiera_postua: Mapped[int] = mapped_column(
        ForeignKey("postuak.id_postu"), nullable=False
    )
    id_bukaera_postua: Mapped[int | None] = mapped_column(
        ForeignKey("postuak.id_postu"), nullable=True
    )
    egoera: Mapped[ErreserbakEgoeraEnum] = mapped_column(
        Enum(
            ErreserbakEgoeraEnum,
            name="egoera_erreserba",
            create_type=False,
            values_callable=lambda enum_cls: [elem.value for elem in enum_cls],
        ),
        nullable=False,
        default=ErreserbakEgoeraEnum.aktiboa,
        server_default="aktiboa",
    )

    erabiltzailea: Mapped["Erabiltzaileak"] = relationship(
        back_populates="erreserbak", foreign_keys=[id_erab]
    )
    powerbank: Mapped["Powerbank"] = relationship(foreign_keys=[id_power])
    hasiera_takilla: Mapped["Takillak"] = relationship(
        foreign_keys=[id_hasiera_takilla]
    )
    bukaera_takilla: Mapped["Takillak | None"] = relationship(
        foreign_keys=[id_bukaera_takilla]
    )
    hasiera_postua: Mapped["Postuak"] = relationship(
        foreign_keys=[id_hasiera_postua]
    )
    bukaera_postua: Mapped["Postuak | None"] = relationship(
        foreign_keys=[id_bukaera_postua]
    )
