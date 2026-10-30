import { CommonModule } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AgGridAngular } from 'ag-grid-angular';
import { AllCommunityModule, ColDef, ModuleRegistry } from 'ag-grid-community';
import { API_OINARRIA, PowerbankApi } from '../api/powerbank-api';
import { Kargagune, KargaguneEgoera, Postua, PostuaEgoera } from '../api/ereduak';

ModuleRegistry.registerModules([AllCommunityModule]);

@Component({
  selector: 'app-kargaguneak',
  standalone: true,
  imports: [CommonModule, FormsModule, AgGridAngular],
  templateUrl: './kargaguneak-component.html',
  styleUrl: './kargaguneak-component.css',
})
export class KargaguneakComponent implements OnInit {
  private api = inject(PowerbankApi);

  kargaguneak = signal<Kargagune[]>([]);
  aukeratua = signal<Kargagune | null>(null);
  formularioa = signal(false);
  editatzen = signal<Kargagune | null>(null);
  gordetzen = signal(false);
  mezua = signal<string | null>(null);
  errorea = signal<string | null>(null);

  bilaketa = '';
  egoeraFiltroa: KargaguneEgoera | '' = '';

  inprimakia: { izena: string; helbidea: string; egoera: KargaguneEgoera } = {
    izena: '',
    helbidea: '',
    egoera: 'erabilgarri',
  };

  irudiUrl = '';
  postuEgoera: PostuaEgoera = 'hutsa';

  readonly egoerak: { balioa: KargaguneEgoera; izena: string }[] = [
    { balioa: 'erabilgarri', izena: 'Erabilgarri' },
    { balioa: 'mantentze_lanetan', izena: 'Mantentze-lanetan' },
    { balioa: 'zerbitzuz_kanpo', izena: 'Zerbitzuz kanpo' },
  ];

  readonly postuEgoerak: { balioa: PostuaEgoera; izena: string }[] = [
    { balioa: 'hutsa', izena: 'Hutsa' },
    { balioa: 'kargatuta', izena: 'Kargatuta' },
    { balioa: 'kargatzen', izena: 'Kargatzen' },
  ];

  ngOnInit(): void {
    this.kargatu();
  }

  // ------------------------------------------------------------ datuak

  kargatu(): void {
    this.api.getKargaguneak(this.bilaketa, this.egoeraFiltroa).subscribe({
      next: (emaitza) => this.kargaguneak.set(emaitza),
      error: (err) => this.errorea.set(this.erroreMezua(err)),
    });
  }

  bilatu(): void {
    this.errorea.set(null);
    this.kargatu();
  }

  garbituIragazkiak(): void {
    this.bilaketa = '';
    this.egoeraFiltroa = '';
    this.kargatu();
  }

  hautatu(kargagunea: Kargagune | undefined): void {
    if (!kargagunea) return;
    this.errorea.set(null);
    this.api.getKargagunea(kargagunea.id_takilla).subscribe({
      next: (zehatza) => this.aukeratua.set(zehatza),
      error: (err) => this.errorea.set(this.erroreMezua(err)),
    });
  }

  // ------------------------------------------------------------ formularioa

  irekiFormularioa(kargagunea?: Kargagune): void {
    this.errorea.set(null);
    this.mezua.set(null);
    this.editatzen.set(kargagunea ?? null);
    this.inprimakia = kargagunea
      ? { izena: kargagunea.izena, helbidea: kargagunea.helbidea, egoera: kargagunea.egoera }
      : { izena: '', helbidea: '', egoera: 'erabilgarri' };
    this.formularioa.set(true);
  }

  itxiFormularioa(): void {
    this.formularioa.set(false);
    this.editatzen.set(null);
  }

  gorde(): void {
    if (!this.inprimakia.izena.trim() || !this.inprimakia.helbidea.trim()) {
      this.errorea.set('Izena eta helbidea bete behar dira.');
      return;
    }

    this.gordetzen.set(true);
    const editatzen = this.editatzen();

    const eskaera = editatzen
      ? this.api.eguneratuKargagunea(editatzen.id_takilla, this.inprimakia)
      : this.api.sortuKargagunea(this.inprimakia);

    eskaera.subscribe({
      next: (emaitza) => {
        this.gordetzen.set(false);
        this.mezua.set(
          editatzen ? 'Kargagunea ondo eguneratu da.' : 'Kargagunea ondo sortu da.',
        );
        this.itxiFormularioa();
        this.kargatu();
        if (this.aukeratua()?.id_takilla === emaitza.id_takilla) {
          this.hautatu(emaitza);
        }
      },
      error: (err) => {
        this.gordetzen.set(false);
        this.errorea.set(this.erroreMezua(err));
      },
    });
  }

  // ------------------------------------------------------------ akzioak

  ezabatu(kargagunea: Kargagune): void {
    if (!confirm(`"${kargagunea.izena}" kargagunea ezabatu nahi duzu?`)) return;

    this.api.ezabatuKargagunea(kargagunea.id_takilla).subscribe({
      next: () => {
        this.mezua.set('Kargagunea ondo ezabatu da.');
        if (this.aukeratua()?.id_takilla === kargagunea.id_takilla) {
          this.aukeratua.set(null);
        }
        this.kargatu();
      },
      error: (err) => this.errorea.set(this.erroreMezua(err)),
    });
  }

  desaktibatu(kargagunea: Kargagune): void {
    if (!confirm(`"${kargagunea.izena}" kargagunea desaktibatu nahi duzu?`)) return;

    this.api.desaktibatuKargagunea(kargagunea.id_takilla).subscribe({
      next: (emaitza) => {
        this.mezua.set('Kargagunea zerbitzuz kanpo utzi da.');
        this.kargaguneak.update((zerrenda) =>
          zerrenda.map((k) => (k.id_takilla === emaitza.id_takilla ? { ...k, ...emaitza } : k)),
        );
        if (this.aukeratua()?.id_takilla === emaitza.id_takilla) {
          this.aukeratua.set(emaitza);
        }
      },
      error: (err) => this.errorea.set(this.erroreMezua(err)),
    });
  }

  // ------------------------------------------------------------ irudiak

  irudiOsoa(url: string): string {
    return url.startsWith('http') ? url : `${API_OINARRIA}${url}`;
  }

  gehituIrudiaUrl(): void {
    const kargagunea = this.aukeratua();
    if (!kargagunea) return;

    const url = this.irudiUrl.trim();
    if (!url) {
      this.errorea.set('Irudiaren URLa idatzi behar duzu.');
      return;
    }

    this.api.gehituIrudia(kargagunea.id_takilla, url).subscribe({
      next: () => {
        this.irudiUrl = '';
        this.mezua.set('Irudia ondo gehitu da.');
        this.hautatu(kargagunea);
        this.kargatu();
      },
      error: (err) => this.errorea.set(this.erroreMezua(err)),
    });
  }

  igoIrudia(gertaera: Event): void {
    const sarrera = gertaera.target as HTMLInputElement;
    const fitxategia = sarrera.files?.[0];
    const kargagunea = this.aukeratua();
    if (!fitxategia || !kargagunea) return;

    this.api.igoIrudia(kargagunea.id_takilla, fitxategia).subscribe({
      next: () => {
        this.mezua.set('Irudia ondo igo da.');
        sarrera.value = '';
        this.hautatu(kargagunea);
        this.kargatu();
      },
      error: (err) => {
        sarrera.value = '';
        this.errorea.set(this.erroreMezua(err));
      },
    });
  }

  ezabatuIrudia(idIrudia: number): void {
    const kargagunea = this.aukeratua();
    if (!kargagunea || !confirm('Irudi hau ezabatu nahi duzu?')) return;

    this.api.ezabatuIrudia(kargagunea.id_takilla, idIrudia).subscribe({
      next: () => {
        this.mezua.set('Irudia ondo ezabatu da.');
        this.hautatu(kargagunea);
        this.kargatu();
      },
      error: (err) => this.errorea.set(this.erroreMezua(err)),
    });
  }

  // ------------------------------------------------------------ karga-postuak

  gehituPostua(): void {
    const kargagunea = this.aukeratua();
    if (!kargagunea) return;

    this.api.sortuPostua(kargagunea.id_takilla, this.postuEgoera).subscribe({
      next: () => {
        this.mezua.set('Karga-postua ondo gehitu da.');
        this.hautatu(kargagunea);
        this.kargatu();
      },
      error: (err) => this.errorea.set(this.erroreMezua(err)),
    });
  }

  aldatuPostuEgoera(postua: Postua, egoera: PostuaEgoera): void {
    const kargagunea = this.aukeratua();
    if (!kargagunea) return;

    this.api.eguneratuPostua(postua.id_postu, { egoera }).subscribe({
      next: () => {
        this.mezua.set('Karga-postuaren egoera aldatu da.');
        this.hautatu(kargagunea);
      },
      error: (err) => this.errorea.set(this.erroreMezua(err)),
    });
  }

  ezabatuPostua(postua: Postua): void {
    const kargagunea = this.aukeratua();
    if (!kargagunea || !confirm(`Karga-postua #${postua.id_postu} ezabatu nahi duzu?`)) return;

    this.api.ezabatuPostua(postua.id_postu).subscribe({
      next: () => {
        this.mezua.set('Karga-postua ondo ezabatu da.');
        this.hautatu(kargagunea);
        this.kargatu();
      },
      error: (err) => this.errorea.set(this.erroreMezua(err)),
    });
  }

  // ------------------------------------------------------------ laguntzaileak

  private erroreMezua(err: any): string {
    const detail = err?.error?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
      return detail.map((x: any) => x.msg ?? JSON.stringify(x)).join(' | ');
    }
    return 'Ezin izan da eragiketa egin. Egiaztatu zerbitzaria martxan dagoela.';
  }

  // ------------------------------------------------------------ AG Grid

  colDefs: ColDef<Kargagune>[] = [
    { field: 'id_takilla', headerName: 'ID', width: 80, flex: 0 },
    { field: 'izena', headerName: 'IZENA', filter: 'agTextColumnFilter' },
    { field: 'helbidea', headerName: 'HELBIDEA' },
    {
      field: 'egoera',
      headerName: 'EGOERA',
      cellClassRules: {
        'text-success fw-bold': (p) => p.value === 'erabilgarri',
        'text-warning fw-bold': (p) => p.value === 'mantentze_lanetan',
        'text-danger fw-bold': (p) => p.value === 'zerbitzuz_kanpo',
      },
    },
    { field: 'postuak_kopurua', headerName: 'POSTUAK', width: 110, flex: 0 },
    { field: 'powerbank_kopurua', headerName: 'POWERBANK', width: 130, flex: 0 },
    { field: 'erreserba_aktiboak', headerName: 'ERRESERBAK', width: 130, flex: 0 },
    {
      headerName: 'Akzioak',
      width: 320,
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
  paginationPageSize = 5;
  paginationPageSizeSelector: number[] | boolean = [5, 10, 20];

  private akzioenZelda(kargagunea: Kargagune): HTMLElement {
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

    botoia('Ikusi', 'btn-outline-primary', () => this.hautatu(kargagunea));
    botoia('Aldatu', 'btn-success', () => this.irekiFormularioa(kargagunea));
    botoia('Desaktibatu', 'btn-warning', () => this.desaktibatu(kargagunea));
    botoia('Ezabatu', 'btn-danger', () => this.ezabatu(kargagunea));

    return edukiontzia;
  }
}
