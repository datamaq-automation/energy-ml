"""src/application/sibo/mappers/sibo_mapper.py — Entidades y eventos del dominio → DTOs de aplicación."""

from __future__ import annotations

from datetime import datetime

from src.application.sibo.dtos.eliminar_registro import EliminarRegistroResponse
from src.application.sibo.dtos.estimar_gases import EstimarGasesResponse, PuntoGasesDTO
from src.application.sibo.dtos.listar_alimentos import AlimentoDTO
from src.application.sibo.dtos.recomendar_alimentos import RecomendacionDTO
from src.application.sibo.dtos.registrar_comida import RegistrarComidaResponse
from src.domain.sibo.entities import Alimento, PuntoGases, Recomendacion, RegistroComida
from src.domain.sibo.events import ComidaRegistrada, RegistroEliminado


class SiboMapper:
    """Traduce el vocabulario del dominio a los contratos de la aplicación."""

    @staticmethod
    def alimento_a_dto(alimento: Alimento) -> AlimentoDTO:
        """Copia los campos nutricionales de la entidad al DTO."""
        return AlimentoDTO(
            id=alimento.id,
            nombre=alimento.nombre,
            categoria=alimento.categoria,
            porcion_base_g=alimento.porcion_base_g,
            kcal=alimento.kcal,
            proteinas_g=alimento.proteinas_g,
            carbohidratos_g=alimento.carbohidratos_g,
            grasas_g=alimento.grasas_g,
            fibra_g=alimento.fibra_g,
            fodmap=alimento.fodmap,
            score_inflamatorio=alimento.score_inflamatorio,
            score_desinflamatorio=alimento.score_desinflamatorio,
            notas=alimento.notas,
        )

    @staticmethod
    def registro_a_response(
        registro: RegistroComida,
        alimento: Alimento,
        evento: ComidaRegistrada | None = None,
    ) -> RegistrarComidaResponse:
        """Aplana el registro y su alimento; el evento aporta el id al registrar."""
        id_registro = evento.registro_id if evento else (registro.id or 0)
        return RegistrarComidaResponse(
            id=id_registro,
            fecha_hora=registro.fecha_hora,
            alimento_id=registro.alimento_id,
            alimento_nombre=alimento.nombre,
            categoria=alimento.categoria,
            fodmap=alimento.fodmap,
            porcion_g=registro.porcion_g,
            sintomas=registro.sintomas,
            notas=registro.notas,
            score_inflamatorio=alimento.score_inflamatorio,
            score_desinflamatorio=alimento.score_desinflamatorio,
        )

    @staticmethod
    def punto_a_dto(punto: PuntoGases) -> PuntoGasesDTO:
        """Convierte un punto de la curva en su DTO."""
        return PuntoGasesDTO(
            instante=punto.instante,
            nivel_estimado=punto.nivel_estimado,
            nivel_bajo=punto.nivel_bajo,
            nivel_alto=punto.nivel_alto,
        )

    @staticmethod
    def serie_a_response(
        rango: str,
        desde: datetime,
        hasta: datetime,
        promedio: float,
        pico: float,
        puntos: list[PuntoGases],
    ) -> EstimarGasesResponse:
        """Compone la respuesta de la curva con el resumen y todos sus puntos."""
        return EstimarGasesResponse(
            rango=rango,
            desde=desde,
            hasta=hasta,
            promedio=promedio,
            pico=pico,
            puntos=[SiboMapper.punto_a_dto(punto) for punto in puntos],
        )

    @staticmethod
    def recomendacion_a_dto(recomendacion: Recomendacion) -> RecomendacionDTO:
        """Incluye el alimento recomendado junto a su puntaje y motivo."""
        return RecomendacionDTO(
            alimento=SiboMapper.alimento_a_dto(recomendacion.alimento),
            puntaje=recomendacion.puntaje,
            motivo=recomendacion.motivo,
        )

    @staticmethod
    def registro_eliminado_a_response(evento: RegistroEliminado) -> EliminarRegistroResponse:
        """Deriva la confirmación de la baja del evento de dominio."""
        return EliminarRegistroResponse(registro_id=evento.registro_id)
