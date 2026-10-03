const f = document.getElementById('f');
f.addEventListener('submit', async (e) => {
  e.preventDefault();
  const q = new URLSearchParams(new FormData(f));
  const resumen = document.getElementById('resumen'), cont = document.getElementById('cargas');
  resumen.textContent = 'Calculando…'; cont.innerHTML = '';
  let d;
  try {
    const r = await fetch(`/api/v1/identify-loads?${q}`);
    if (!r.ok) {
      const err = await r.json().catch(() => ({}));
      resumen.textContent = typeof err.detail === 'string' ? `Error ${r.status}: ${err.detail}` : `Error ${r.status}`;
      return;
    }
    d = await r.json();
  } catch {
    resumen.textContent = 'No se pudo contactar al servidor.';
    return;
  }
  resumen.textContent = `${d.mediciones} mediciones · ${d.eventos} eventos · potencia media ${d.potencia_media_kw} kW`;
  const max = Math.max(...d.cargas.map(c => c.potencia_tipica_kw), 1);
  d.cargas.forEach(c => cont.insertAdjacentHTML('beforeend',
    `<div class="fila"><strong>${c.potencia_tipica_kw} kW</strong><div class="barra" style="width:${c.potencia_tipica_kw / max * 100}%"></div><span class="muted">↑${c.encendidos} ↓${c.apagados}</span></div>`));
  if (!d.cargas.length) cont.textContent = 'No se identificaron cargas con los parámetros actuales.';
});
