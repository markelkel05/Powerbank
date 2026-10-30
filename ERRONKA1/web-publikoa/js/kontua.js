// ---------------------------------------------------------------------------
// Atal publikoa: saioa hasi, erregistratu eta norberaren datuak
// ---------------------------------------------------------------------------

import {
  api,
  erabiltzailea,
  erabiltzaileaEguneratu,
  saioaEzabatu,
  saioaGorde,
  saioaHasita,
} from './api.js';
import { ihes, mezua, nabigazioaMarraztu } from './nabigazioa.js';

const saioAtala = document.getElementById('saioAtala');
const profilAtala = document.getElementById('profilAtala');
const query = new URLSearchParams(window.location.search);
const hurrengoa = query.get('next');

nabigazioaMarraztu('kontua.html');

if (saioaHasita()) {
  erakutsiProfila();
} else {
  saioAtala.classList.remove('d-none');

  if (query.get('erregistratu')) {
    document.querySelector('[data-bs-target="#erregistroaPanela"]')?.click();
  }
}

// --------------------------------------------------------------- saioa hasi

document.getElementById('saioFormularioa').addEventListener('submit', async (gertaera) => {
  gertaera.preventDefault();
  ezkutatu('saioErrorea');

  const emaila = document.getElementById('saioEmaila').value.trim();
  const pasahitza = document.getElementById('saioPasahitza').value;
  const botoia = document.getElementById('saioBotoia');

  if (!emaila || !pasahitza) {
    mostratu('saioErrorea', 'Emaila eta pasahitza bete behar dira.');
    return;
  }

  botoia.disabled = true;
  try {
    const erantzuna = await api.saioaHasi(emaila, pasahitza);
    saioaGorde(erantzuna.access_token, erantzuna.erabiltzailea);
    mezua(`Ongi etorri, ${erantzuna.erabiltzailea.izena}!`, 'success');

    if (hurrengoa) {
      window.location.href = hurrengoa;
      return;
    }

    nabigazioaMarraztu('kontua.html');
    erakutsiProfila();
  } catch (errorea) {
    mostratu('saioErrorea', errorea.message);
  } finally {
    botoia.disabled = false;
  }
});

// --------------------------------------------------------------- erregistroa

document.getElementById('erregistroFormularioa').addEventListener('submit', async (gertaera) => {
  gertaera.preventDefault();
  ezkutatu('erregistroErrorea');

  const datuak = {
    nan: document.getElementById('erNan').value.trim(),
    izena: document.getElementById('erIzena').value.trim(),
    abizenak: document.getElementById('erAbizenak').value.trim(),
    email: document.getElementById('erEmaila').value.trim(),
    helbidea: document.getElementById('erHelbidea').value.trim(),
    pasahitza: document.getElementById('erPasahitza').value,
  };
  const errepikatua = document.getElementById('erPasahitza2').value;

  if (Object.values(datuak).some((balioa) => !balioa)) {
    mostratu('erregistroErrorea', 'Eremu guztiak bete behar dira.');
    return;
  }
  if (datuak.nan.length !== 9) {
    mostratu('erregistroErrorea', 'NANak 9 karaktere izan behar ditu.');
    return;
  }
  if (datuak.pasahitza.length < 6) {
    mostratu('erregistroErrorea', 'Pasahitzak gutxienez 6 karaktere izan behar ditu.');
    return;
  }
  if (datuak.pasahitza !== errepikatua) {
    mostratu('erregistroErrorea', 'Pasahitzak ez datoz bat.');
    return;
  }

  const botoia = document.getElementById('erregistroBotoia');
  botoia.disabled = true;
  try {
    const erantzuna = await api.erregistratu(datuak);
    saioaGorde(erantzuna.access_token, erantzuna.erabiltzailea);
    mezua('Kontua ondo sortu da. Ongi etorri!', 'success');

    if (hurrengoa) {
      window.location.href = hurrengoa;
      return;
    }

    nabigazioaMarraztu('kontua.html');
    erakutsiProfila();
  } catch (errorea) {
    mostratu('erregistroErrorea', errorea.message);
  } finally {
    botoia.disabled = false;
  }
});

// --------------------------------------------------------------- profila

function erakutsiProfila() {
  saioAtala.classList.add('d-none');
  profilAtala.classList.remove('d-none');

  const erabiltzaileDatuak = erabiltzailea();
  if (!erabiltzaileDatuak) return;

  document.getElementById('profilIzena').textContent =
    `${erabiltzaileDatuak.izena} ${erabiltzaileDatuak.abizenak}`;
  document.getElementById('profilEmaila').textContent = erabiltzaileDatuak.email;

  document.getElementById('profilDatuak').innerHTML = `
    <li class="mb-2"><i class="bi bi-person-vcard me-2 text-primary"></i>NAN: ${ihes(
      erabiltzaileDatuak.nan
    )}</li>
    <li class="mb-2"><i class="bi bi-envelope me-2 text-primary"></i>${ihes(
      erabiltzaileDatuak.email
    )}</li>
    <li class="mb-2"><i class="bi bi-geo-alt me-2 text-primary"></i>${ihes(
      erabiltzaileDatuak.helbidea
    )}</li>
    <li><i class="bi bi-shield-check me-2 text-primary"></i>Rola: ${
      erabiltzaileDatuak.id_rol === 1 ? 'Administratzailea' : 'Erabiltzaile arrunta'
    }</li>`;

  document.getElementById('prIzena').value = erabiltzaileDatuak.izena;
  document.getElementById('prAbizenak').value = erabiltzaileDatuak.abizenak;
  document.getElementById('prEmaila').value = erabiltzaileDatuak.email;
  document.getElementById('prHelbidea').value = erabiltzaileDatuak.helbidea;
  document.getElementById('prPasahitza').value = '';
  document.getElementById('prPasahitza2').value = '';
}

document.getElementById('profilFormularioa').addEventListener('submit', async (gertaera) => {
  gertaera.preventDefault();
  ezkutatu('profilErrorea');

  const erabiltzaileDatuak = erabiltzailea();
  if (!erabiltzaileDatuak) return;

  const datuak = {
    izena: document.getElementById('prIzena').value.trim(),
    abizenak: document.getElementById('prAbizenak').value.trim(),
    email: document.getElementById('prEmaila').value.trim(),
    helbidea: document.getElementById('prHelbidea').value.trim(),
  };
  const pasahitza = document.getElementById('prPasahitza').value;
  const pasahitza2 = document.getElementById('prPasahitza2').value;

  if (Object.values(datuak).some((balioa) => !balioa)) {
    mostratu('profilErrorea', 'Eremu guztiak bete behar dira.');
    return;
  }
  if (pasahitza || pasahitza2) {
    if (pasahitza.length < 6) {
      mostratu('profilErrorea', 'Pasahitzak gutxienez 6 karaktere izan behar ditu.');
      return;
    }
    if (pasahitza !== pasahitza2) {
      mostratu('profilErrorea', 'Pasahitzak ez datoz bat.');
      return;
    }
    datuak.pasahitza = pasahitza;
  }

  const botoia = document.getElementById('profilBotoia');
  botoia.disabled = true;
  try {
    const eguneratua = await api.eguneratuProfila(erabiltzaileDatuak.id_erab, datuak);
    // Pasahitzaren hash-a ez da inoiz nabigatzailean gordetzen
    const { pasahitza: _, ...segurua } = eguneratua;
    erabiltzaileaEguneratu(segurua);
    nabigazioaMarraztu('kontua.html');
    erakutsiProfila();
    mezua('Zure datuak ondo eguneratu dira.', 'success');
  } catch (errorea) {
    mostratu('profilErrorea', errorea.message);
  } finally {
    botoia.disabled = false;
  }
});

document.getElementById('saioaAmaituProfila').addEventListener('click', () => {
  saioaEzabatu();
  window.location.href = 'index.html';
});

// --------------------------------------------------------------- laguntzaileak

function mostratu(id, testua) {
  const edukiontzia = document.getElementById(id);
  edukiontzia.textContent = testua;
  edukiontzia.classList.remove('d-none');
}

function ezkutatu(id) {
  document.getElementById(id).classList.add('d-none');
}
