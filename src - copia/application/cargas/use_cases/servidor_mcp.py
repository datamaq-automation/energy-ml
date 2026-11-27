"""src/application/cargas/use_cases/servidor_mcp.py — Servidor JSON-RPC 2.0 con herramientas locales."""

from typing import Any

from src.application.cargas.dtos.mcp import (
    HerramientaMCP,
    ParametroHerramienta,
    RespuestaMCPError,
    RespuestaMCPExito,
    SolicitudMCP,
)
from src.domain.cargas.repositories import ClasificadorSaltos


class ServidorMCP:
    """Servidor JSON-RPC 2.0 que expone herramientas locales para interactuar con el modelo."""

    def __init__(self, clasificador: ClasificadorSaltos) -> None:
        self._clasificador = clasificador
        self._herramientas = self._inicializar_herramientas()

    def _inicializar_herramientas(self) -> dict[str, HerramientaMCP]:
        """Define las herramientas disponibles en el servidor."""
        return {
            "explain_tree": HerramientaMCP(
                nombre="explain_tree",
                descripcion="Obtiene la estructura del árbol de decisión en formato JSON",
                parametros=[],
            ),
            "extract_rules": HerramientaMCP(
                nombre="extract_rules",
                descripcion="Extrae reglas conjuntivas del árbol de decisión",
                parametros=[],
            ),
            "predict": HerramientaMCP(
                nombre="predict",
                descripcion="Realiza una predicción con el modelo sobre un salto de potencia",
                parametros=[
                    ParametroHerramienta(
                        nombre="delta_kw",
                        tipo="number",
                        descripcion="Salto de potencia ΔP en kW",
                        requerido=True,
                    ),
                    ParametroHerramienta(
                        nombre="delta_previo_kw",
                        tipo="number",
                        descripcion="Salto anterior en kW",
                        requerido=True,
                    ),
                    ParametroHerramienta(
                        nombre="delta_siguiente_kw",
                        tipo="number",
                        descripcion="Salto siguiente en kW",
                        requerido=True,
                    ),
                ],
            ),
        }

    def procesar_solicitud(self, solicitud: SolicitudMCP) -> RespuestaMCPExito | RespuestaMCPError:
        """Procesa una solicitud JSON-RPC 2.0 y retorna la respuesta."""
        try:
            if solicitud.method == "tools/list":
                return self._tools_list(solicitud.id)
            elif solicitud.method == "tools/call":
                return self._tools_call(solicitud.params, solicitud.id)
            else:
                return RespuestaMCPError(
                    error={"code": -32601, "message": f"Método no encontrado: {solicitud.method}"},
                    id=solicitud.id,
                )
        except Exception as e:
            return RespuestaMCPError(
                error={"code": -32603, "message": f"Error interno: {str(e)}"},
                id=solicitud.id,
            )

    def _tools_list(self, request_id: int | str | None) -> RespuestaMCPExito:
        """Retorna la lista de herramientas disponibles."""
        herramientas_dict = [
            {
                "nombre": h.nombre,
                "descripcion": h.descripcion,
                "parametros": [
                    {
                        "nombre": p.nombre,
                        "tipo": p.tipo,
                        "descripcion": p.descripcion,
                        "requerido": p.requerido,
                    }
                    for p in h.parametros
                ],
            }
            for h in self._herramientas.values()
        ]

        return RespuestaMCPExito(
            result={"herramientas": herramientas_dict, "cantidad": len(herramientas_dict)},
            id=request_id,
        )

    def _tools_call(
        self, params: dict[str, Any], request_id: int | str | None
    ) -> RespuestaMCPExito | RespuestaMCPError:
        """Ejecuta una herramienta específica."""
        nombre_herramienta = params.get("nombre")
        argumentos = params.get("argumentos", {})

        if nombre_herramienta == "explain_tree":
            resultado = self._clasificador.obtener_arbol_dict()
        elif nombre_herramienta == "extract_rules":
            resultado = self._clasificador.obtener_reglas_dict()
        elif nombre_herramienta == "predict":
            from datetime import datetime

            from src.domain.cargas.entities import Salto

            salto = Salto(
                instante=datetime.now(),
                delta_kw=argumentos.get("delta_kw", 0.0),
                delta_previo_kw=argumentos.get("delta_previo_kw", 0.0),
                delta_siguiente_kw=argumentos.get("delta_siguiente_kw", 0.0),
            )
            predicciones = self._clasificador.predecir([salto])
            resultado = {"prediccion": predicciones[0] if predicciones else None}
        else:
            return RespuestaMCPError(
                error={
                    "code": -32602,
                    "message": f"Herramienta no encontrada: {nombre_herramienta}",
                },
                id=request_id,
            )

        return RespuestaMCPExito(result=resultado, id=request_id)
