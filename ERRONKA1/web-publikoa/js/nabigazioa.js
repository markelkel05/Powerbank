// ---------------------------------------------------------------------------
// Goiburuko nabigazioa eta mezu orokorrak
// ---------------------------------------------------------------------------

import { erabiltzailea, saioaEzabatu, saioaHasita } from './api.js';

export function ihes(testua) {
  return String(testua ?? '').replace(
    /[&<>"']/g,
    (karakterea) =>
      ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;',
      })[karakterea]
  );
}

export function nabigazioaMarraztu(aktiboa = 'index.html') {
  const edukiontzia = document.getElementById('goiburu-nabigazioa');
  if (!edukiontzia) return;

  const lotura = (bidea, izena) => `
    <li class="nav-item">
      <a class="nav-link ${bidea === aktiboa ? 'active' : ''}" href="${bidea}">${izena}</a>
    </li>`;

  const saioAtala = saioaHasita()
    ? `
      <div class="dropdown">
        <button class="btn btn-outline-light dropdown-toggle" data-bs-toggle="dropdown">
          <i class="bi bi-person-circle me-1"></i>${ihes(
            erabiltzailea()?.izena || 'Nire kontua'
          )}
        </button>
        <ul class="dropdown-menu dropdown-menu-end">
          <li><a class="dropdown-item" href="kontua.html"><i class="bi bi-person me-2"></i>Nire datuak</a></li>
          <li><a class="dropdown-item" href="erreserbak.html"><i class="bi bi-calendar-check me-2"></i>Nire erreserbak</a></li>
          <li><hr class="dropdown-divider"></li>
          <li><button class="dropdown-item text-danger" id="saioaAmaitu"><i class="bi bi-box-arrow-right me-2"></i>Saioa amaitu</button></li>
        </ul>
      </div>`
    : `<a class="btn btn-light fw-semibold" href="kontua.html"><i class="bi bi-box-arrow-in-right me-1"></i>Saioa hasi</a>`;

  edukiontzia.innerHTML = `
    <nav class="navbar navbar-expand-lg nabigazioa">
      <div class="container">
        <a class="navbar-brand text-white fw-bold" href="index.html">
          <i class="bi bi-lightning-charge-fill me-1"></i>KargaGunea
        </a>
        <button class="navbar-toggler border-0" type="button" data-bs-toggle="collapse"
          data-bs-target="#nabigazioEdukia" aria-controls="nabigazioEdukia"
          aria-expanded="false" aria-label="Nabigazioa">
          <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="nabigazioEdukia">
          <ul class="navbar-nav me-auto mb-2 mb-lg-0">
            ${lotura('index.html', 'Kargaguneak')}
            ${lotura('erreserbak.html', 'Nire erreserbak')}
          </ul>
          <div class="d-flex align-items-center gap-2">${saioAtala}</div>
        </div>
      </div>
    </nav>`;

  document.getElementById('saioaAmaitu')?.addEventListener('click', () => {
    saioaEzabatu();
    window.location.href = 'index.html';
  });
}

/**
 * Mezu bat erakusten du orriaren goialdean.
 * @param {string} testua
 * @param {'success'|'danger'|'warning'|'info'} mota
 */
export function mezua(testua, mota = 'success') {
  const edukiontzia = document.getElementById('jakinarazpenak');
  if (!edukiontzia) return;

  const alerta = document.createElement('div');
  alerta.className = `alert alert-${mota} alert-dismissible shadow-sm fade show`;
  alerta.setAttribute('role', 'alert');
  alerta.innerHTML = `${ihes(testua)}
    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Itxi"></button>`;

  edukiontzia.appendChild(alerta);
  if (mota === 'success') {
    setTimeout(() => alerta.remove(), 6000);
  }
  window.scrollTo({ top: 0, behavior: 'smooth' });
}
