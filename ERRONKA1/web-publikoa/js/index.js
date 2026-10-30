// ---------------------------------------------------------------------------
// Atal publikoa: kargaguneen zerrenda eta xehetasunak
// ---------------------------------------------------------------------------

import {
  api,
  dataFormularioarentzat,
  irudiOsoa,
  KARGAGUNE_EGOERA,
  saioaHasita,
} from './api.js';
import { ihes, mezua, nabigazioaMarraztu } from './nabigazioa.js';

const POSTU_EGOERA = {
  hutsa: { testua: 'Hutsa', klasea: 'bg-secondary-subtle text-secondary-emphasis' },
  kargatuta: { testua: 'Kargatuta', klasea: 'bg-success-subtle text-success-emphasis' },
  kargatzen: { testua: 'Kargatzen', klasea: 'bg-info-subtle text-info-emphasis' },
};

const zerrenda = document.getElementById('kargaguneenZerrenda');
const kargatzen = document.getElementById('kargatzen');
const emaitzarikEz = document.getElementById('emaitzarikEz');
const emaitzaKopurua = document.getElementById('emaitzaKopurua');
const modalElementua = document.getElementById('kargaguneModala');
const modala = new bootstrap.Modal(modalElementua);
const modalEdukia = document.getElementById('kargaguneModalEdukia');
const modalTitulua = document.getElementById('kargaguneModalTitulua');

let unekoKargagunea = null;

nabigazioaMarraztu('index.html');
kargatu();

// --------------------------------------------------------------- zerrenda

async function kargatu(bilaketa = '', egoera = '') {
  kargatzen.classList.remove('d-none');
  emaitzarikEz.classList.add('d-none');
  zerrenda.innerHTML = '';

  try {
    const kargaguneak = await api.kargaguneak(bilaketa, egoera);
    marraztu(kargaguneak);
  } catch (errorea) {
    mezua(errorea.message, 'danger');
  } finally {
    kargatzen.classList.add('d-none');
  }
}

function marraztu(kargaguneak) {
  emaitzaKopurua.textContent = `${kargaguneak.length} kargagune`;

  if (kargaguneak.length === 0) {
    emaitzarikEz.classList.remove('d-none');
    return;
  }

  zerrenda.innerHTML = kargaguneak.map(karta).join('');
}

function karta(k) {
  const egoera = KARGAGUNE_EGOERA[k.egoera] ?? {
    testua: k.egoera,
    klasea: 'bg-secondary-subtle text-secondary-emphasis',
  };
  const irudia = k.irudiak?.[0];

  const irudiAtala = irudia
    ? `<img src="${ihes(irudiOsoa(irudia))}" class="karta-irudia" alt="${ihes(k.izena)}" loading="lazy">`
    : `<div class="karta-irudia irudi-placeholder"><i class="bi bi-lightning-charge"></i></div>`;

  const libreTestua =
    k.postu_libreak > 0
      ? `<span class="text-success"><i class="bi bi-battery-charging me-1"></i>${k.postu_libreak} postu libre</span>`
      : `<span class="text-secondary"><i class="bi bi-battery me-1"></i>Une honetan okupatuta</span>`;

  return `
    <div class="col-12 col-md-6 col-lg-4">
      <article class="card kargagune-karta h-100 border-0 shadow-sm">
        ${irudiAtala}
        <div class="card-body d-flex flex-column">
          <div class="d-flex justify-content-between align-items-start gap-2 mb-2">
            <h3 class="h5 mb-0">${ihes(k.izena)}</h3>
            <span class="badge rounded-pill ${egoera.klasea}">${ihes(egoera.testua)}</span>
          </div>
          <p class="text-secondary small mb-3">
            <i class="bi bi-geo-alt me-1"></i>${ihes(k.helbidea)}
          </p>
          <div class="d-flex flex-wrap gap-3 small mb-3">
            <span class="text-secondary">
              <i class="bi bi-plug me-1"></i>${k.postuak_kopurua} karga-postu
            </span>
            ${libreTestua}
          </div>
          <div class="mt-auto d-flex gap-2">
            <button class="btn btn-outline-primary btn-sm flex-grow-1" data-ikusi="${k.id_takilla}">
              <i class="bi bi-info-circle me-1"></i>Xehetasunak
            </button>
            <a class="btn btn-primary btn-sm" href="erreserbak.html?kargagunea=${k.id_takilla}">
              Erreserbatu
            </a>
          </div>
        </div>
      </article>
    </div>`;
}

// --------------------------------------------------------------- xehetasunak

zerrenda.addEventListener('click', async (gertaera) => {
  const botoia = gertaera.target.closest('[data-ikusi]');
  if (!botoia) return;
  await irekiXehetasunak(Number(botoia.dataset.ikusi));
});

async function irekiXehetasunak(id) {
  modalEdukia.innerHTML = `
    <div class="text-center py-5">
      <div class="spinner-border text-primary" role="status"></div>
    </div>`;
  modala.show();

  try {
    unekoKargagunea = await api.kargagunea(id);
    modalTitulua.textContent = unekoKargagunea.izena;
    xehetasunaMarraztu(unekoKargagunea);
  } catch (errorea) {
    modalEdukia.innerHTML = `<div class="alert alert-danger mb-0">${ihes(errorea.message)}</div>`;
  }
}

function xehetasunaMarraztu(k, postuak = null) {
  const egoera = KARGAGUNE_EGOERA[k.egoera] ?? {
    testua: k.egoera,
    klasea: 'bg-secondary-subtle text-secondary-emphasis',
  };

  const hasiera = new Date(Date.now() + 60 * 60 * 1000);
  const bukaera = new Date(Date.now() + 2 * 60 * 60 * 1000);

  const irudiak = k.irudiak?.length
    ? `
      <img id="irudiNaguisa" src="${ihes(irudiOsoa(k.irudiak[0]))}" class="modal-irudi nagusia mb-2"
        alt="${ihes(k.izena)}">
      <div class="d-flex gap-2 flex-wrap">
        ${k.irudiak
          .map(
            (url, indizea) => `
            <button type="button" class="btn p-0 border-0 irudi-miniatura" data-irudia="${ihes(
              irudiOsoa(url)
            )}" aria-label="Irudia ${indizea + 1}">
              <img src="${ihes(irudiOsoa(url))}" alt="">
            </button>`
          )
          .join('')}
      </div>`
    : `<div class="modal-irudi nagusia irudi-placeholder mb-2"><i class="bi bi-lightning-charge"></i></div>`;

  modalEdukia.innerHTML = `
    <div class="row g-4">
      <div class="col-12 col-md-6">${irudiak}</div>
      <div class="col-12 col-md-6">
        <span class="badge rounded-pill ${egoera.klasea} mb-2">${ihes(egoera.testua)}</span>
        <p class="text-secondary mb-3">
          <i class="bi bi-geo-alt me-1"></i>${ihes(k.helbidea)}
        </p>
        <ul class="list-unstyled small mb-0">
          <li class="mb-1"><i class="bi bi-plug me-2 text-primary"></i>${k.postuak_kopurua} karga-postu</li>
          <li class="mb-1"><i class="bi bi-battery-charging me-2 text-primary"></i>${k.powerbank_kopurua} powerbank</li>
          <li><i class="bi bi-broadcast me-2 text-primary"></i>${k.postu_libreak} postu libre une honetan</li>
        </ul>
      </div>
    </div>

    <hr class="my-4">

    <h3 class="h6">Karga-postuen erabilgarritasuna</h3>
    <form id="erabilgarritasunFormularioa" class="row g-2 align-items-end mb-3">
      <div class="col-12 col-sm-5">
        <label class="form-label small mb-1" for="mHasiera">Noiztik</label>
        <input id="mHasiera" type="datetime-local" class="form-control form-control-sm"
          value="${dataFormularioarentzat(hasiera)}" required>
      </div>
      <div class="col-12 col-sm-5">
        <label class="form-label small mb-1" for="mBukaera">Noiz arte</label>
        <input id="mBukaera" type="datetime-local" class="form-control form-control-sm"
          value="${dataFormularioarentzat(bukaera)}" required>
      </div>
      <div class="col-12 col-sm-2 d-grid">
        <button class="btn btn-outline-primary btn-sm" type="submit" title="Egiaztatu">
          <i class="bi bi-search"></i>
        </button>
      </div>
    </form>

    <div class="table-responsive">
      <table class="table table-sm align-middle mb-0">
        <thead>
          <tr>
            <th>Postua</th>
            <th>Egoera</th>
            <th>Powerbank</th>
            <th class="text-end">Libre?</th>
          </tr>
        </thead>
        <tbody id="postuTaula">${postuErrenkadak(postuak ?? k.postuak ?? [])}</tbody>
      </table>
    </div>

    <div class="d-flex flex-column flex-sm-row gap-2 mt-4">
      <a class="btn btn-primary flex-grow-1" href="erreserbak.html?kargagunea=${k.id_takilla}">
        <i class="bi bi-calendar-plus me-1"></i>Erreserbatu kargagune honetan
      </a>
      ${
        saioaHasita()
          ? ''
          : `<a class="btn btn-outline-secondary" href="kontua.html?next=erreserbak.html%3Fkargagunea%3D${k.id_takilla}">
              <i class="bi bi-box-arrow-in-right me-1"></i>Saioa hasi
            </a>`
      }
    </div>
    ${
      saioaHasita()
        ? ''
        : `<p class="small text-secondary mt-2 mb-0">Erreserba egiteko saioa hasi behar duzu.</p>`
    }`;

  // Irudiak aldatzea
  modalEdukia.querySelectorAll('[data-irudia]').forEach((botoia) => {
    botoia.addEventListener('click', () => {
      modalEdukia.querySelector('#irudiNaguisa').src = botoia.dataset.irudia;
    });
  });

  // Erabilgarritasunaren egiaztapena
  modalEdukia
    .querySelector('#erabilgarritasunFormularioa')
    .addEventListener('submit', async (gertaera) => {
      gertaera.preventDefault();
      const hasieraBalioa = modalEdukia.querySelector('#mHasiera').value;
      const bukaeraBalioa = modalEdukia.querySelector('#mBukaera').value;

      if (!hasieraBalioa || !bukaeraBalioa) {
        mezua('Aukeratu hasiera eta bukaera datak.', 'warning');
        return;
      }
      if (new Date(hasieraBalioa) >= new Date(bukaeraBalioa)) {
        mezua('Hasiera-data amaiera-data baino lehenagokoa izan behar da.', 'warning');
        return;
      }

      try {
        const zehatza = await api.erabilgarritasuna(
          k.id_takilla,
          hasieraBalioa,
          bukaeraBalioa
        );
        modalEdukia.querySelector('#postuTaula').innerHTML = postuErrenkadak(
          zehatza.postuak ?? []
        );
      } catch (errorea) {
        mezua(errorea.message, 'danger');
      }
    });
}

function postuErrenkadak(postuak) {
  if (postuak.length === 0) {
    return `<tr><td colspan="4" class="text-secondary">Kargagune honek ez du karga-posturik.</td></tr>`;
  }

  return postuak
    .map((postua) => {
      const egoera = POSTU_EGOERA[postua.egoera] ?? {
        testua: postua.egoera,
        klasea: 'bg-secondary-subtle text-secondary-emphasis',
      };
      const powerbank = postua.powerbank
        ? `#${postua.powerbank.id_power} · ${postua.powerbank.karga}%`
        : '<span class="text-secondary">—</span>';
      const libre = postua.libre
        ? '<span class="badge bg-success-subtle text-success-emphasis">Bai</span>'
        : '<span class="badge bg-danger-subtle text-danger-emphasis">Ez</span>';

      return `
        <tr>
          <td>#${postua.id_postu}</td>
          <td><span class="badge ${egoera.klasea}">${ihes(egoera.testua)}</span></td>
          <td>${powerbank}</td>
          <td class="text-end">${libre}</td>
        </tr>`;
    })
    .join('');
}

// --------------------------------------------------------------- bilaketa

document.getElementById('bilaketaFormularioa').addEventListener('submit', (gertaera) => {
  gertaera.preventDefault();
  const bilaketa = document.getElementById('bilaketa').value;
  const egoera = document.getElementById('egoeraIragazkia').value;
  kargatu(bilaketa, egoera);
});
