"""
TEMPLATE: Configuración Central y Variables de Entorno (.env)
Ubicación: backend/app/core/config.py

Propósito:
    Cargar y validar con `pydantic-settings` todas las configuraciones del sistema:
    credenciales de `google-genai`, identificador del modelo BETO entrenado,
    rutas a `backend/data/chile_political_context.json` y conexión a base de datos/caché.
"""


class Settings:
    """
    TODO (Fase 1):
    Heredar de `BaseSettings` (pydantic_settings) y declarar:
        - APP_ENV: str
        - GEMINI_API_KEY: str
        - GEMINI_ANALYST_MODEL: str
        - BETO_MODEL_ID: str
        - SPACY_MODEL_NAME: str
        - CHILE_CONTEXT_JSON_PATH: Path
        - DATABASE_URL: str
    """
    pass
