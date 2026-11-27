/**web/maquinas.test.js — E2E tests para M5-M7 Frontend.*/

import { fetchMaquinasInferidas, guardarFeedback, leerFeedback } from './maquinas-service.js';
import { crearBadge, crearMaquinaCard } from './maquinas-badge.js';

describe('M5: Servicio API (fetchMaquinasInferidas)', () => {
	test('fetch válido retorna lista de máquinas', async () => {
		// Mock endpoint: /api/v1/dispositivos/planta_2_a/maquinas/inferidas
		const maquinas = await fetchMaquinasInferidas('planta_2_a');
		expect(Array.isArray(maquinas)).toBe(true);
		if (maquinas.length > 0) {
			expect(maquinas[0]).toHaveProperty('id');
			expect(maquinas[0]).toHaveProperty('confianza');
		}
	});

	test('fetch dispositivo inexistente lanza error 404', async () => {
		try {
			await fetchMaquinasInferidas('inexistente');
			fail('Debería haber lanzado error');
		} catch (err) {
			expect(err.message).toContain('sin análisis NILM');
		}
	});

	test('guardarFeedback guarda en localStorage', () => {
		guardarFeedback('carga_001', 'aceptado');
		const feedback = leerFeedback('carga_001');
		expect(feedback).toBe('aceptado');
	});

	test('leerFeedback retorna null si no existe', () => {
		const feedback = leerFeedback('carga_inexistente');
		expect(feedback).toBeNull();
	});
});

describe('M6: Badge Visual', () => {
	test('crearBadge genera elemento con confianza alta', () => {
		const maquina = {
			id: 'carga_001',
			confianza: 'alta',
			nombre: 'Bomba A',
		};
		const badge = crearBadge(maquina);
		expect(badge.textContent).toContain('🤖');
		expect(badge.textContent).toContain('Alta');
	});

	test('crearBadge genera elemento con confianza media', () => {
		const maquina = {
			id: 'carga_002',
			confianza: 'media',
		};
		const badge = crearBadge(maquina);
		expect(badge.textContent).toContain('Media');
	});

	test('crearBadge genera elemento con confianza baja', () => {
		const maquina = {
			id: 'carga_003',
			confianza: 'baja',
		};
		const badge = crearBadge(maquina);
		expect(badge.textContent).toContain('Baja');
	});

	test('crearMaquinaCard es clickeable', () => {
		const maquina = {
			id: 'carga_001',
			nombre: 'Bomba A',
			confianza: 'alta',
			potencia_tipica_kw: 92.5,
			encendidos: 412,
			apagados: 380,
		};
		let clicked = false;
		const card = crearMaquinaCard(maquina, () => {
			clicked = true;
		});
		card.click();
		expect(clicked).toBe(true);
	});
});

describe('M7: Modal + Feedback', () => {
	test('feedback se guarda y recupera desde localStorage', () => {
		const cargaId = 'carga_test_001';
		guardarFeedback(cargaId, 'aceptado');
		expect(leerFeedback(cargaId)).toBe('aceptado');

		guardarFeedback(cargaId, 'rechazado');
		expect(leerFeedback(cargaId)).toBe('rechazado');

		guardarFeedback(cargaId, 'revisar_despues');
		expect(leerFeedback(cargaId)).toBe('revisar_despues');
	});

	test('feedback múltiples cargas se guardan independientemente', () => {
		guardarFeedback('carga_001', 'aceptado');
		guardarFeedback('carga_002', 'rechazado');

		expect(leerFeedback('carga_001')).toBe('aceptado');
		expect(leerFeedback('carga_002')).toBe('rechazado');
	});
});

describe('Integración Frontend-Backend', () => {
	test('badge colors se aplican correctamente por confianza', () => {
		const maquinaAlta = { confianza: 'alta' };
		const badgeAlta = crearBadge(maquinaAlta);
		expect(badgeAlta.style.backgroundColor).toBe('#D1FAE5');

		const maquinaMedia = { confianza: 'media' };
		const badgeMedia = crearBadge(maquinaMedia);
		expect(badgeMedia.style.backgroundColor).toBe('#FEF3C7');

		const maquinaBaja = { confianza: 'baja' };
		const badgeBaja = crearBadge(maquinaBaja);
		expect(badgeBaja.style.backgroundColor).toBe('#F3F4F6');
	});

	test('card muestra nombre o id por defecto', () => {
		const maquinaConNombre = {
			id: 'c1',
			nombre: 'Bomba A',
			confianza: 'alta',
			potencia_tipica_kw: 92.5,
			encendidos: 100,
			apagados: 100,
		};
		const cardConNombre = crearMaquinaCard(maquinaConNombre, () => {});
		expect(cardConNombre.textContent).toContain('Bomba A');

		const maquinaSinNombre = {
			id: 'c2',
			confianza: 'baja',
			potencia_tipica_kw: 45.0,
			encendidos: 50,
			apagados: 50,
		};
		const cardSinNombre = crearMaquinaCard(maquinaSinNombre, () => {});
		expect(cardSinNombre.textContent).toContain('Carga c2');
	});
});
