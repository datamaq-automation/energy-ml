/**web/maquinas-badge.js — Badge visual para máquinas inferidas.*/

import { confianzaColors } from './maquinas-service.js';

/**Crea un elemento badge para una máquina.*/
export function crearBadge(maquina) {
	const confianza = maquina.confianza || 'baja';
	const colors = confianzaColors[confianza] || confianzaColors.baja;

	const badge = document.createElement('span');
	badge.className = 'badge-maquina';
	badge.style.backgroundColor = colors.bg;
	badge.style.color = colors.text;
	badge.style.padding = '0.5rem 0.75rem';
	badge.style.borderRadius = '0.375rem';
	badge.style.fontSize = '0.875rem';
	badge.style.fontWeight = '500';
	badge.style.display = 'inline-block';
	badge.title = `Confianza: ${confianza}`;
	badge.textContent = colors.badge;

	return badge;
}

/**Crea contenedor con badge + nombre carga.*/
export function crearMaquinaCard(maquina, onClickModal) {
	const card = document.createElement('div');
	card.className = 'maquina-card';
	card.style.border = '1px solid #e5e7eb';
	card.style.borderRadius = '0.5rem';
	card.style.padding = '1rem';
	card.style.marginBottom = '1rem';
	card.style.cursor = 'pointer';
	card.style.transition = 'box-shadow 0.2s';
	card.onmouseover = () => {
		card.style.boxShadow = '0 4px 6px rgba(0, 0, 0, 0.1)';
	};
	card.onmouseout = () => {
		card.style.boxShadow = 'none';
	};

	const header = document.createElement('div');
	header.style.display = 'flex';
	header.style.justifyContent = 'space-between';
	header.style.alignItems = 'center';
	header.style.marginBottom = '0.5rem';

	const nombre = document.createElement('span');
	nombre.textContent = maquina.nombre || `Carga ${maquina.id}`;
	nombre.style.fontWeight = 'bold';
	nombre.style.fontSize = '1rem';

	const badge = crearBadge(maquina);

	header.appendChild(nombre);
	header.appendChild(badge);

	const potencia = document.createElement('p');
	potencia.style.margin = '0.5rem 0 0 0';
	potencia.style.fontSize = '0.875rem';
	potencia.style.color = '#6b7280';
	potencia.textContent = `${maquina.potencia_tipica_kw} kW • ${maquina.encendidos} encendidos • ${maquina.apagados} apagados`;

	card.appendChild(header);
	card.appendChild(potencia);

	card.addEventListener('click', () => onClickModal(maquina));

	return card;
}
