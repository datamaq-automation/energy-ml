const API = "/api/sibo";

const estado = {
  alimentos: [],
  rango: "dia",
  registros: [],
  ultimaSerie: null,
};

const $ = (selector) => document.querySelector(selector);

function dosDigitos(valor) {
  return String(valor).padStart(2, "0");
}

function hoyISO() {
  const fecha = new Date();
  return `${fecha.getFullYear()}-${dosDigitos(fecha.getMonth() + 1)}-${dosDigitos(fecha.getDate())}`;
}

function ahoraLocal() {
  const fecha = new Date();
  fecha.setMinutes(fecha.getMinutes() - fecha.getTimezoneOffset());
  return fecha.toISOString().slice(0, 16);
}

function escapar(texto) {
  return String(texto)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function mostrarMensaje(texto, tipo = "") {
  const mensaje = $("#mensaje");
  mensaje.textContent = texto;
  mensaje.className = `mensaje ${tipo}`;
}

async function pedir(url, opciones = {}) {
  const respuesta = await fetch(url, opciones);
  if (!respuesta.ok) {
    let detalle = `Error ${respuesta.status}`;
    try {
      const cuerpo = await respuesta.json();
      if (cuerpo.detail) {
        detalle = typeof cuerpo.detail === "string" ? cuerpo.detail : JSON.stringify(cuerpo.detail);
      }
    } catch (_error) {
      // Sin cuerpo JSON: se conserva el código de estado.
    }
    throw new Error(detalle);
  }
  if (respuesta.status === 204) {
    return null;
  }
  return respuesta.json();
}

function cambiarVista(nombre) {
  document.querySelectorAll(".pestanas button").forEach((boton) => {
    boton.classList.toggle("activa", boton.dataset.vista === nombre);
  });
  document.querySelectorAll(".vista").forEach((vista) => {
    vista.classList.toggle("activa", vista.id === `vista-${nombre}`);
  });
  if (nombre === "curva") {
    cargarCurva();
  }
  if (nombre === "recomendaciones") {
    cargarRecomendaciones();
  }
}

async function cargarAlimentos() {
  estado.alimentos = await pedir(`${API}/alimentos`);
  const select = $("#alimento");
  select.innerHTML = "";
  estado.alimentos.forEach((alimento) => {
    const opcion = document.createElement("option");
    opcion.value = alimento.id;
    opcion.textContent = `${alimento.nombre} · ${alimento.categoria}`;
    select.appendChild(opcion);
  });
}

function fichaFodmap(nivel) {
  return `<span class="ficha ${escapar(nivel)}">FODMAP ${escapar(nivel)}</span>`;
}

function formatearFecha(iso) {
  const fecha = new Date(iso);
  return fecha.toLocaleString([], {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function renderizarRegistros(registros) {
  const lista = $("#lista-registros");
  if (!registros.length) {
    lista.innerHTML = '<li class="vacio">Todavía no registraste comidas.</li>';
    return;
  }
  lista.innerHTML = registros
    .slice()
    .reverse()
    .slice(0, 20)
    .map(
      (registro) => `
        <li>
          <div class="registro-info">
            <strong>${escapar(registro.alimento_nombre)} · ${registro.porcion_g} g</strong>
            <span>${formatearFecha(registro.fecha_hora)} · síntomas ${registro.sintomas}/10</span>
            <span>${fichaFodmap(registro.fodmap)}</span>
          </div>
          <button class="boton-eliminar" data-id="${registro.id}" type="button">Eliminar</button>
        </li>
      `,
    )
    .join("");
}

async function cargarRegistros() {
  estado.registros = await pedir(`${API}/registros`);
  renderizarRegistros(estado.registros);
}

async function eliminarRegistro(id) {
  try {
    await pedir(`${API}/registros/${id}`, { method: "DELETE" });
    mostrarMensaje("Registro eliminado.", "ok");
    await Promise.all([cargarRegistros(), cargarCurva(), cargarRecomendaciones()]);
  } catch (error) {
    mostrarMensaje(error.message, "error");
  }
}

function dibujar(serie) {
  const canvas = $("#grafico");
  const contexto = canvas.getContext("2d");
  const dpr = window.devicePixelRatio || 1;
  const ancho = canvas.clientWidth || canvas.parentElement.clientWidth;
  const alto = 320;
  canvas.width = ancho * dpr;
  canvas.height = alto * dpr;
  contexto.setTransform(dpr, 0, 0, dpr, 0, 0);
  contexto.clearRect(0, 0, ancho, alto);

  const puntos = serie.puntos;
  if (!puntos.length) {
    return;
  }

  const margen = { arriba: 16, derecha: 18, abajo: 38, izquierda: 42 };
  const anchoUtil = ancho - margen.izquierda - margen.derecha;
  const altoUtil = alto - margen.arriba - margen.abajo;
  const maxY = 100;
  const x = (indice) => margen.izquierda + (indice / Math.max(puntos.length - 1, 1)) * anchoUtil;
  const y = (valor) => margen.arriba + (1 - valor / maxY) * altoUtil;

  contexto.font = "11px system-ui, sans-serif";
  contexto.lineWidth = 1;
  contexto.strokeStyle = "#dbe7ea";
  contexto.fillStyle = "#5b7180";
  for (let valor = 0; valor <= maxY; valor += 25) {
    const posicion = y(valor);
    contexto.beginPath();
    contexto.moveTo(margen.izquierda, posicion);
    contexto.lineTo(ancho - margen.derecha, posicion);
    contexto.stroke();
    contexto.fillText(String(valor), 8, posicion + 4);
  }

  contexto.beginPath();
  puntos.forEach((punto, indice) => {
    const posicion = y(punto.nivel_alto);
    if (indice === 0) {
      contexto.moveTo(x(indice), posicion);
    } else {
      contexto.lineTo(x(indice), posicion);
    }
  });
  for (let indice = puntos.length - 1; indice >= 0; indice -= 1) {
    contexto.lineTo(x(indice), y(puntos[indice].nivel_bajo));
  }
  contexto.closePath();
  contexto.fillStyle = "rgba(22, 125, 110, 0.14)";
  contexto.fill();

  contexto.beginPath();
  puntos.forEach((punto, indice) => {
    const posicion = y(punto.nivel_estimado);
    if (indice === 0) {
      contexto.moveTo(x(indice), posicion);
    } else {
      contexto.lineTo(x(indice), posicion);
    }
  });
  contexto.strokeStyle = "#0f6f8f";
  contexto.lineWidth = 2.5;
  contexto.lineJoin = "round";
  contexto.stroke();

  const indicesEtiqueta = Array.from(
    new Set([0, Math.floor(puntos.length / 4), Math.floor(puntos.length / 2), Math.floor((puntos.length * 3) / 4), puntos.length - 1]),
  );
  contexto.fillStyle = "#5b7180";
  indicesEtiqueta.forEach((indice) => {
    const fecha = new Date(puntos[indice].instante);
    const etiqueta =
      serie.rango === "dia"
        ? fecha.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
        : fecha.toLocaleDateString([], { day: "2-digit", month: "2-digit" });
    const texto = contexto.measureText(etiqueta).width;
    contexto.fillText(etiqueta, Math.min(Math.max(x(indice) - texto / 2, 0), ancho - texto), alto - 14);
  });
}

async function cargarCurva() {
  const fecha = $("#fecha-curva").value || hoyISO();
  const parametros = new URLSearchParams({ rango: estado.rango, fecha });
  try {
    const serie = await pedir(`${API}/gases?${parametros.toString()}`);
    estado.ultimaSerie = serie;
    dibujar(serie);
    $("#promedio").textContent = serie.promedio;
    $("#pico").textContent = serie.pico;

    const registros = await pedir(
      `${API}/registros?${new URLSearchParams({ desde: serie.desde, hasta: serie.hasta }).toString()}`,
    );
    $("#total-registros").textContent = registros.length;
  } catch (error) {
    mostrarMensaje(`No se pudo cargar la curva: ${error.message}`, "error");
  }
}

function renderizarRecomendaciones(recomendaciones) {
  const contenedor = $("#recomendaciones");
  if (!recomendaciones.length) {
    contenedor.innerHTML = '<p class="nota">No hay recomendaciones disponibles.</p>';
    return;
  }
  contenedor.innerHTML = recomendaciones
    .map(
      (recomendacion) => `
        <article class="recomendacion">
          <h3>${escapar(recomendacion.alimento.nombre)}</h3>
          <div class="categoria">${escapar(recomendacion.alimento.categoria)}</div>
          <p>${escapar(recomendacion.motivo)}</p>
          <div class="puntaje">Puntaje de idoneidad: ${recomendacion.puntaje}</div>
          <p>${fichaFodmap(recomendacion.alimento.fodmap)} · Desinflamatorio ${recomendacion.alimento.score_desinflamatorio}/10</p>
        </article>
      `,
    )
    .join("");
}

async function cargarRecomendaciones() {
  try {
    const recomendaciones = await pedir(`${API}/recomendaciones?limite=8`);
    renderizarRecomendaciones(recomendaciones);
  } catch (error) {
    mostrarMensaje(`No se pudieron cargar las recomendaciones: ${error.message}`, "error");
  }
}

function configurarEventos() {
  document.querySelectorAll(".pestanas button").forEach((boton) => {
    boton.addEventListener("click", () => cambiarVista(boton.dataset.vista));
  });

  $("#sintomas").addEventListener("input", (evento) => {
    $("#sintomas-valor").textContent = evento.target.value;
  });

  $("#form-registro").addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const cuerpo = {
      alimento_id: Number($("#alimento").value),
      porcion_g: Number($("#porcion").value),
      fecha_hora: $("#fecha").value || null,
      sintomas: Number($("#sintomas").value),
      notas: $("#notas").value,
    };
    try {
      await pedir(`${API}/registros`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(cuerpo),
      });
      mostrarMensaje("Comida registrada correctamente.", "ok");
      $("#notas").value = "";
      $("#sintomas").value = "0";
      $("#sintomas-valor").textContent = "0";
      await Promise.all([cargarRegistros(), cargarCurva(), cargarRecomendaciones()]);
    } catch (error) {
      mostrarMensaje(`No se pudo registrar: ${error.message}`, "error");
    }
  });

  $("#lista-registros").addEventListener("click", (evento) => {
    const boton = evento.target.closest(".boton-eliminar");
    if (boton) {
      eliminarRegistro(boton.dataset.id);
    }
  });

  $("#recargar-registros").addEventListener("click", cargarRegistros);
  $("#recargar-recomendaciones").addEventListener("click", cargarRecomendaciones);
  $("#fecha-curva").addEventListener("change", cargarCurva);

  $("#rango").addEventListener("click", (evento) => {
    const boton = evento.target.closest("button[data-rango]");
    if (!boton) {
      return;
    }
    estado.rango = boton.dataset.rango;
    document.querySelectorAll("#rango button").forEach((opcion) => {
      opcion.classList.toggle("activa", opcion === boton);
    });
    cargarCurva();
  });

  let temporizador = null;
  window.addEventListener("resize", () => {
    clearTimeout(temporizador);
    temporizador = setTimeout(() => {
      if (estado.ultimaSerie) {
        dibujar(estado.ultimaSerie);
      }
    }, 150);
  });
}

async function iniciar() {
  $("#fecha").value = ahoraLocal();
  $("#fecha-curva").value = hoyISO();
  configurarEventos();
  try {
    await cargarAlimentos();
    await Promise.all([cargarRegistros(), cargarCurva(), cargarRecomendaciones()]);
  } catch (error) {
    mostrarMensaje(`No se pudo conectar con el servicio: ${error.message}`, "error");
  }
}

iniciar();
