import { CommonModule } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AgGridAngular } from 'ag-grid-angular';
import { AllCommunityModule, ColDef, ModuleRegistry } from 'ag-grid-community';
import { ApiDeiak } from '../erabiltzaileak-component/api-deiak';
import { ErabiltzaileResponse } from '../erabiltzaileak-component/erabiltzaile-interface';
import { PowerbankApi } from '../api/powerbank-api';
import {
  Erreserba,
  ErreserbaEgoera,
  ErreserbaFiltroak,
  Kargagune,
  Postua,
  Powerbank,
} from '../api/ereduak';

ModuleRegistry.registerModules([AllCommunityModule]);

@Component({
  selector: 'app-erreserbak',
  standalone: true,
  imports: [CommonModule, FormsModule, AgGridAngular],
  templateUrl: './erreserbak-component.html',
  styleUrl: './erreserbak-component.css',
})
export class ErreserbakComponent implements OnInit {
  private api = inject(PowerbankApi);
  private erabiltzaileApi = inject(ApiDeiak);

  erreserbak = signal<Erreserba[]>([]);
  erabiltzaileak = signal<ErabiltzaileResponse[]>([]);
  kargaguneak = signal<Kargagune[]>([]);
  powerbankak = signal<Powerbank[]>([]);

  mezua = signal<string | null>(null);
  errorea = signal<string | null>(null);

  filtroak: {
    id_erab: number | '';
    id_takilla: number | '';
    id_power: number | '';
    egoera: ErreserbaEgoera | '';
    hasiera: string;
    bukaera: string;
  } = {
    id_erab: '',
    id_takilla: '',
    id_power: '',
    egoera: '',
    hasiera: '',
    bukaera: '',
  };

  // Erreserba berriaren formularioa
  formularioa = signal(false);
  gordetzen = signal(false);
  form = {
    id_erab: null as number | null,
    id_hasiera_takilla: null as number | null,
    id_hasiera_postua: null as number | null,
    id_power: null as number | null,
    hasiera: '',
    bukaera: '',
  };
  formPostuak = signal<Postua[]>([]);
  formPowerbankak = signal<Powerbank[]>([]);

  readonly egoerak: { balioa: ErreserbaEgoera; izena: string }[] = [
    { balioa: 'aktiboa', izena: 'Aktiboa' },
    { balioa: 'ezeztatuta', izena: 'Ezeztatuta' },
    { balioa: 'amaituta', izena: 'Amaituta' },
  ];

  ngOnInit(): void {
    this.kargatu();
    this.kargatuLagungarriak();
  }

  // ------------------------------------------------------------ datuak

  private kargatuLagungarriak(): void {
    this.erabiltzaileApi.getInfoErabiltzaileak().subscribe({
      next: (erabiltzaileak) => this.erabiltzaileak.set(erabiltzaileak),
      error: (err) => this.errorea.set(this.erroreMezua(err)),
    });

    this.api.getKargaguneak().subscribe({
      next: (kargaguneak) => this.kargaguneak.set(kargaguneak),
      error: (err) => this.errorea.set(this.erroreMezua(err)),
    });

    this.api.getPowerbankak().subscribe({
      next: (powerbankak) => this.powerbankak.set(powerbankak),
      error: (err) => this.errorea.set(this.erroreMezua(err)),
    });
  }

  kargatu(): void {
    const filtroak: ErreserbaFiltroak = {};

    if (this.filtroak.id_erab !== '') filtroak.id_erab = Number(this.filtroak.id_erab);
    if (this.filtroak.id_takilla !== '') {
      filtroak.id_takilla = Number(this.filtroak.id_takilla);
    }
    if (this.filtroak.id_power !== '') filtroak.id_power = Number(this.filtroak.id_power);
    if (this.filtroak.egoera !== '') filtroak.egoera = this.filtroak.egoera;
    if (this.filtroak.hasiera) filtroak.hasiera = `${this.filtroak.hasiera}T00:00:00`;
    if (this.filtroak.bukaera) filtroak.bukaera = `${this.filtroak.bukaera}T23:59:59`;

    this.api.getErreserbak(filtroak).subscribe({
      next: (erreserbak) => this.erreserbak.set(erreserbak),
      error: (err) => this.errorea.set(this.erroreMezua(err)),
    });
  }

  bilatu(): void {
    this.errorea.set(null);
    this.kargatu();
  }

  garbituIragazkiak(): void {
    this.filtroak = {
      id_erab: '',
      id_takilla: '',
      id_power: '',
      egoera: '',
      hasiera: '',
      bukaera: '',
    };
    this.kargatu();
  }

  // ------------------------------------------------------------ erreserba berria

  irekiFormularioa(): void {
    this.errorea.set(null);
    this.mezua.set(null);

    const bihar = new Date();
    bihar.setDate(bihar.getDate() + 1);
    bihar.setHours(10, 0, 0, 0);
    const bukaera = new Date(bihar);
    bukaera.setHours(bihar.getHours() + 1);

    this.form = {
      id_erab: null,
      id_hasiera_takilla: null,
      id_hasiera_postua: null,
      id_power: null,
      hasiera: this.dataFormatuarentzat(bihar),
      bukaera: this.dataFormatuarentzat(bukaera),
    };
    this.formPostuak.set([]);
    this.formPowerbankak.set([]);
    this.formularioa.set(true);
  }

  itxiFormularioa(): void {
    this.formularioa.set(false);
  }

  kargaguneaAldatu(): void {
    this.form.id_hasiera_postua = null;
    this.form.id_power = null;
    this.formPostuak.set([]);
    this.formPowerbankak.set([]);

    if (this.form.id_hasiera_takilla === null) return;

    this.api.getKargagunea(this.form.id_hasiera_takilla).subscribe({
      next: (kargagunea) => this.formPostuak.set(kargagunea.postuak ?? []),
      error: (err) => this.errorea.set(this.erroreMezua(err)),
    });

    this.formPowerbankak.set(
      this.powerbankak().filter((p) => p.id_takilla === this.form.id_hasiera_takilla),
    );
  }

  postuaAldatu(): void {
    // Postuan kokatuta dagoen powerbank-a automatikoki hautatu
    const postua = this.formPostuak().find((p) => p.id_postu === this.form.id_hasiera_postua);
    this.form.id_power = postua?.powerbank?.id_power ?? null;
  }

  gorde(): void {
    if (
      !this.form.id_erab ||
      !this.form.id_hasiera_takilla ||
      !this.form.id_hasiera_postua ||
      !this.form.id_power ||
      !this.form.hasiera ||
      !this.form.bukaera
    ) {
      this.errorea.set('Eremu guztiak bete behar dira.');
      return;
    }

    if (new Date(this.form.hasiera) >= new Date(this.form.bukaera)) {
      this.errorea.set('Hasiera-data amaiera-data baino lehenagokoa izan behar da.');
      return;
    }

    this.gordetzen.set(true);
    this.api
      .sortuErreserba({
        id_erab: this.form.id_erab,
        id_power: this.form.id_power,
        erreserba_hasiera: this.form.hasiera,
        erreserba_bukaera: this.form.bukaera,
        id_hasiera_takilla: this.form.id_hasiera_takilla,
        id_hasiera_postua: this.form.id_hasiera_postua,
      })
      .subscribe({
        next: () => {
          this.gordetzen.set(false);
          this.mezua.set('Erreserba ondo sortu da.');
          this.itxiFormularioa();
          this.kargatu();
        },
        error: (err) => {
          this.gordetzen.set(false);
          this.errorea.set(this.erroreMezua(err));
        },
      });
  }

  // ------------------------------------------------------------ egoera-aldaketak

  ezeztatu(erreserba: Erreserba): void {
    if (!confirm(`Erreserba #${erreserba.id_erreserba} ezeztatu nahi duzu?`)) return;

    this.api.ezeztatuErreserba(erreserba.id_erreserba).subscribe({
      next: () => {
        this.mezua.set('Erreserba ondo ezeztatu da.');
        this.kargatu();
      },
      error: (err) => this.errorea.set(this.erroreMezua(err)),
    });
  }

  amaitu(erreserba: Erreserba): void {
    if (!confirm(`Erreserba #${erreserba.id_erreserba} amaitutzat eman nahi duzu?`)) return;

    this.api.aldatuErreserbaEgoera(erreserba.id_erreserba, 'amaituta').subscribe({
      next: () => {
        this.mezua.set('Erreserba amaitutzat eman da.');
        this.kargatu();
      },
      error: (err) => this.errorea.set(this.erroreMezua(err)),
    });
  }

  berraktibatu(erreserba: Erreserba): void {
    if (!confirm(`Erreserba #${erreserba.id_erreserba} berriro aktibatu nahi duzu?`)) return;

    this.api.aldatuErreserbaEgoera(erreserba.id_erreserba, 'aktiboa').subscribe({
      next: () => {
        this.mezua.set('Erreserba berriro aktibatu da.');
        this.kargatu();
      },
      error: (err) => this.errorea.set(this.erroreMezua(err)),
    });
  }

  // Oharra: erantzunak ez du erlazioen informazioa (izenak), beraz zerrenda
  // berriz kargatzen da aldaketaren ondoren.

  // ------------------------------------------------------------ laguntzaileak

  dataFormatuarentzat(data: Date): string {
    const pad = (balioa: number) => String(balioa).padStart(2, '0');
    return `${data.getFullYear()}-${pad(data.getMonth() + 1)}-${pad(data.getDate())}T${pad(
      data.getHours(),
    )}:${pad(data.getMinutes())}`;
  }

  formatuData(balioa: string | null): string {
    if (!balioa) return '—';
    const data = new Date(balioa);
    if (Number.isNaN(data.getTime())) return balioa;
    return data.toLocaleString('eu-ES', { dateStyle: 'short', timeStyle: 'short' });
  }

  private erroreMezua(err: any): string {
    const detail = err?.error?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
      return detail.map((x: any) => x.msg ?? JSON.stringify(x)).join(' | ');
    }
    return 'Ezin izan da eragiketa egin. Egiaztatu zerbitzaria martxan dagoela.';
  }

  // ------------------------------------------------------------ AG Grid

  colDefs: ColDef<Erreserba>[] = [
    { field: 'id_erreserba', headerName: 'ID', width: 70, flex: 0 },
    { field: 'erabiltzaile_izena', headerName: 'ERABILTZAILEA' },
    { field: 'kargagune_izena', headerName: 'KARGAGUNEA' },
    { field: 'id_hasiera_postua', headerName: 'POSTUA', width: 90, flex: 0 },
    {
      headerName: 'POWERBANK',
      width: 120,
      flex: 0,
      valueGetter: (p) =>
        p.data ? `#${p.data.id_power} (${p.data.powerbank_karga}%)` : '',
    },
    {
      field: 'erreserba_hasiera',
      headerName: 'HASIERA',
      valueFormatter: (p) => this.formatuData(p.value),
    },
    {
      field: 'erreserba_bukaera',
      headerName: 'BUKAERA',
      valueFormatter: (p) => this.formatuData(p.value),
    },
    {
      field: 'egoera',
      headerName: 'EGOERA',
      width: 120,
      flex: 0,
      cellClassRules: {
        'text-success fw-bold': (p) => p.value === 'aktiboa',
        'text-secondary fw-bold': (p) => p.value === 'ezeztatuta',
        'text-muted fw-bold': (p) => p.value === 'amaituta',
      },
    },
    {
      headerName: 'Akzioak',
      width: 260,
      flex: 0,
      sortable: false,
      filter: false,
      cellRenderer: (params: any) => this.akzioenZelda(params.data),
    },
  ];

  defaultColDef: ColDef = {
    flex: 1,
    filter: true,
    sortable: true,
    resizable: true,
  };

  pagination = true;
  paginationPageSize = 10;
  paginationPageSizeSelector: number[] | boolean = [10, 20, 50];

  private akzioenZelda(erreserba: Erreserba): HTMLElement {
    const edukiontzia = document.createElement('div');
    edukiontzia.className = 'd-flex gap-1 align-items-center h-100';

    const botoia = (testua: string, klasea: string, ekintza: () => void) => {
      const botoia = document.createElement('button');
      botoia.className = `btn ${klasea} btn-sm`;
      botoia.textContent = testua;
      botoia.addEventListener('click', (gertaera) => {
        gertaera.stopPropagation();
        ekintza();
      });
      edukiontzia.appendChild(botoia);
    };

    if (erreserba.egoera === 'aktiboa') {
      botoia('Amaitu', 'btn-outline-primary', () => this.amaitu(erreserba));
      botoia('Ezeztatu', 'btn-danger', () => this.ezeztatu(erreserba));
    } else if (erreserba.egoera === 'ezeztatuta') {
      botoia('Berriro aktibatu', 'btn-outline-success', () => this.berraktibatu(erreserba));
    } else {
      const testua = document.createElement('span');
      testua.className = 'text-muted small';
      testua.textContent = 'Ez dago ekintzarik';
      edukiontzia.appendChild(testua);
    }

    return edukiontzia;
  }
}
