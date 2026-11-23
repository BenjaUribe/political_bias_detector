"""
TEMPLATE: Actor 6 — La "Memoria de Contexto" (Base de Conocimiento Político Chileno)
Ubicación: backend/app/services/context_memory.py

Propósito:
    Gestionar el archivador de referencia sobre la realidad política chilena
    (`backend/data/chile_political_context.json`): siglas, cargos actuales, coaliciones,
    reformas en discusión y marcos conceptuales.
    Provee contexto relevante tanto al Anonimizador (Fase 1) como al Analista Crítico
    (Fase 2) para evitar malinterpretaciones de términos propios del país.
"""


class ChileanContextMemoryService:
    """
    TODO (Fase 1 / Fase 2):
    Cargar `backend/data/chile_political_context.json` en memoria y ofrecer búsquedas
    de entidades, siglas y reformas mencionadas en una noticia.
    """

    def load_context_database(self):
        """
        TODO (Fase 1):
        Leer y validar el archivo JSON de contexto político chileno.
        """
        raise NotImplementedError("Pendiente de implementar en Fase 1.")

    def retrieve_relevant_context(self, article_text: str) -> list:
        """
        TODO (Fase 2):
        Detectar qué siglas, partidos, coaliciones o reformas chilenas aparecen en
        `article_text` y devolver sus fichas de contexto para enriquecer el prompt
        del Analista Crítico.
        """
        raise NotImplementedError("Pendiente de implementar en Fase 2.")
