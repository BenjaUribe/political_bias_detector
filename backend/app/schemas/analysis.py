"""
TEMPLATE: Contratos JSON con Pydantic (Entrada, Salida y Reporte Estructurado del LLM)
Ubicación: backend/app/schemas/analysis.py

Propósito:
    Definir los esquemas estrictos de validación para:
    1. Peticiones del usuario (`AnalyzeRequest`, `CompareRequest`).
    2. Salida probabilística del Juez Entrenado BETO (`BiasProbabilitiesSchema`).
    3. Métricas duras del Contador Objetivo (`StructuralMetricsSchema` - Fase 2).
    4. Salida JSON estructurada exigida al Analista Crítico vía `google-genai` (`CriticalExplanationSchema`).
    5. Respuesta consolidada de lectura crítica y tabla comparativa lado a lado (Fase 3).
"""


class AnalyzeRequestSchema:
    """
    TODO (Fase 1):
    Campos de entrada:
        - url: Optional[HttpUrl]
        - raw_text: Optional[str]
        - title_override: Optional[str]
    """
    pass


class BiasProbabilitiesSchema:
    """
    TODO (Fase 1):
    Distribución probabilística emitida por el Juez Entrenado (BETO):
        - left_percentage: float    (Izquierda %)
        - center_percentage: float  (Centro %)
        - right_percentage: float   (Derecha %)
        - dominant_framing: str
    """
    pass


class StructuralMetricsSchema:
    """
    TODO (Fase 2 - Contador Objetivo):
    Datos duros y auditables del texto:
        - direct_quotes_by_actor: Dict[str, int]   (citas entre comillas por actor/sector)
        - paraphrases_by_actor: Dict[str, int]     (menciones sin cita directa)
        - qualifying_adjectives_ratio: float       (proporción de adjetivos calificativos)
        - unattributed_claims: List[str]           (cifras o afirmaciones sin fuente oficial)
    """
    pass


class QuoteEvidenceSchema:
    """
    TODO (Fase 1):
    Cita textual literal extraída por el Analista Crítico:
        - exact_quote: str          (cita literal del artículo)
        - framing_indicator: str    (qué patrón de encuadre evidencia)
        - explanation: str          (justificación basada en el texto)
    """
    pass


class CriticalExplanationSchema:
    """
    TODO (Fase 1 / Fase 2 - Analista Crítico con `google-genai` + Pydantic Structured Outputs):
        - summary_verdict: str
        - supporting_quotes: List[QuoteEvidenceSchema]  (mínimo 2 citas textuales obligatorias)
        - missing_perspectives: List[str]               (qué puntos de vista o fuentes faltaron)
        - local_context_notes: List[str]                (glosario chileno aplicado en Fase 2)
    """
    pass


class AnalysisResponseSchema:
    """
    TODO (Fase 1 / Fase 2):
    Respuesta completa empaquetada por el Orquestador para la interfaz web:
        - article_metadata: Dict[str, Any] (titular, bajada, medio detectado)
        - anonymized_preview: str          (vista del texto con tokens [POLITICO_A], [MEDIO])
        - probabilities: BiasProbabilitiesSchema
        - structural_metrics: Optional[StructuralMetricsSchema]
        - critical_analysis: CriticalExplanationSchema
    """
    pass


class SideBySideComparisonResponseSchema:
    """
    TODO (Fase 3 - Comparador de Encuadres):
    Matriz de contraste para 2 o más noticias sobre un mismo evento:
        - individual_reports: List[AnalysisResponseSchema]
        - headline_emphasis_contrast: Dict[str, str]
        - interviewed_actors_matrix: Dict[str, List[str]]
        - cross_omissions: List[str] (qué datos incluye un medio y omite el otro)
    """
    pass
