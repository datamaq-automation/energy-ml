/**web/maquinas-service.js — Servicio para máquinas inferidas por NILM.*/

/**Fetch máquinas inferidas desde backend.*/
export async function fetchMaquinasInferidas(dispositivo_id) {
	try {
		const res = await fetch(
			`/api/v1/dispositivos/${dispositivo_id}/maquinas/inferidas`
		);
		if (!res.ok) {
			if (res.status === 404) {
				throw new Error(`Dispositivo '${dispositivo_id}' sin análisis NILM`);
			}
			if (res.status === 503) {
				throw new Error('Cache de datos vacío o desactualizado');
			}
			throw new Error(`Error ${res.status}: ${res.statusText}`);
		}
		const data = await res.json();
		return data.maquinas_inferidas || [];
	} catch (err) {
		console.error('fetchMaquinasInferidas error:', err);
		throw err;
	}
}

/**Colores por nivel de confianza.*/
export const confianzaColors = {
	alta: { bg: '#D1FAE5', text: '#065F46', badge: '🤖 Alta' },
	media: { bg: '#FEF3C7', text: '#92400E', badge: '🤖 Media' },
	baja: { bg: '#F3F4F6', text: '#374151', badge: '🤖 Baja' },
};

/**Carga una máquina inferida en localStorage.*/
export function guardarFeedback(cargaId, feedback) {
	const datos = JSON.parse(localStorage.getItem('feedback') || '{}');
	datos[cargaId] = feedback; // 'aceptado', 'rechazado', 'revisar_despues'
	localStorage.setItem('feedback', JSON.stringify(datos));
}

/**Lee feedback de una carga desde localStorage.*/
export function leerFeedback(cargaId) {
	const datos = JSON.parse(localStorage.getItem('feedback') || '{}');
	return datos[cargaId] || null;
}
