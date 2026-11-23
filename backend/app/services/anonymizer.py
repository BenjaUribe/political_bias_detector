"""
TEMPLATE: Actor 2 — El "Anonimizador" (Filtro de Neutralidad)
Ubicación: backend/app/services/anonymizer.py

Propósito:
    Recorrer el texto limpio antes de que el Juez Entrenado (BETO) lo evalúe y
    ocultar pistas nominales obvias: reemplazar nombres propios de políticos,
    partidos, coaliciones y el nombre del diario por etiquetas genéricas neutras
    (ej. `[POLITICO_1]`, `[PARTIDO_A]`, `[COALICION_B]`, `[MEDIO]`).

    Garantiza que la clasificación se base en *cómo está escrita* la noticia y no
    en atajos por asociación nominal.

Tecnologías (`stack_tecnologico.md`):
    - `spaCy` (`es_core_news_lg`) para reconocimiento de entidades (`PER`, `ORG`).
    - `re` (Regex) + diccionario local (`backend/data/chile_political_context.json`).
"""


class AnonymizerService:
    """
    TODO (Fase 1):
    Cargar modelo `es_core_news_lg` de spaCy y el diccionario de entidades políticas chilenas.
    Mantener un mapa reversible de entidades (`entity_map`) por petición para que el
    reporte final sea legible sin haber contaminado al clasificador.
    """

    def anonymize_article(self, title: str, lead: str, body: str):
        """
        TODO (Fase 1):
        1. Detectar menciones de medios de comunicación y reemplazarlas por `[MEDIO]`.
        2. Detectar partidos y coaliciones chilenas y asignarlos a `[PARTIDO_A]`, `[PARTIDO_B]`, etc.
        3. Ejecutar NER con `spaCy` + lista local para reemplazar actores por `[POLITICO_1]`, `[POLITICO_2]`, etc.
        4. Retornar texto anonimizado y diccionario de mapeo (`entity_map`).
        """
        raise NotImplementedError("Pendiente de implementar en Fase 1.")
