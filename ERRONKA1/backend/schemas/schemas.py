from datetime import datetime

from models.models import (
    ErreserbakEgoeraEnum,
    PostuakEgoeraEnum,
    TakillakEgoeraEnum,
)
from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# ERABILTZAILEEN ESKEMAK
# ---------------------------------------------------------------------------


# Erabiltzailearen Login-a egiteko
class ErabiltzaileLogin(BaseModel):
    email: str
    pasahitza: str


# Erabiltzaileak zerrendatzeko (taula, zerrenda bat...)
class ListErabiltzaileak(BaseModel):
    id_erab: int
    nan: str = Field(min_length=9, max_length=9)
    izena: str = Field(min_length=2)
    abizenak: str = Field(min_length=2)
    email: str = Field(max_length=200)
    pasahitza: str = Field(min_length=3)
    helbidea: str = Field(min_length=5)
    id_rol: int = Field(ge=1, le=2)
    activo: bool = Field(default=True)

    model_config = ConfigDict(from_attributes=True)


# Atal publikotik norberak erregistratzeko (rola beti 2 = erabiltzaile arrunta)
class Erregistroa(BaseModel):
    nan: str = Field(min_length=9, max_length=9)
    izena: str = Field(min_length=2)
    abizenak: str = Field(min_length=2)
    email: str = Field(max_length=200)
    pasahitza: str = Field(min_length=6)
    helbidea: str = Field(min_length=5)


# Erabiltzaile bat sortzeko (datu basean gordetzeko eskema)
class CreateErabiltzaile(BaseModel):
    nan: str = Field(min_length=9, max_length=9)
    izena: str = Field(min_length=2)
    abizenak: str = Field(min_length=2)
    email: str = Field(max_length=200)
    pasahitza: str = Field(min_length=6)
    helbidea: str = Field(min_length=5)
    id_rol: int = Field(ge=1, le=2)


# Atal publikorako erabiltzailearen datuak (pasahitza EZ da inoiz bidaltzen)
class ErabiltzaileSegurua(BaseModel):
    id_erab: int
    nan: str
    izena: str
    abizenak: str
    email: str
    helbidea: str
    id_rol: int
    activo: bool = True

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    erabiltzailea: ErabiltzaileSegurua


class PatchErabiltzaile(BaseModel):
    nan: str | None = Field(default=None, min_length=9, max_length=9)
    izena: str | None = Field(default=None, min_length=2)
    abizenak: str | None = Field(default=None, min_length=2)
    email: str | None = Field(default=None, max_length=200)
    pasahitza: str | None = Field(default=None, min_length=6)
    helbidea: str | None = Field(default=None, min_length=5)
    id_rol: int | None = Field(default=None, ge=1, le=2)
    activo: bool | None = Field(default=None)


# ---------------------------------------------------------------------------
# ERRESERBEN ESKEMAK
# ---------------------------------------------------------------------------


# Erreserbak listatzeko (taula hutsa, erlazioak gabe)
class ListErreserbak(BaseModel):
    id_erreserba: int
    id_erab: int
    id_power: int
    erreserba_hasiera: datetime
    erreserba_bukaera: datetime
    erabilera_hasiera: datetime | None = None
    erabilera_bukaera: datetime | None = None
    id_hasiera_takilla: int
    id_bukaera_takilla: int | None = None
    id_hasiera_postua: int
    id_bukaera_postua: int | None = None
    egoera: ErreserbakEgoeraEnum

    model_config = ConfigDict(from_attributes=True)


# Erabiltzaile batek erreserba bat sortzeko (datu basean gordetzeko)
class CreateErreserba(BaseModel):
    id_erab: int
    id_power: int
    erreserba_hasiera: datetime
    erreserba_bukaera: datetime
    erabilera_hasiera: datetime | None = None
    erabilera_bukaera: datetime | None = None
    id_hasiera_takilla: int
    id_bukaera_takilla: int | None = None
    id_hasiera_postua: int
    id_bukaera_postua: int | None = None
    egoera: ErreserbakEgoeraEnum = ErreserbakEgoeraEnum.aktiboa


# Erreserba bat sortzeko (endpoint zaharra, bateragarritasuneralko)
# TODO: atal publikoa /erreserbak/post erabiltzen hasi behar da.
class ErreserbaCreate(BaseModel):
    id_power: int
    erreserba_hasiera: datetime
    erreserba_bukaera: datetime
    id_hasiera_takilla: int
    id_hasiera_postua: int


# Administrazio-atalean / atal publikoan erreserba berria egiteko
class ErreserbaSortu(BaseModel):
    id_erab: int
    id_power: int
    erreserba_hasiera: datetime
    erreserba_bukaera: datetime
    id_hasiera_takilla: int
    id_hasiera_postua: int


# Erreserba baten datuak aldatzeko (data edo postua)
class ErreserbaEguneratu(BaseModel):
    id_power: int | None = None
    erreserba_hasiera: datetime | None = None
    erreserba_bukaera: datetime | None = None
    id_hasiera_takilla: int | None = None
    id_hasiera_postua: int | None = None


class ErreserbaEgoeraPatch(BaseModel):
    egoera: ErreserbakEgoeraEnum


# Powerbank-a hartu / bueltatu denean markatzeko
class ErreserbaErabileraPatch(BaseModel):
    erabilera_hasiera: datetime | None = None
    erabilera_bukaera: datetime | None = None
    id_bukaera_takilla: int | None = None
    id_bukaera_postua: int | None = None


class ErreserbaResponse(BaseModel):
    id_erreserba: int
    id_erab: int
    id_power: int
    erreserba_hasiera: datetime
    erreserba_bukaera: datetime
    id_hasiera_takilla: int
    id_hasiera_postua: int
    egoera: ErreserbakEgoeraEnum

    model_config = ConfigDict(from_attributes=True)


# Administrazio-taulako erreserba erlazioekin (erabiltzailearen izena, kargagunea...)
class ErreserbaXehetasuna(ErreserbaResponse):
    erabiltzaile_izena: str
    erabiltzaile_email: str
    kargagune_izena: str
    kargagune_helbidea: str
    powerbank_karga: int
    bukaera_kargagune_izena: str | None = None
    erabilera_hasiera: datetime | None = None
    erabilera_bukaera: datetime | None = None


# ---------------------------------------------------------------------------
# POWERBANK-AK
# ---------------------------------------------------------------------------


# Powerbank-ak listatzeko (bakoitza non dagoen jakiteko)
class ListPowerbank(BaseModel):
    id_power: int
    id_takilla: int | None = None
    id_postu: int | None = None
    karga: int = Field(ge=0, le=100)

    model_config = ConfigDict(from_attributes=True)


# Powerbank sortzeko
class CreatePowerbank(BaseModel):
    id_takilla: int | None = None
    id_postu: int | None = None
    karga: int = Field(ge=0, le=100)


class PowerbankTokiaPatch(BaseModel):
    id_takilla: int | None = Field(default=None)
    id_postu: int | None = Field(default=None)


# ---------------------------------------------------------------------------
# KARGAGUNEAK (takillak)
# ---------------------------------------------------------------------------


class CreateTakilla(BaseModel):
    """Kargagune berria sortzeko."""

    izena: str = Field(min_length=2, max_length=200)
    helbidea: str = Field(min_length=3, max_length=250)
    egoera: TakillakEgoeraEnum = TakillakEgoeraEnum.erabilgarri


class PatchTakilla(BaseModel):
    izena: str | None = Field(default=None, min_length=2, max_length=200)
    helbidea: str | None = Field(default=None, min_length=3, max_length=250)
    egoera: TakillakEgoeraEnum | None = Field(default=None)


class TakillaResponse(BaseModel):
    id_takilla: int
    izena: str = Field(min_length=2, max_length=200)
    helbidea: str = Field(min_length=3, max_length=250)
    egoera: TakillakEgoeraEnum

    model_config = ConfigDict(from_attributes=True)


class KargaguneResponse(TakillaResponse):
    """Kargagunea, taulan erakusteko informazio gehiagorekin."""

    irudiak: list[str] = Field(default_factory=list)
    postuak_kopurua: int = 0
    postu_libreak: int = 0
    powerbank_kopurua: int = 0
    erreserba_aktiboak: int = 0


class TakillaIrudiaCreate(BaseModel):
    url: str = Field(min_length=3, max_length=500)


class TakillaIrudiaUpdate(BaseModel):
    url: str | None = Field(default=None, min_length=3, max_length=500)


class TakillaIrudiaResponse(BaseModel):
    id_irudi: int
    id_takilla: int
    url: str

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# KARGA-POSTUAK (postuak)
# ---------------------------------------------------------------------------


class PowerbankLaburra(BaseModel):
    id_power: int
    karga: int
    id_postu: int | None = None
    id_takilla: int | None = None

    model_config = ConfigDict(from_attributes=True)


class PostuaResponse(BaseModel):
    id_postu: int
    id_takilla: int
    egoera: PostuakEgoeraEnum
    libre: bool = True
    powerbank: PowerbankLaburra | None = None

    model_config = ConfigDict(from_attributes=True)


class KargaguneXehetasuna(KargaguneResponse):
    postuak: list[PostuaResponse] = Field(default_factory=list)
    irudien_xehetasuna: list[TakillaIrudiaResponse] = Field(default_factory=list)


class PostuaSortu(BaseModel):
    id_takilla: int
    egoera: PostuakEgoeraEnum = PostuakEgoeraEnum.hutsa


class PostuaEguneratu(BaseModel):
    id_takilla: int | None = None
    egoera: PostuakEgoeraEnum | None = None
