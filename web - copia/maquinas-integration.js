/**web/maquinas-integration.js — Integración de M5-M7 en energia.html.*/

import { fetchMaquinasInferidas } from './maquinas-service.js';
import { crearMaquinaCard } from './maquinas-badge.js';
import { mostrarModal } from './maquinas-modal.js';

/**Carga y muestra máquinas inferidas para un dispositivo.*/
async function cargarMaquinasInferidas(dispositivoId) {
	const section = document.getElementById('maquinas-section');
	const list = document.getElementById('maquinas-list');

	if (!section || !list) {
		console.warn('Elementos del DOM para máquinas no encontrados');
		return;
	}

	try {
		list.innerHTML = '<p class="muted">Cargando máquinas inferidas...</p>';
		const maquinas = await fetchMaquinasInferidas(dispositivoId);

		if (maquinas.length === 0) {
			list.innerHTML =
				'<p class="muted">No se detectaron máquinas inferidas para este dispositivo.</p>';
			section.hidden = false;
			return;
		}

		list.innerHTML = '';
		maquinas.forEach((maquina) => {
			const card = crearMaquinaCard(maquina, mostrarModal);
			list.appendChild(card);
		});

		section.hidden = false;
	} catch (err) {
		list.innerHTML = `<p class="error">Error cargando máquinas: ${err.message}</p>`;
		section.hidden = false;
	}
}

/**Hook en el formulario existente para cargar máquinas después de identificar cargas.*/
document.addEventListener('DOMContentLoaded', () => {
	const form = document.getElementById('f');
	if (!form) return;

	// Interceptar envío del formulario
	const originalSubmit = form.onsubmit;
	form.onsubmit = async (e) => {
		// Ejecutar código original si existe
		if (originalSubmit) {
			const result = originalSubmit.call(form, e);
			if (result === false) return false;
		}

		// Después de que se completen las cargas, cargar máquinas inferidas
		setTimeout(() => {
			const medidor = form.medidor?.value || 'planta_2_a';
			cargarMaquinasInferidas(medidor);
		}, 1000);

		return false;
	};
});

/**Exportar para testing.*/
export { cargarMaquinasInferidas };
