// Renderiza docs/guia-docente.md: el Markdown es la única fuente (también se lee en GitHub).
(async () => {
  const destino = document.getElementById('guia');
  try {
    const r = await fetch('/guia/guia-docente.md');
    if (!r.ok) throw new Error(`Error ${r.status}`);
    const markdown = await r.text();
    // DOMPurify limpia el HTML generado para que el Markdown no pueda ejecutar scripts.
    destino.innerHTML = DOMPurify.sanitize(marked.parse(markdown));
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
      ? 'No se pudo cargar el visor de Markdown (¿sin internet?). La guía está en docs/guia-docente.md.'
      : `No se pudo cargar la guía: ${e.message}`;
    destino.appendChild(p);
  }
})();
