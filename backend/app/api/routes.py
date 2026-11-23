"""
TEMPLATE: Definición de Endpoints de la API REST
Ubicación: backend/app/api/routes.py

Rutas planeadas según `estructura.md` y `roadmap.md`:
    1. GET  `/api/health`        -> Verificación de estado de la API y modelos cargados (Fase 1).
    2. POST `/api/analyze`       -> Análisis de una noticia por URL o texto plano (Fase 1).
    3. POST `/api/analyze/image` -> Análisis de captura de pantalla móvil vía OCR multimodal (Fase 2).
    4. POST `/api/compare`       -> Comparador lado a lado de 2 o más coberturas sobre un mismo hecho (Fase 3).
"""


def health_check():
    """
    TODO (Fase 1):
    Retornar estado del servicio, versión del modelo Juez (BETO V1/V2) y estado de la memoria de contexto.
    """
    raise NotImplementedError("Pendiente de implementar en Fase 1.")


def analyze_single_article():
    """
    TODO (Fase 1):
    Recibir `AnalyzeRequest` (URL o texto pegado), delegar al `OrchestratorService`
    y devolver `AnalysisResponse` con:
        - Porcentajes (`Izquierda % / Centro % / Derecha %`) del Juez Entrenado.
        - Métricas del Contador Objetivo (Fase 2).
        - Explicación con al menos 2 citas textuales del Analista Crítico.
    """
    raise NotImplementedError("Pendiente de implementar en Fase 1.")


def analyze_screenshot_image():
    """
    TODO (Fase 2):
    Recibir archivo de imagen (captura de pantalla móvil/redes sociales),
    extraer contenido periodístico mediante OCR multimodal (Gemini Flash) y
    ejecutar el flujo completo del Orquestador.
    """
    raise NotImplementedError("Pendiente de implementar en Fase 2.")


def compare_multiple_articles():
    """
    TODO (Fase 3):
    Recibir `CompareRequest` (2 o más URLs sobre el mismo evento noticioso),
    procesar en paralelo y retornar la tabla de contraste lado a lado
    (énfasis de titulares, actores entrevistados y datos omitidos entre medios).
    """
    raise NotImplementedError("Pendiente de implementar en Fase 3.")
