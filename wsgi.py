"""Flask WSGI compatibility entrypoint for PythonAnywhere.

This keeps the existing business logic in src/ and exposes a small Flask app
that covers the endpoints used by the web UI. The original FastAPI app stays
untouched for local development.
"""

from datetime import datetime
from typing import cast

from flask import Flask, jsonify, request, send_file

from src.application.cargas.dtos.identificar_cargas import IdentificarCargasRequest
from src.infrastructure.fastapi.dependencies import get_identificar_cargas, get_mediciones
from src.infrastructure.settings.config import get_settings
from src.infrastructure.settings.logger import logger
from src.infrastructure.ssh.medicion_repository import SshMedicionRepository

app = Flask(__name__, static_folder="web", static_url_path="/static")
app.config["JSON_SORT_KEYS"] = False


@app.errorhandler(LookupError)
def handle_lookup_error(error: LookupError):
    logger.warning("Respondiendo 404 desde Flask: %s", error)
    return jsonify({"detail": str(error)}), 404


@app.route("/")
def index():
    return send_file("web/energia.html")


@app.route("/guia")
def guia():
    return send_file("web/guia.html")


@app.route("/guia/cuaderno-alumno.md")
def guia_markdown():
    return send_file("docs/cuaderno-alumno.md", mimetype="text/markdown; charset=utf-8")


@app.route("/health")
def health_check():
    settings = get_settings()
    return jsonify({"status": "ok", "environment": settings.ENVIRONMENT})


@app.route("/api/v1/mediciones/fuente")
def obtener_fuente_mediciones():
    settings = get_settings()
    repo = get_mediciones()
    medidores = repo.medidores()
    ultima_descarga: dict[str, object] | None = None

    if isinstance(repo, SshMedicionRepository):
        info = repo.ultima_descarga_info()
        instante = cast(str | None, info.get("instante"))
        duracion_segundos = cast(float | int | None, info.get("duracion_segundos"))
        filas_por_medidor = cast(dict[str, int], info.get("filas_por_medidor", {}))

        ultima_descarga = {
            "instante": instante,
            "duracion_segundos": float(duracion_segundos or 0.0),
            "filas_por_medidor": filas_por_medidor,
        }
        logger.info(
            "📊 Fuente SSH: %d medidores, descarga en %.1f seg",
            len(medidores),
            float(duracion_segundos or 0.0),
        )
    else:
        logger.info("📂 Fuente local: %d medidores disponibles", len(medidores))

    payload: dict[str, object] = {
        "fuente": settings.MEDICIONES_SOURCE,
        "medidores": medidores,
        "ultima_descarga": ultima_descarga,
    }
    return jsonify(payload)


@app.route("/api/v1/identify-loads")
def identificar_cargas():
    medidor = request.args.get("medidor", "planta_2_a")
    desde = request.args.get("desde", "2026-09-12")
    hasta = request.args.get("hasta", "2026-10-03")

    try:
        desde_dt = datetime.fromisoformat(desde)
        hasta_dt = datetime.fromisoformat(hasta)
    except ValueError:
        return jsonify({"detail": "Parámetros desde/hasta inválidos. Usa YYYY-MM-DD."}), 400

    try:
        payload = IdentificarCargasRequest(medidor=medidor, desde=desde_dt, hasta=hasta_dt)
    except ValueError as exc:
        return jsonify({"detail": str(exc)}), 422

    use_case = get_identificar_cargas()
    response = use_case.execute(payload)
    return app.response_class(response.model_dump_json(), mimetype="application/json")


@app.route("/api/v1/docs")
def docs_redirect():
    return jsonify({
        "message": "API docs no están disponibles en esta build Flask; usa los endpoints REST documentados en el repo.",
        "endpoints": [
            "/api/v1/identify-loads",
            "/api/v1/mediciones/fuente",
            "/health",
        ],
    })


@app.route("/api/v1/openapi.json")
def openapi_json():
    return jsonify({"openapi": "3.0.0", "info": {"title": "energy-ml Flask compatibility", "version": "1.0.0"}})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
