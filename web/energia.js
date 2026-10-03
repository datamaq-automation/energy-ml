const f = document.getElementById('f');
const kw = (v) => `${Number(v).toLocaleString('es-AR', { maximumFractionDigits: 1 })} kW`;
const numero = (v) => Number(v).toLocaleString('es-AR');
const kpi = (valor, etiqueta) => `<div class="kpi"><strong>${valor}</strong><span>${etiqueta}</span></div>`;

f.addEventListener('submit', async (e) => {
  e.preventDefault();
  const q = new URLSearchParams(new FormData(f));
  const estado = document.getElementById('estado'), resultado = document.getElementById('resultado');
  estado.textContent = 'Calculando…'; estado.className = 'muted'; resultado.hidden = true;
  let d;
  try {
    const r = await fetch(`/api/v1/identify-loads?${q}`);
    if (!r.ok) {
      const err = await r.json().catch(() => ({}));
      estado.textContent = typeof err.detail === 'string' ? `Error ${r.status}: ${err.detail}` : `Error ${r.status}`;
      estado.className = 'aviso';
      return;
    }
    d = await r.json();
  } catch {
    estado.textContent = 'No se pudo contactar al servidor.'; estado.className = 'aviso';
    return;
  }
  estado.textContent = `Resultado para ${d.medidor}, en el mismo orden en que lo calcula el sistema:`;
  dibujarDatos(d);
  dibujarHistograma(d.histograma, d.umbral);
  dibujarEventos(d);
  dibujarCargas(d.cargas, d.umbral);
  resultado.hidden = false;
});

function dibujarDatos(d) {
  document.getElementById('kpi-datos').innerHTML =
    kpi(d.mediciones.toLocaleString('es-AR'), 'mediciones')
    + kpi(d.dias.toLocaleString('es-AR'), 'días')
    + kpi(kw(d.potencia_media_kw), 'potencia media');
}

function dibujarEventos(d) {
  document.getElementById('kpi-eventos').innerHTML =
    kpi(d.eventos.toLocaleString('es-AR'), 'eventos (saltos ≥ umbral)')
    + kpi(`↑ ${d.encendidos}`, 'encendidos')
    + kpi(`↓ ${d.apagados}`, 'apagados')
    + kpi(d.eventos_sin_grupo, 'sin grupo (ruido)')
    + (d.agrupamiento.radio_kw === null ? '' : kpi(kw(d.agrupamiento.radio_kw), `radio de agrupamiento (${d.agrupamiento.radio_automatico ? 'automático' : 'fijo'})`))
    + kpi(d.agrupamiento.min_eventos, `eventos mínimos por carga (${d.agrupamiento.min_eventos_automatico ? 'automático' : 'fijo'})`);
}

function frecuencia(c) {
  if (c.ciclos_por_dia === null) return '';
  return c.ciclos_por_dia >= 1
    ? `: unas <strong>${Math.round(c.ciclos_por_dia)} veces por día</strong>`
    : `: unas <strong>${(c.ciclos_por_dia * 7).toFixed(1)} veces por semana</strong>`;
}

function dibujarCargas(cargas, umbral) {
  const cont = document.getElementById('cargas');
  if (!cargas.length) {
    cont.innerHTML = '<p class="aviso">No se identificaron cargas: ningún grupo de eventos alcanzó el mínimo.</p>';
    return;
  }
  // Primero las que se comportan como un equipo ON/OFF; dentro de cada grupo, de mayor a menor potencia.
  const ordenadas = [...cargas].sort((a, b) => (b.on_off - a.on_off) || (b.potencia_tipica_kw - a.potencia_tipica_kw));
  const dudaUmbral = umbral.confiable === false
    ? '<p class="aviso">⚠ El umbral es dudoso (paso 2): esta potencia puede estar mezclada con ruido.</p>' : '';
  cont.innerHTML = ordenadas.map(c => `
    <article class="carga${c.on_off ? '' : ' dudosa'}">
      <div class="potencia">≈ ${kw(c.potencia_tipica_kw)}</div>
      <div>
        <p>Se encendió <strong>${c.encendidos}</strong> veces y se apagó <strong>${c.apagados}</strong>${c.on_off ? frecuencia(c) : ''}.</p>
        ${c.on_off
          ? '<p class="muted">Se comporta como un equipo que se prende y se apaga.</p>'
          : '<p class="aviso">⚠ Dudosa: los encendidos y apagados no coinciden, probablemente no es un único equipo.</p>'}
        ${c.on_off ? dudaUmbral : ''}
      </div>
    </article>`).join('');
}

// Histograma de |ΔP| con escala de raíz cuadrada: el ruido tiene miles de saltos y los eventos
// cientos; en escala lineal la montaña de los eventos no se vería.
function dibujarHistograma(barras, umbral) {
  const histo = document.getElementById('histo');
  histo.innerHTML = '';
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
  document.getElementById('eje-max').textContent = `≥ ${kw(fin)}`;
  const texto = document.getElementById('umbral');
  if (umbral.kw === null) {
    texto.textContent = 'No hay suficientes mediciones para estimar el umbral.';
  } else if (!umbral.automatico) {
    texto.innerHTML = `Umbral <strong>${kw(umbral.kw)}</strong> (fijado por configuración).`;
  } else if (umbral.confiable) {
    texto.innerHTML = `Umbral automático: <strong>${kw(umbral.kw)}</strong>. Hay un valle claro entre ruido y eventos (separación η = ${numero(umbral.separacion)}).`;
  } else {
    texto.innerHTML = `⚠ Umbral automático: <strong>${kw(umbral.kw)}</strong>, pero <strong>no hay un valle claro</strong> entre ruido y eventos (separación η = ${numero(umbral.separacion)}, menor a 0,8). Tomá los resultados con cuidado.`;
  }
  texto.className = umbral.confiable === false ? 'aviso' : '';
}
