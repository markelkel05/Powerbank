// ---------------------------------------------------------------------------
// Atal publikoa: erreserba berria egitea eta norberaren erreserbak kudeatzea
// ---------------------------------------------------------------------------

import {
  api,
  dataFormularioarentzat,
  ERRESERBA_EGOERA,
  erabiltzailea,
  formatuData,
  saioaHasita,
} from './api.js';
import { ihes, mezua, nabigazioaMarraztu } from './nabigazioa.js';

const kargaguneaHautatzailea = document.getElementById('kargagunea');
const postuaHautatzailea = document.getElementById('postua');
const powerbankHautatzailea = document.getElementById('powerbank');
const hasieraSarrera = document.getElementById('hasiera');
const bukaeraSarrera = document.getElementById('bukaera');
const formularioErrorea = document.getElementById('formularioErrorea');
const erreserbatuBotoia = document.getElementById('erreserbatuBotoia');
const nireErreserbakEdukiontzia = document.getElementById('nireErreserbak');

let nireErreserbak = [];
let unekoPowerbankak = [];

nabigazioaMarraztu('erreserbak.html');

if (!saioaHasita()) {
  document.getElementById('saioaBeharrezkoa').classList.remove('d-none');
} else {
  document.getElementById('erreserbaAtala').classList.remove('d-none');
  hasieratu();
}

// --------------------------------------------------------------- hasieraketa

async function hasieratu() {
  const orain = new Date(Date.now() + 60 * 60 * 1000);
  orain.setMinutes(0, 0, 0);
  const bukaera = new Date(orain.getTime() + 60 * 60 * 1000);

  hasieraSarrera.value = dataFormularioarentzat(orain);
  bukaeraSarrera.value = dataFormularioarentzat(bukaera);

  await kargatuKargaguneak();
  await kargatuNireErreserbak();
}

async function kargatuKargaguneak() {
  try {
    const kargaguneak = await api.kargaguneak();

    kargaguneaHautatzailea.innerHTML =
      '<option value="">— Aukeratu —</option>' +
      kargaguneak
        .map(
          (k) =>
            `<option value="${k.id_takilla}">${ihes(k.izena)} · ${ihes(k.helbidea)}${
              k.egoera !== 'erabilgarri' ? ' (ez dago erabilgarri)' : ''
            }</option>`
        )
        .join('');

    const query = new URLSearchParams(window.location.search);
    const hasierakoa = query.get('kargagunea');
    if (hasierakoa) {
      kargaguneaHautatzailea.value = hasierakoa;
      await kargaguneaAldatu();
    }
  } catch (errorea) {
    mostratuErrorea(errorea.message);
  }
}

// --------------------------------------------------------------- formularioa

kargaguneaHautatzailea.addEventListener('change', kargaguneaAldatu);

async function kargaguneaAldatu() {
  const id = Number(kargaguneaHautatzailea.value);

  postuaHautatzailea.disabled = true;
  powerbankHautatzailea.disabled = true;
  postuaHautatzailea.innerHTML = '<option value="">— Aukeratu —</option>';
  powerbankHautatzailea.innerHTML = '<option value="">— Aukeratu —</option>';

  if (!id) return;

  try {
    const [kargagunea, powerbankak] = await Promise.all([
      api.kargagunea(id),
      api.powerbankak(id),
    ]);

    unekoPowerbankak = powerbankak;

    postuaHautatzailea.innerHTML =
      '<option value="">— Aukeratu —</option>' +
      (kargagunea.postuak ?? [])
        .map(
          (postua) =>
            `<option value="${postua.id_postu}">#${postua.id_postu} · ${ihes(
              postua.egoera
            )}${postua.libre ? ' · libre' : ' · okupatuta'}</option>`
        )
        .join('');

    powerbankHautatzailea.innerHTML =
      '<option value="">— Aukeratu —</option>' +
      powerbankak
        .map(
          (powerbank) =>
            `<option value="${powerbank.id_power}">#${powerbank.id_power} · ${powerbank.karga}%${
              powerbank.id_postu ? ` · postua #${powerbank.id_postu}` : ''
            }</option>`
        )
        .join('');

    postuaHautatzailea.disabled = false;
    powerbankHautatzailea.disabled = false;
    ezkutatuErrorea();
  } catch (errorea) {
    mostratuErrorea(errorea.message);
  }
}

postuaHautatzailea.addEventListener('change', () => {
  // Hautatutako postuan kokatuta dagoen powerbank-a automatikoki aukeratu
  const postua = Number(postuaHautatzailea.value);
  if (!postua) return;

  const postukoa = unekoPowerbankak.find((p) => p.id_postu === postua);
  if (postukoa) powerbankHautatzailea.value = String(postukoa.id_power);
});

document.getElementById('erreserbaFormularioa').addEventListener('submit', async (gertaera) => {
  gertaera.preventDefault();
  ezkutatuErrorea();

  const id_erab = erabiltzailea()?.id_erab;
  const id_hasiera_takilla = Number(kargaguneaHautatzailea.value);
  const id_hasiera_postua = Number(postuaHautatzailea.value);
  const id_power = Number(powerbankHautatzailea.value);
  const hasiera = hasieraSarrera.value;
  const bukaera = bukaeraSarrera.value;

  if (!id_erab) {
    mostratuErrorea('Saioa iraungi da. Hasi saioa berriro.');
    return;
  }
  if (!id_hasiera_takilla || !id_hasiera_postua || !id_power || !hasiera || !bukaera) {
    mostratuErrorea('Bete itzazu eremu guztiak.');
    return;
  }
  if (new Date(hasiera) >= new Date(bukaera)) {
    mostratuErrorea('Hasiera-data amaiera-data baino lehenagokoa izan behar da.');
    return;
  }

  erreserbatuBotoia.disabled = true;
  erreserbatuBotoia.textContent = 'Erreserbatzen...';

  try {
    await api.sortuErreserba({
      id_erab,
      id_power,
      erreserba_hasiera: hasiera,
      erreserba_bukaera: bukaera,
      id_hasiera_takilla,
      id_hasiera_postua,
    });
    mezua('Erreserba ondo egin da. Powerbank-a kargagunean izango duzu.', 'success');
    await kargatuNireErreserbak();
    await kargaguneaAldatu();
  } catch (errorea) {
    mostratuErrorea(errorea.message);
  } finally {
    erreserbatuBotoia.disabled = false;
    erreserbatuBotoia.innerHTML = '<i class="bi bi-check2-circle me-1"></i>Erreserbatu';
  }
});

// --------------------------------------------------------------- nire erreserbak

document.getElementById('berrizKargatu').addEventListener('click', kargatuNireErreserbak);

async function kargatuNireErreserbak() {
  try {
    nireErreserbak = await api.nireErreserbak();
    marraztuNireErreserbak();
  } catch (errorea) {
    nireErreserbakEdukiontzia.innerHTML = `<div class="alert alert-danger mb-0">${ihes(
      errorea.message
    )}</div>`;
  }
}

function marraztuNireErreserbak() {
  if (nireErreserbak.length === 0) {
    nireErreserbakEdukiontzia.innerHTML = `
      <div class="text-center py-4">
        <i class="bi bi-calendar-x display-6 text-secondary"></i>
        <p class="text-secondary mt-3 mb-0">Oraindik ez duzu erreserbarik egin.</p>
      </div>`;
    return;
  }

  nireErreserbakEdukiontzia.innerHTML = `
    <div class="table-responsive">
      <table class="table align-middle mb-0">
        <thead>
          <tr>
            <th>Kargagunea</th>
            <th>Tartea</th>
            <th>Powerbank</th>
            <th>Egoera</th>
            <th class="text-end"></th>
          </tr>
        </thead>
        <tbody>
          ${nireErreserbak.map(erreserbaErrenkada).join('')}
        </tbody>
      </table>
    </div>`;

  nireErreserbakEdukiontzia.querySelectorAll('[data-ezeztatu]').forEach((botoia) => {
    botoia.addEventListener('click', () => ezeztatu(Number(botoia.dataset.ezeztatu)));
  });
}

function erreserbaErrenkada(erreserba) {
  const egoera = ERRESERBA_EGOERA[erreserba.egoera] ?? {
    testua: erreserba.egoera,
    klasea: 'bg-secondary-subtle text-secondary-emphasis',
  };
  const hasiera = new Date(erreserba.erreserba_hasiera);
  const etorkizunekoa = hasiera.getTime() > Date.now();
  const ezeztatuDaiteke = erreserba.egoera === 'aktiboa' && etorkizunekoa;

  return `
    <tr>
      <td>
        <div class="fw-semibold">${ihes(erreserba.kargagune_izena)}</div>
        <div class="small text-secondary">Postua #${erreserba.id_hasiera_postua}</div>
      </td>
      <td class="small">
        <div>${formatuData(erreserba.erreserba_hasiera)}</div>
        <div class="text-secondary">→ ${formatuData(erreserba.erreserba_bukaera)}</div>
      </td>
      <td class="small">#${erreserba.id_power}</td>
      <td><span class="badge ${egoera.klasea}">${ihes(egoera.testua)}</span></td>
      <td class="text-end">
        ${
          ezeztatuDaiteke
            ? `<button class="btn btn-outline-danger btn-sm" data-ezeztatu="${erreserba.id_erreserba}">
                Ezeztatu
              </button>`
            : `<span class="small text-secondary">${
                erreserba.egoera === 'aktiboa' ? 'Abian' : '—'
              }</span>`
        }
      </td>
    </tr>`;
}

async function ezeztatu(id) {
  if (!confirm('Erreserba hau ezeztatu nahi duzu?')) return;

  try {
    await api.ezeztatuErreserba(id);
    mezua('Erreserba ezeztatu da.', 'success');
    await kargatuNireErreserbak();
    await kargaguneaAldatu();
  } catch (errorea) {
    mezua(errorea.message, 'danger');
  }
}

// --------------------------------------------------------------- laguntzaileak

function mostratuErrorea(testua) {
  formularioErrorea.textContent = testua;
  formularioErrorea.classList.remove('d-none');
}

function ezkutatuErrorea() {
  formularioErrorea.classList.add('d-none');
}
