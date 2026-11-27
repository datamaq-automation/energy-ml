"""src/application/cargas/dtos/mcp.py — DTOs para protocolo Model Context Protocol (MCP) JSON-RPC 2.0."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ParametroHerramienta(BaseModel):
    """Parámetro de una herramienta MCP."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    nombre: str = Field(description="Nombre del parámetro")
    tipo: str = Field(description="Tipo: 'string', 'number', 'boolean', etc.")
    descripcion: str = Field(description="Descripción del parámetro")
    requerido: bool = Field(default=True, description="¿Es requerido?")


class HerramientaMCP(BaseModel):
    """Una herramienta disponible en el servidor MCP."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    nombre: str = Field(description="ID único de la herramienta")
    descripcion: str = Field(description="Descripción legible de qué hace")
    parametros: list[ParametroHerramienta] = Field(description="Parámetros aceptados")


class SolicitudMCP(BaseModel):
    """Solicitud JSON-RPC 2.0 al servidor MCP."""

    model_config = ConfigDict(extra="forbid")

    jsonrpc: str = Field(default="2.0", description="Versión JSON-RPC")
    method: str = Field(description="Nombre del método: 'tools/list' o 'tools/call'")
    params: dict[str, Any] = Field(default_factory=dict, description="Parámetros del método")
    id: int | str | None = Field(
        default=None, description="ID de la solicitud para correlacionar respuesta"
    )


class RespuestaMCPExito(BaseModel):
    """Respuesta exitosa JSON-RPC 2.0."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    jsonrpc: str = Field(default="2.0", description="Versión JSON-RPC")
    result: Any = Field(description="Resultado del método")
    id: int | str | None = Field(default=None, description="ID de la solicitud correlacionada")


class RespuestaMCPError(BaseModel):
    """Respuesta de error JSON-RPC 2.0."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    jsonrpc: str = Field(default="2.0", description="Versión JSON-RPC")
    error: dict[str, Any] = Field(description="Objeto error con code y message")
    id: int | str | None = Field(default=None, description="ID de la solicitud correlacionada")
