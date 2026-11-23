"""Planning des exposés M354 : application de démonstration DevOps."""

import os
import time

from flask import Flask, Response, g, jsonify, render_template, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, Info, generate_latest

from app.data import EXPOSES

APP_VERSION = os.environ.get("APP_VERSION", "dev")
GIT_COMMIT = os.environ.get("GIT_COMMIT", "local")
APP_ENV = os.environ.get("APP_ENV", "local")

REQUESTS = Counter(
    "app_http_requests_total",
    "Nombre de requêtes HTTP",
    ["method", "endpoint", "status"],
)
LATENCY = Histogram(
    "app_http_request_duration_seconds",
    "Durée des requêtes HTTP",
    ["endpoint"],
)
INFO = Info("app_build", "Version déployée")
INFO.info({"version": APP_VERSION, "commit": GIT_COMMIT, "env": APP_ENV})


def create_app() -> Flask:
    app = Flask(__name__)

    @app.before_request
    def _start_timer():
        g.start = time.perf_counter()

    @app.after_request
    def _record_metrics(response):
        endpoint = request.url_rule.rule if request.url_rule else "inconnu"
        if endpoint != "/metrics":
            LATENCY.labels(endpoint).observe(time.perf_counter() - g.start)
            REQUESTS.labels(request.method, endpoint, response.status_code).inc()
        return response

    @app.get("/")
    def index():
        return render_template("index.html", exposes=EXPOSES, version=APP_VERSION, env=APP_ENV)

    @app.get("/api/exposes")
    def api_exposes():
        return jsonify(EXPOSES)

    @app.get("/api/exposes/<int:numero>")
    def api_expose(numero: int):
        for expose in EXPOSES:
            if expose["numero"] == numero:
                return jsonify(expose)
        return jsonify({"erreur": f"exposé {numero} introuvable"}), 404

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.get("/version")
    def version():
        return jsonify({"version": APP_VERSION, "commit": GIT_COMMIT, "env": APP_ENV})

    @app.get("/metrics")
    def metrics():
        return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

    return app


app = create_app()
