"""Servicio de dominio para procesamiento y filtrado de señales de potencia."""

def calcular_consumo_activo(potencia_w: float, tiempo_horas: float) -> float:
    """Calcula el consumo en kilovatios-hora (kWh)."""
    if potencia_w <= 0:
        raise ValueError("La potencia no puede ser negativa")
    if potencia_w < 10.0:
        return 0.0
    return (potencia_w * tiempo_horas) / 1000.0
