from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# ERABILTZAILEEN ESKEMAK

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

# Erabiltzaile bat sortzeko (datu basean gordetzeko eskema)
class CreateErabiltzaile(BaseModel):
    nan: str = Field(min_length=9, max_length=9)
    izena: str = Field(min_length=2)
    abizenak: str = Field(min_length=2)
    email: str = Field(max_length=200)
    pasahitza: str = Field(min_length=6)
    helbidea: str = Field(min_length=5)
    id_rol: int = Field(ge=1, le=2)

class PatchErabiltzaile(BaseModel):
    nan: str | None = Field(default=None, min_length=9, max_length=9)
    izena: str | None = Field(default=None,min_length=2)
    abizenak: str | None = Field(default=None,min_length=2)
    email: str | None = Field(default=None,max_length=200)
    pasahitza: str | None = Field(default=None,min_length=6)
    helbidea: str | None = Field(default=None,min_length=5)
    id_rol: int | None = Field(default=None,ge=1, le=2)
    activo: bool | None = Field(default=None)

    
# ERRESERBEN ESKEMAK

# Erreserbak listatzeko
class ListErreserbak(BaseModel):
    id: int
    id_erab: int
    id_power: int
    erreserba_hasiera: str = Field(min_length=6)
    erreserba_bukaera: str = Field(min_lenght=6)
    erabilera_hasiera: str = Field(min_lenght=6)
    erabilera_bukaera: str = Field(min_lenght=6)
    id_hasiera_takilla: int = Field(min_lenght=6)
    id_bukaera_takilla: int = Field(min_lenght=6)
    id_hasiera_postua: int = Field(min_lenght=6)
    id_bukaera_postua: int = Field(min_lenght=6)
    egoera: str = Field(max_lenght=20)
    
# Erabiltzaile batek erreserba bat sortzeko (datu basean gordetzeko)
class CreateErreserba(BaseModel):
    id_erab: int
    id_power: int
    erreserba_hasiera: str = Field(min_length=6)
    erreserba_bukaera: str = Field(min_lenght=6)
    erabilera_hasiera: str = Field(min_lenght=6)
    erabilera_bukaera: str = Field(min_lenght=6)
    id_hasiera_takilla: int = Field(min_lenght=6)
    id_bukaera_takilla: int = Field(min_lenght=6)
    id_hasiera_postua: int = Field(min_lenght=6)
    id_bukaera_postua: int = Field(min_lenght=6)
    egoera: str = Field(max_lenght=20)

# POWERBANK-AK

#Powerbank-ak listatzeko (bakoitza non dagoen jakiteko)
class ListPowerbank(BaseModel):
    id_power: int
    id_takilla: int
    id_postu: int
    karga: int = Field(ge=0, le= 100)
    
# Powerbank sortzeko 
class CreatePowerbank(BaseModel):
    id_takilla: int
    id_postu: int
    karga: int = Field(ge=0, le= 100)
    
class PowerbankTokiaPatch(BaseModel):
    id_takilla: int | None = Field(default=None)
    id_postu: int | None = Field(default=None)
    
########################### ERRESERBAK-AK###########################
    


class ErreserbaCreate(BaseModel):
    id_power: int
    erreserba_hasiera: datetime
    erreserba_bukaera: datetime
    id_hasiera_takilla: int
    id_hasiera_postua: int


class ErreserbaResponse(ErreserbaCreate):
    id_erreserba: int
    id_erab: int
    egoera: str

    model_config =  ConfigDict(from_attributes=True)
    
    
############### KARGAGUNEAK ###############

# Takillak sortu
class CreateTakilla(BaseModel):
    izena: str = Field(min_length=2, max_length=100)
    helbidea: str = Field(min_length=3, max_length=200)
    egoera: str = Field(max_length=20)
    
class PatchTakilla(BaseModel):
    izena: str | None = Field(default=None, min_length=2, max_length=100)
    helbidea: str | None = Field(default=None,min_length=3, max_length=200)
    egoera: str | None = Field(default=None,max_length=20)
    
class TakillaResponse(BaseModel):
    id_takilla: int
    izena: str = Field(min_length=2, max_length=100)
    helbidea: str = Field(min_length=3, max_length=200)
    egoera: str = Field(max_length=20)
    
class TakillaIrudiaCreate(BaseModel):
    url: str = Field(max_length=500)

