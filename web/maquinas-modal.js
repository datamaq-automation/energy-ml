/**web/maquinas-modal.js — Modal detalles + feedback para máquinas inferidas.*/

import { confianzaColors, guardarFeedback, leerFeedback } from './maquinas-service.js';

/**Crea y muestra modal con detalles de una máquina.*/
export function mostrarModal(maquina) {
	// Remover modal anterior si existe
	const existing = document.getElementById('modal-maquinas');
	if (existing) existing.remove();

	const overlay = document.createElement('div');
	overlay.id = 'modal-overlay';
	overlay.style.position = 'fixed';
	overlay.style.top = '0';
	overlay.style.left = '0';
	overlay.style.width = '100%';
	overlay.style.height = '100%';
	overlay.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
	overlay.style.display = 'flex';
	overlay.style.alignItems = 'center';
	overlay.style.justifyContent = 'center';
	overlay.style.zIndex = '1000';

	const modal = document.createElement('div');
	modal.id = 'modal-maquinas';
	modal.style.backgroundColor = 'white';
	modal.style.borderRadius = '0.5rem';
	modal.style.padding = '2rem';
	modal.style.maxWidth = '500px';
	modal.style.boxShadow = '0 20px 25px rgba(0, 0, 0, 0.15)';
	modal.style.zIndex = '1001';

	// Header
	const header = document.createElement('div');
	header.style.marginBottom = '1.5rem';
	header.style.display = 'flex';
	header.style.justifyContent = 'space-between';
	header.style.alignItems = 'start';

	const title = document.createElement('h2');
	title.style.margin = '0';
	title.style.fontSize = '1.25rem';
	title.textContent = maquina.nombre || `Carga ${maquina.id}`;

	const closeBtn = document.createElement('button');
	closeBtn.textContent = '✕';
	closeBtn.style.background = 'none';
	closeBtn.style.border = 'none';
	closeBtn.style.fontSize = '1.5rem';
	closeBtn.style.cursor = 'pointer';
	closeBtn.style.padding = '0';
	closeBtn.onclick = () => overlay.remove();

	header.appendChild(title);
	header.appendChild(closeBtn);

	// Detalles
	const details = document.createElement('table');
	details.style.width = '100%';
	details.style.marginBottom = '1.5rem';
	details.style.fontSize = '0.875rem';

	const confianza = maquina.confianza || 'baja';
	const colors = confianzaColors[confianza];

	const rows = [
		['Confianza', `🤖 ${confianza.charAt(0).toUpperCase() + confianza.slice(1)}`, colors.bg],
		['Potencia', `${maquina.potencia_tipica_kw} kW`, '#f9fafb'],
		['Encendidos', maquina.encendidos, '#f9fafb'],
		['Apagados', maquina.apagados, '#f9fafb'],
		['Dispersión', `${maquina.dispersion_kw} kW`, '#f9fafb'],
		['Ciclos/día', maquina.ciclos_por_dia?.toFixed(1) || '—', '#f9fafb'],
	];

	rows.forEach(([label, value, bg]) => {
		const row = details.insertRow();
		row.style.backgroundColor = bg;
		const labelCell = row.insertCell();
		const valueCell = row.insertCell();
		labelCell.textContent = label;
		valueCell.textContent = value;
		labelCell.style.padding = '0.5rem';
		valueCell.style.padding = '0.5rem';
		labelCell.style.fontWeight = 'bold';
	});

	// Botones feedback
	const buttonContainer = document.createElement('div');
	buttonContainer.style.display = 'flex';
	buttonContainer.style.gap = '0.75rem';
	buttonContainer.style.justifyContent = 'flex-end';

	const feedback = leerFeedback(maquina.id);

	const btnAceptar = crearBotonFeedback(
		'✓ Aceptar',
		'aceptado',
		maquina.id,
		overlay,
		feedback
	);
	const btnRechazar = crearBotonFeedback(
		'✗ Rechazar',
		'rechazado',
		maquina.id,
		overlay,
		feedback
	);
	const btnRevisar = crearBotonFeedback(
		'⏱ Revisar después',
		'revisar_despues',
		maquina.id,
		overlay,
		feedback
	);

	buttonContainer.appendChild(btnAceptar);
	buttonContainer.appendChild(btnRechazar);
	buttonContainer.appendChild(btnRevisar);

	modal.appendChild(header);
	modal.appendChild(details);
	modal.appendChild(buttonContainer);
	overlay.appendChild(modal);

	// Cerrar al hacer click fuera
	overlay.addEventListener('click', (e) => {
		if (e.target === overlay) overlay.remove();
	});

	document.body.appendChild(overlay);
}

/**Crea botón de feedback.*/
function crearBotonFeedback(label, tipo, cargaId, overlay, feedbackActual) {
	const btn = document.createElement('button');
	btn.textContent = label;
	btn.style.padding = '0.5rem 1rem';
	btn.style.borderRadius = '0.375rem';
	btn.style.border = 'none';
	btn.style.cursor = 'pointer';
	btn.style.fontSize = '0.875rem';
	btn.style.fontWeight = '500';
	btn.style.transition = 'all 0.2s';

	const isSelected = feedbackActual === tipo;

	if (isSelected) {
		btn.style.backgroundColor = '#10b981';
		btn.style.color = 'white';
	} else {
		btn.style.backgroundColor = '#f3f4f6';
		btn.style.color = '#374151';
		btn.onmouseover = () => {
			btn.style.backgroundColor = '#e5e7eb';
		};
		btn.onmouseout = () => {
			btn.style.backgroundColor = '#f3f4f6';
		};
	}

	btn.onclick = (e) => {
		e.preventDefault();
		guardarFeedback(cargaId, tipo);
		// Mostrar confirmación
		const msg = document.createElement('div');
		msg.textContent = `Feedback guardado: ${label}`;
		msg.style.position = 'fixed';
		msg.style.bottom = '1rem';
		msg.style.right = '1rem';
		msg.style.backgroundColor = '#10b981';
		msg.style.color = 'white';
		msg.style.padding = '1rem';
		msg.style.borderRadius = '0.375rem';
		msg.style.zIndex = '2000';
		document.body.appendChild(msg);
		setTimeout(() => msg.remove(), 2000);
		// Cerrar modal
		overlay.remove();
	};

	return btn;
}
