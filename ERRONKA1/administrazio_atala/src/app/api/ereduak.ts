// Backend-etik datozen datuen tipoak (Pydantic eskemen isla)

export type KargaguneEgoera = 'erabilgarri' | 'mantentze_lanetan' | 'zerbitzuz_kanpo';
export type PostuaEgoera = 'hutsa' | 'kargatuta' | 'kargatzen';
export type ErreserbaEgoera = 'aktiboa' | 'ezeztatuta' | 'amaituta';

export interface Powerbank {
  id_power: number;
  id_takilla: number | null;
  id_postu: number | null;
  karga: number;
}

export interface Postua {
  id_postu: number;
  id_takilla: number;
  egoera: PostuaEgoera;
  libre: boolean;
  powerbank: Powerbank | null;
}

export interface Kargagune {
  id_takilla: number;
  izena: string;
  helbidea: string;
  egoera: KargaguneEgoera;
  irudiak: string[];
  postuak_kopurua: number;
  powerbank_kopurua: number;
  erreserba_aktiboak: number;
  postuak?: Postua[];
  irudien_xehetasuna?: Irudia[];
}

export interface KargaguneSortu {
  izena: string;
  helbidea: string;
  egoera: KargaguneEgoera;
}

export interface Irudia {
  id_irudi: number;
  id_takilla: number;
  url: string;
}

export interface Erreserba {
  id_erreserba: number;
  id_erab: number;
  id_power: number;
  erreserba_hasiera: string;
  erreserba_bukaera: string;
  id_hasiera_takilla: number;
  id_hasiera_postua: number;
  egoera: ErreserbaEgoera;
  erabiltzaile_izena: string;
  erabiltzaile_email: string;
  kargagune_izena: string;
  kargagune_helbidea: string;
  powerbank_karga: number;
  bukaera_kargagune_izena: string | null;
  erabilera_hasiera: string | null;
  erabilera_bukaera: string | null;
}

export interface ErreserbaSortu {
  id_erab: number;
  id_power: number;
  erreserba_hasiera: string;
  erreserba_bukaera: string;
  id_hasiera_takilla: number;
  id_hasiera_postua: number;
}

export interface ErreserbaFiltroak {
  id_erab?: number;
  id_takilla?: number;
  id_power?: number;
  hasiera?: string;
  bukaera?: string;
  egoera?: ErreserbaEgoera;
}
