import { Component, OnInit, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AgGridAngular } from 'ag-grid-angular';
import {
  ColDef,
  ModuleRegistry,
  AllCommunityModule,
  GridReadyEvent,
  SelectionChangedEvent
} from 'ag-grid-community';
import { HttpClient } from '@angular/common/http';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatFormFieldModule } from '@angular/material/form-field';
import { ApiDeiak } from './api-deiak';
import { ErabiltzaileCreate, ErabiltzaileResponse } from './erabiltzaile-interface';

ModuleRegistry.registerModules([AllCommunityModule]);


@Component({
  selector: 'app-erabiltzaileak-component',
  standalone: true,
  imports: [CommonModule, AgGridAngular, FormsModule, MatFormFieldModule, MatSelectModule, MatInputModule],
  templateUrl: './erabiltzaileak-component.html',
  styleUrl: './erabiltzaileak-component.css'
})


export class ErabiltzaileakComponent implements OnInit {
  private apiService = inject(ApiDeiak);

  errepikatuPasahitza = '';
  newUser: ErabiltzaileCreate = this.emptyUser();
  gordetzen = signal(false);
  gordetzeErrorea = signal<string | null>(null);

  constructor(private http: HttpClient) { }

  erabiltzaileak = signal<ErabiltzaileResponse[]>([]);
  formulario = signal<boolean>(false);

  ngOnInit(): void {
    this.lortuInfoErabiltzaileak();
  }

  datuBaseanGordeErabiltzailea(erabiltzaile: ErabiltzaileCreate): void {
    this.gordetzen.set(true);
    this.gordetzeErrorea.set(null);

    this.apiService.gordeErabiltzailea(erabiltzaile).subscribe({
      next: (res) => {
        this.erabiltzaileak.update(list => [...list, res]);
        this.gordetzen.set(false);
        this.closeForm();
      },
      error: (err) => {
        const msg = err?.error?.detail;
        this.gordetzeErrorea.set(
          typeof msg === 'string' ? msg : 'Ezin izan da erabiltzailea gorde.'
        );
        this.gordetzen.set(false);
      }
    });
  }

  onSubmit(): void {
    if (this.gordetzen()) {
      return;
    }

    if (this.newUser.pasahitza !== this.errepikatuPasahitza) {
      this.gordetzeErrorea.set('Pasahitzak ez datoz bat.');
      return;
    }

    this.datuBaseanGordeErabiltzailea({ ...this.newUser });
  }

  lortuInfoErabiltzaileak(): void {
    this.apiService.getInfoErabiltzaileak().subscribe({
      next: (res: ErabiltzaileResponse[]) => {
        this.erabiltzaileak.set(res);
      },
      error: (err) => {
        console.error('Errorea erabiltzaileak kargatzean:', err);
      }
    });
  }

  onEditUser(erabiltzaile: ErabiltzaileResponse): void {
    this.openForm();
    const aldatutakoDatuak: ErabiltzaileCreate = { ...erabiltzaile, izena: erabiltzaile.izena + ' (Eguneratuta)' };

    this.apiService.editatuErabiltzaileak(erabiltzaile.id_erab, aldatutakoDatuak).subscribe({
      next: (res: ErabiltzaileResponse) => {
        this.erabiltzaileak.update(zerrenda =>
          zerrenda.map(item => item.id_erab === res.id_erab ? res : item)
        );
      },
      error: (err) => {
        console.error('Errorea erabiltzailea eguneratzean:', err);
      }
    });
  }

  onDeleteUser(erabiltzaile: ErabiltzaileResponse): void {
    if (confirm(`${erabiltzaile.izena} ezabatu nahi duzu?`)) {
      this.apiService.ezabatuErabiltzailea(erabiltzaile.id_erab).subscribe({
        next: () => {
          this.erabiltzaileak.update(zerrenda =>
            zerrenda.filter(item => item.id_erab !== erabiltzaile.id_erab)
          );
        },
        error: (err) => {
          console.error('Errorea erabiltzailea ezabatzean:', err);
        }
      });
    }
  }

  onDesaktibatuUser(erabiltzaile: ErabiltzaileResponse): void {
    const aldatutakoDatuak: ErabiltzaileCreate = { ...erabiltzaile, activo: false };

    this.apiService.editatuErabiltzaileak(erabiltzaile.id_erab, aldatutakoDatuak).subscribe({
      next: (res: ErabiltzaileResponse) => {
        this.erabiltzaileak.update(zerrenda =>
          zerrenda.map(item => item.id_erab === res.id_erab ? res : item)
        );
      },
      error: (err) => {
        console.error('Errorea erabiltzailea desaktibatzean:', err);
      }
    });
  }

  openForm(): void {
    this.newUser = this.emptyUser();
    this.errepikatuPasahitza = '';
    this.gordetzeErrorea.set(null);
    this.formulario.set(true);
  }

  closeForm(): void {
    this.formulario.set(false);
  }

  private emptyUser(): ErabiltzaileCreate {
    return {
      nan: '',
      izena: '',
      abizenak: '',
      email: '',
      pasahitza: '',
      helbidea: '',
      id_rol: 2,
      activo: true
    };
  }


  colDefs: ColDef<ErabiltzaileResponse>[] = [
    { field: 'id_erab', headerName: 'ID', width: 90, flex: 0 },
    { field: 'nan', headerName: 'NAN', filter: 'agTextColumnFilter' },
    { field: 'izena', headerName: 'IZENA' },
    { field: 'abizenak', headerName: 'ABIZENAK' },
    { field: 'email', headerName: 'EMAIL' },
    { field: 'pasahitza', headerName: 'PASAHITZA' },
    { field: 'helbidea', headerName: 'HELBIDEA' },
    { field: 'id_rol', headerName: 'ROL ID' },
    { field: 'activo', headerName: 'AKTIBO' },
    {
      headerName: 'Akzioak',
      field: 'id_erab',
      width: 200,
      flex: 0,
      sortable: false,
      filter: false,
      cellRenderer: (params: any) => {
        const container = document.createElement('div');
        container.className = 'd-flex gap-2 align-items-center h-100';

        const btnEdit = document.createElement('button');
        btnEdit.className = 'btn btn-success btn-sm';
        const icon = document.createElement('i');
        icon.className = 'bi bi-pencil';
        btnEdit.appendChild(icon);
        btnEdit.addEventListener('click', () => {
          this.onEditUser(params.data);
        });

        const btnDelete = document.createElement('button');
        btnDelete.className = 'btn btn-danger btn-sm';
        const deleteIcon = document.createElement('i');
        deleteIcon.className = 'bi bi-trash';
        btnDelete.appendChild(deleteIcon);
        btnDelete.addEventListener('click', () => {
          this.onDeleteUser(params.data);
        });

        const btnDesaktibatu = document.createElement('button');
        btnDesaktibatu.className = 'btn btn-warning btn-sm';
        const desaktibatuIcon = document.createElement('i');
        desaktibatuIcon.className = 'bi bi-x-circle';
        btnDesaktibatu.appendChild(desaktibatuIcon);
        btnDesaktibatu.addEventListener('click', () => {
          this.onDesaktibatuUser(params.data);
        });

        container.appendChild(btnEdit);
        container.appendChild(btnDelete);
        container.appendChild(btnDesaktibatu);

        return container;
      }
    }
  ];

  defaultColDef: ColDef = {
    flex: 1,
    filter: true,
    sortable: true,
    resizable: true
  };

  pagination = true;
  paginationPageSize = 5;
  paginationPageSizeSelector: number[] | boolean = [5, 10, 20];

  onGridReady(params: GridReadyEvent): void {
    console.log('AG Grid is ready');
  }

  onSelectionChanged(event: SelectionChangedEvent): void {
    const selectedRows = event.api.getSelectedRows();
    console.log('Selected rows:', selectedRows);
  }
}