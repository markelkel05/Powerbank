import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { ErabiltzaileCreate, ErabiltzaileResponse } from './erabiltzaile-interface';

@Injectable({
    providedIn: 'root'
})

export class ApiDeiak {

    constructor(private http: HttpClient) { }

    getInfoErabiltzaileak(): Observable<ErabiltzaileResponse[]> {
        const url = `http://localhost:8000/alokaziosistema/erabiltzaileak`;
        return this.http.get<ErabiltzaileResponse[]>(url);
    }

    editatuErabiltzaileak(id: number, erabiltzaile: ErabiltzaileCreate): Observable<ErabiltzaileResponse> {
        const url = `http://localhost:8000/alokaziosistema/erabiltzaileak/${id}/eguneratu`;
        return this.http.put<ErabiltzaileResponse>(url, erabiltzaile);
    }

    ezabatuErabiltzailea(id: number): Observable<void> {
        const url = `http://localhost:8000/alokaziosistema/erabiltzaileak/${id}/ezabatu`;
        return this.http.delete<void>(url);
    }

    gordeErabiltzailea(erabiltzaile: ErabiltzaileCreate): Observable<ErabiltzaileResponse> {
        const url = `http://localhost:8000/alokaziosistema/erabiltzaileak/post`;
        return this.http.post<ErabiltzaileResponse>(url, erabiltzaile);
    }

    desaktibatuErabiltzailea(id: number): Observable<ErabiltzaileResponse> {
        const url = `http://localhost:8000/alokaziosistema/erabiltzaileak/${id}/desaktibatu`;
        return this.http.put<ErabiltzaileResponse>(url, {});
    }
}