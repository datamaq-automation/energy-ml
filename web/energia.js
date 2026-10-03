const f = document.getElementById('f');
f.addEventListener('submit', async (e) => {
  e.preventDefault();
  const q = new URLSearchParams(new FormData(f));
  const resumen = document.getElementById('resumen'), cont = document.getElementById('cargas');
  resumen.textContent = 'Calculando…'; cont.innerHTML = '';
  document.getElementById('saltos').hidden = true;
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
  dibujarHistograma(d.histograma, d.umbral);
  resumen.textContent = `${d.mediciones} mediciones · ${d.eventos} eventos · potencia media ${d.potencia_media_kw} kW`;
  const max = Math.max(...d.cargas.map(c => c.potencia_tipica_kw), 1);
  d.cargas.forEach(c => cont.insertAdjacentHTML('beforeend',
    `<div class="fila"><strong>${c.potencia_tipica_kw} kW</strong><div class="barra" style="width:${c.potencia_tipica_kw / max * 100}%"></div><span class="muted">↑${c.encendidos} ↓${c.apagados}</span></div>`));
  if (!d.cargas.length) cont.textContent = 'No se identificaron cargas con los parámetros actuales.';
});

// Histograma de |ΔP| con escala de raíz cuadrada: el ruido tiene miles de saltos y los eventos
// cientos; en escala lineal la montaña de los eventos no se vería.
function dibujarHistograma(barras, umbral) {
  const seccion = document.getElementById('saltos'), histo = document.getElementById('histo');
  if (!barras.length) return;
  const maximo = Math.sqrt(Math.max(...barras.map(b => b.cantidad), 1));
  const fin = barras[barras.length - 1].hasta_kw;
  histo.innerHTML = barras.map(b => {
    const tipo = umbral.kw !== null && b.desde_kw >= umbral.kw ? 'evento' : 'ruido';
    const alto = Math.sqrt(b.cantidad) / maximo * 100;
    return `<div class="col ${tipo}" style="height:${alto}%" title="${b.desde_kw}–${b.hasta_kw} kW: ${b.cantidad} saltos"></div>`;
  }).join('');
  if (umbral.kw !== null) {
    histo.insertAdjacentHTML('beforeend', `<div class="corte" style="left:${Math.min(umbral.kw / fin, 1) * 100}%"></div>`);
  }
  document.getElementById('eje-max').textContent = `≥ ${fin} kW`;
  const texto = document.getElementById('umbral');
  if (umbral.kw === null) {
    texto.textContent = 'No hay suficientes mediciones para estimar el umbral.';
  } else if (!umbral.automatico) {
    texto.textContent = `Umbral fijo por configuración: ${umbral.kw} kW.`;
  } else {
    texto.textContent = `Umbral automático (Otsu): ${umbral.kw} kW · separación η = ${umbral.separacion}`
      + (umbral.confiable ? ' — valle claro entre ruido y eventos.' : ' — ⚠ no hay un valle claro: el umbral es poco confiable.');
  }
  texto.className = umbral.confiable === false ? 'aviso' : 'muted';
  seccion.hidden = false;
}
