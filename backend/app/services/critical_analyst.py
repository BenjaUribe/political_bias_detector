"""
TEMPLATE: Actor 5 — El "Analista Crítico" (Explicador Generativo)
Ubicación: backend/app/services/critical_analyst.py

Propósito:
    Componente de razonamiento avanzado conectado vía API (`google-genai`).
    Recibe:
        1. El texto periodístico original.
        2. Los porcentajes calculados por el Juez Entrenado (BETO).
        3. Los conteos duros del Contador Objetivo (en Fase 2).
        4. El glosario relevante de la Memoria de Contexto Chileno (en Fase 2).
    Con todo ello, redacta un informe claro en formato JSON estricto (`Pydantic`)
    explicando *por qué* se llegó a ese resultado, extrayendo al menos **2 citas textuales
    literales** del artículo e identificando qué puntos de vista faltaron en la nota.

Tecnologías (`stack_tecnologico.md`):
    - SDK `google-genai` (Gemini Flash) con `response_schema=CriticalExplanationSchema`.
"""


class CriticalAnalystService:
    """
    TODO (Fase 1):
    Implementar generación explicativa con validación JSON estricta y verificación de citas.
    TODO (Fase 3):
    Implementar síntesis comparativa para el modo Comparador Lado a Lado (`compare_framings`).
    """

    def generate_explanation(
        self,
        original_article: dict,
        judge_probabilities: dict,
        structural_metrics: dict = None,
        local_context_snippets: list = None,
    ):
        """
        TODO (Fase 1 / Fase 2):
        1. Construir prompt de auditoría neutral exigiendo respaldo en citas textuales exactas.
        2. Invocar `client.models.generate_content` con `response_mime_type="application/json"`
           y `response_schema=CriticalExplanationSchema`.
        3. Verificar que las citas devueltas existan literalmente en el texto original (anti-alucinación).
        """
        raise NotImplementedError("Pendiente de implementar en Fase 1.")

    def compare_framings(self, analyzed_articles: list):
        """
        TODO (Fase 3 - Comparador Lado a Lado):
        Recibir 2 o más análisis individuales sobre un mismo hecho noticioso y generar
        la matriz de contraste: diferencias de énfasis en titulares, actores entrevistados
        por cada medio y datos omitidos entre coberturas.
        """
        raise NotImplementedError("Pendiente de implementar en Fase 3.")
