// Renderiza docs/cuaderno-alumno.md: el Markdown es la única fuente (también se lee en GitHub).
(async () => {
  const destino = document.getElementById('guia');
  try {
    const r = await fetch('/guia/cuaderno-alumno.md');
    if (!r.ok) throw new Error(`Error ${r.status}`);
    const markdown = await r.text();
    // DOMPurify limpia el HTML generado para que el Markdown no pueda ejecutar scripts.
    destino.innerHTML = DOMPurify.sanitize(marked.parse(markdown));
    // Mismos id que GitHub ("## 14. Ejercicios" → "14-ejercicios") para que los enlaces internos anden en ambos lados.
    destino.querySelectorAll('h1, h2, h3').forEach(h => {
      h.id = h.textContent.trim().toLowerCase().replace(/[^\p{L}\p{N}\s-]/gu, '').replace(/\s/g, '-');
    });
    // La guía se dibuja después de cargar la página: hay que saltar al ancla a mano.
    if (location.hash) document.getElementById(decodeURIComponent(location.hash.slice(1)))?.scrollIntoView();
    // Los enlaces relativos del .md apuntan a archivos del repo: en la web se abren en GitHub.
    destino.querySelectorAll('a[href]').forEach(a => {
      const href = a.getAttribute('href');
      if (!/^(https?:|#|\/)/.test(href)) {
        a.href = `https://github.com/datamaq-automation/energy-ml/blob/main/docs/${href}`;
      }
    });
  } catch (e) {
    destino.innerHTML = '';
    const p = document.createElement('p');
    p.textContent = typeof marked === 'undefined'
      ? 'No se pudo cargar el visor de Markdown (¿sin internet?). El cuaderno está en docs/cuaderno-alumno.md.'
      : `No se pudo cargar la guía: ${e.message}`;
    destino.appendChild(p);
  }
})();
