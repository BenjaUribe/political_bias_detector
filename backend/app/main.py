"""
TEMPLATE: Punto de Entrada de la API REST (FastAPI)
Ubicación: backend/app/main.py

Propósito:
    Inicializar la aplicación FastAPI, configurar CORS para permitir peticiones
    desde el frontend en React, gestionar el ciclo de vida de los modelos en memoria
    (spaCy + clasificador BETO) y montar las rutas de `/api`.
"""

# TODO (Fase 1): Configurar instancia FastAPI, middleware CORS y lifespan de carga de modelos.


def create_app():
    """
    TODO (Fase 1):
    1. Instanciar `FastAPI(title="Political Bias Detector API - Chile")`.
    2. Registrar `CORSMiddleware` para el frontend local/producción.
    3. Incluir el router de `app.api.routes`.
    4. Retornar la aplicación configurada.
    """
    raise NotImplementedError("Pendiente de implementar en Fase 1.")
