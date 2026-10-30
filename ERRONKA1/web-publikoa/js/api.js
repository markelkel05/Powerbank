// ---------------------------------------------------------------------------
// API-rekiko komunikazioa eta saioaren kudeaketa
// ---------------------------------------------------------------------------

// Backend-aren helbidea. Zerbitzaria beste portu batean badago, hemen aldatu.
export const API_OINARRIA = 'http://localhost:8000';
export const API = `${API_OINARRIA}/alokaziosistema`;

const TOKEN_GILTZA = 'kargagunea_tokena';
const ERABILTZAILE_GILTZA = 'kargagunea_erabiltzailea';

// --------------------------------------------------------------- saioa

export function tokena() {
  return localStorage.getItem(TOKEN_GILTZA);
}

export function saioaHasita() {
  return Boolean(tokena());
}

export function erabiltzailea() {
  const gordea = localStorage.getItem(ERABILTZAILE_GILTZA);
  if (!gordea) return null;
  try {
    return JSON.parse(gordea);
  } catch {
    return null;
  }
}

export function saioaGorde(token, erabiltzaileaDatuak) {
  localStorage.setItem(TOKEN_GILTZA, token);
  localStorage.setItem(ERABILTZAILE_GILTZA, JSON.stringify(erabiltzaileaDatuak));
}

export function erabiltzaileaEguneratu(erabiltzaileaDatuak) {
  localStorage.setItem(ERABILTZAILE_GILTZA, JSON.stringify(erabiltzaileaDatuak));
}

export function saioaEzabatu() {
  localStorage.removeItem(TOKEN_GILTZA);
  localStorage.removeItem(ERABILTZAILE_GILTZA);
}

// --------------------------------------------------------------- deia

/**
 * HTTP deia egiten du eta JSONa itzultzen du.
 * Errorea bada, mezua duen Error bat botatzen du (detail eremua erabiliz).
 */
export async function deia(bidea, aukerak = {}) {
  const goiburuak = new Headers(aukerak.headers || {});
  if (aukerak.body && !(aukerak.body instanceof FormData)) {
    goiburuak.set('Content-Type', 'application/json');
  }
  const t = tokena();
  if (t) goiburuak.set('Authorization', `Bearer ${t}`);

  let erantzuna;
  try {
    erantzuna = await fetch(`${API}${bidea}`, { ...aukerak, headers: goiburuak });
  } catch {
    throw new Error(
      'Ezin da zerbitzariarekin konektatu. Egiaztatu FastAPI martxan dagoela (http://localhost:8000).'
    );
  }

  if (erantzuna.status === 401 && t && !bidea.startsWith('/auth/login')) {
    saioaEzabatu();
  }

  if (!erantzuna.ok) {
    let xehetasuna = `Errorea (${erantzuna.status})`;
    try {
      const datuak = await erantzuna.json();
      if (typeof datuak.detail === 'string') {
        xehetasuna = datuak.detail;
      } else if (Array.isArray(datuak.detail)) {
        xehetasuna = datuak.detail
          .map((x) => x.msg || JSON.stringify(x))
          .join(' · ');
      }
    } catch {
      /* erantzunak ez du JSONik */
    }
    throw new Error(xehetasuna);
  }

  if (erantzuna.status === 204) return null;
  return erantzuna.json();
}

// --------------------------------------------------------------- API

function kontsulta(ezarpenak) {
  const params = new URLSearchParams();
  Object.entries(ezarpenak).forEach(([gakoa, balioa]) => {
    if (balioa !== undefined && balioa !== null && balioa !== '') {
      params.set(gakoa, balioa);
    }
  });
  const katea = params.toString();
  return katea ? `?${katea}` : '';
}

export const api = {
  kargaguneak(bilaketa = '', egoera = '') {
    return deia(`/kargaguneak${kontsulta({ bilaketa, egoera })}`);
  },

  kargagunea(id) {
    return deia(`/kargaguneak/${id}`);
  },

  erabilgarritasuna(id, hasiera, bukaera) {
    return deia(`/kargaguneak/${id}/erabilgarritasuna${kontsulta({ hasiera, bukaera })}`);
  },

  postuak(idTakilla) {
    return deia(`/postuak${kontsulta({ id_takilla: idTakilla })}`);
  },

  powerbankak(idTakilla) {
    return deia(`/powerbanks${kontsulta({ id_takilla: idTakilla })}`);
  },

  nireErreserbak() {
    return deia('/erreserbak/nireak');
  },

  sortuErreserba(datuak) {
    return deia('/erreserbak/post', {
      method: 'POST',
      body: JSON.stringify(datuak),
    });
  },

  ezeztatuErreserba(id) {
    return deia(`/erreserbak/${id}/ezeztatu`, { method: 'PATCH' });
  },

  saioaHasi(email, pasahitza) {
    return deia('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, pasahitza }),
    });
  },

  erregistratu(datuak) {
    return deia('/auth/erregistratu', {
      method: 'POST',
      body: JSON.stringify(datuak),
    });
  },

  ni() {
    return deia('/auth/ni');
  },

  eguneratuProfila(id, datuak) {
    return deia(`/erabiltzaileak/${id}/eguneratu`, {
      method: 'PATCH',
      body: JSON.stringify(datuak),
    });
  },
};

// --------------------------------------------------------------- laguntzaileak

export function irudiOsoa(url) {
  if (!url) return null;
  return url.startsWith('http') ? url : `${API_OINARRIA}${url}`;
}

export function formatuData(iso) {
  if (!iso) return '—';
  const data = new Date(iso);
  if (Number.isNaN(data.getTime())) return iso;
  return data.toLocaleString('eu-ES', { dateStyle: 'medium', timeStyle: 'short' });
}

export function dataFormularioarentzat(data = new Date()) {
  const pad = (balioa) => String(balioa).padStart(2, '0');
  return `${data.getFullYear()}-${pad(data.getMonth() + 1)}-${pad(data.getDate())}T${pad(
    data.getHours()
  )}:${pad(data.getMinutes())}`;
}

export const KARGAGUNE_EGOERA = {
  erabilgarri: { testua: 'Erabilgarri', klasea: 'bg-success-subtle text-success-emphasis' },
  mantentze_lanetan: {
    testua: 'Mantentze-lanetan',
    klasea: 'bg-warning-subtle text-warning-emphasis',
  },
  zerbitzuz_kanpo: { testua: 'Zerbitzuz kanpo', klasea: 'bg-danger-subtle text-danger-emphasis' },
};

export const ERRESERBA_EGOERA = {
  aktiboa: { testua: 'Aktiboa', klasea: 'bg-success-subtle text-success-emphasis' },
  ezeztatuta: { testua: 'Ezeztatuta', klasea: 'bg-secondary-subtle text-secondary-emphasis' },
  amaituta: { testua: 'Amaituta', klasea: 'bg-primary-subtle text-primary-emphasis' },
};
