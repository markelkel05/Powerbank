export interface ErabiltzaileResponse {
  id_erab: number;
  nan: string;
  izena: string;
  abizenak: string;
  email: string;
  pasahitza: string;
  helbidea: string;
  id_rol: number;
  activo: boolean;
}

export interface ErabiltzaileCreate {
  nan: string;
  izena: string;
  abizenak: string;
  email: string;
  pasahitza: string;
  helbidea: string;
  id_rol: number;
  activo: boolean;
}