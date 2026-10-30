import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import {
  Erreserba,
  ErreserbaEgoera,
  ErreserbaFiltroak,
  ErreserbaSortu,
  Irudia,
  Kargagune,
  KargaguneEgoera,
  KargaguneSortu,
  Postua,
  PostuaEgoera,
  Powerbank,
} from './ereduak';

/** Backend-aren helbidea (behar izanez gero hemen aldatzen da). */
export const API_OINARRIA = 'http://localhost:8000';
const API = `${API_OINARRIA}/alokaziosistema`;

@Injectable({ providedIn: 'root' })
export class PowerbankApi {
  private http = inject(HttpClient);

  // ------------------------------------------------------------- KARGAGUNEAK

  getKargaguneak(bilaketa = '', egoera: KargaguneEgoera | '' = ''): Observable<Kargagune[]> {
    let params = new HttpParams();
    if (bilaketa.trim()) params = params.set('bilaketa', bilaketa.trim());
    if (egoera) params = params.set('egoera', egoera);
    return this.http.get<Kargagune[]>(`${API}/kargaguneak`, { params });
  }

  getKargagunea(id: number): Observable<Kargagune> {
    return this.http.get<Kargagune>(`${API}/kargaguneak/${id}`);
  }

  sortuKargagunea(kargagunea: KargaguneSortu): Observable<Kargagune> {
    return this.http.post<Kargagune>(`${API}/kargaguneak/post`, kargagunea);
  }

  eguneratuKargagunea(id: number, kargagunea: Partial<KargaguneSortu>): Observable<Kargagune> {
    return this.http.patch<Kargagune>(`${API}/kargaguneak/${id}/eguneratu`, kargagunea);
  }

  desaktibatuKargagunea(id: number): Observable<Kargagune> {
    return this.http.patch<Kargagune>(`${API}/kargaguneak/${id}/desaktibatu`, {});
  }

  ezabatuKargagunea(id: number): Observable<{ message: string }> {
    return this.http.delete<{ message: string }>(`${API}/kargaguneak/${id}/ezabatu`);
  }

  gehituIrudia(id: number, url: string): Observable<Irudia> {
    return this.http.post<Irudia>(`${API}/kargaguneak/${id}/irudiak`, { url });
  }

  igoIrudia(id: number, fitxategia: File): Observable<Irudia> {
    const datuak = new FormData();
    datuak.append('fitxategia', fitxategia);
    return this.http.post<Irudia>(`${API}/kargaguneak/${id}/irudiak/igo`, datuak);
  }

  ezabatuIrudia(id: number, idIrudia: number): Observable<{ message: string }> {
    return this.http.delete<{ message: string }>(
      `${API}/kargaguneak/${id}/irudiak/${idIrudia}`,
    );
  }

  // ------------------------------------------------------------- KARGA-POSTUAK

  getPostuak(idTakilla?: number): Observable<Postua[]> {
    let params = new HttpParams();
    if (idTakilla) params = params.set('id_takilla', idTakilla);
    return this.http.get<Postua[]>(`${API}/postuak`, { params });
  }

  sortuPostua(idTakilla: number, egoera: PostuaEgoera): Observable<Postua> {
    return this.http.post<Postua>(`${API}/postuak/post`, {
      id_takilla: idTakilla,
      egoera,
    });
  }

  eguneratuPostua(id: number, datuak: { egoera?: PostuaEgoera }): Observable<Postua> {
    return this.http.patch<Postua>(`${API}/postuak/${id}/eguneratu`, datuak);
  }

  ezabatuPostua(id: number): Observable<{ message: string }> {
    return this.http.delete<{ message: string }>(`${API}/postuak/${id}/ezabatu`);
  }

  // ------------------------------------------------------------- POWERBANKAK

  getPowerbankak(idTakilla?: number): Observable<Powerbank[]> {
    let params = new HttpParams();
    if (idTakilla) params = params.set('id_takilla', idTakilla);
    return this.http.get<Powerbank[]>(`${API}/powerbanks`, { params });
  }

  // ------------------------------------------------------------- ERRESERBAK

  getErreserbak(filtroak: ErreserbaFiltroak = {}): Observable<Erreserba[]> {
    let params = new HttpParams();
    Object.entries(filtroak).forEach(([gakoa, balioa]) => {
      if (balioa !== undefined && balioa !== null && balioa !== '') {
        params = params.set(gakoa, String(balioa));
      }
    });
    return this.http.get<Erreserba[]>(`${API}/erreserbak/zerrenda`, { params });
  }

  sortuErreserba(erreserba: ErreserbaSortu): Observable<Erreserba> {
    return this.http.post<Erreserba>(`${API}/erreserbak/post`, erreserba);
  }

  ezeztatuErreserba(id: number): Observable<Erreserba> {
    // Administrazio-atalea denez, administratzaileak edozein erreserba kudea dezake
    const params = new HttpParams().set('admin', 'true');
    return this.http.patch<Erreserba>(`${API}/erreserbak/${id}/ezeztatu`, {}, { params });
  }

  aldatuErreserbaEgoera(id: number, egoera: ErreserbaEgoera): Observable<Erreserba> {
    const params = new HttpParams().set('admin', 'true');
    return this.http.patch<Erreserba>(
      `${API}/erreserbak/${id}/egoera`,
      { egoera },
      { params },
    );
  }
}
