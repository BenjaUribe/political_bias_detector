"""
TEMPLATE: Actor 3 — El "Contador Objetivo" (Analizador Estructural Determinista)
Ubicación: backend/app/services/structural_analyzer.py

Propósito:
    Actuar como un auditor matemático sin "opinión" (Fase 2).
    Contar elementos duros, deterministas y verificables dentro del texto:
    - Cuántas veces aparece cada actor político/institucional.
    - Quién recibe citas textuales directas entre comillas ("...") frente a quién
      solo es parafraseado o mencionado de pasada.
    - Qué proporción del texto utiliza adjetivos calificativos/valorativos.
    - Qué cifras o afirmaciones se lanzan sin citar una fuente o documento oficial
      (ej. "expertos aseguran...", "se estima que...").

Tecnologías (`stack_tecnologico.md`):
    - `spaCy` (`es_core_news_lg` - análisis morfosintáctico POS y dependencias) + `re` (Regex).
"""


class StructuralAnalyzerService:
    """
    TODO (Fase 2):
    Implementar métodos deterministas de conteo y devolver `StructuralMetricsSchema`.
    """

    def count_direct_quotes_vs_paraphrases(self, text: str):
        """
        TODO (Fase 2):
        Extraer segmentos entre comillas (`"..."`, `«...»`, `“...”`), vincularlos al sujeto
        o verbo de habla mediante el árbol de dependencias de `spaCy` y contrastar con
        menciones indirectas.
        """
        raise NotImplementedError("Pendiente de implementar en Fase 2.")

    def compute_adjective_load(self, text: str):
        """
        TODO (Fase 2):
        Calcular densidad de adjetivos calificativos respecto al total de tokens léxicos.
        """
        raise NotImplementedError("Pendiente de implementar en Fase 2.")

    def detect_unattributed_claims_and_figures(self, text: str):
        """
        TODO (Fase 2):
        Detectar oraciones con cifras (`%`, montos, estadísticas) o generalizaciones
        ("analistas señalan", "críticos apuntan") que carezcan de entidad fuente explícita.
        """
        raise NotImplementedError("Pendiente de implementar en Fase 2.")

    def analyze_structure(self, text: str):
        """
        TODO (Fase 2):
        Ejecutar todas las auditorías deterministas y consolidar el JSON para el Analista Crítico.
        """
        raise NotImplementedError("Pendiente de implementar en Fase 2.")
