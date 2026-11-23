"""
TEMPLATE: Actor 1 — El "Recolector de Entrada" (Ingesta Web, Texto y OCR Multimodal)
Ubicación: backend/app/services/collector.py

Propósito:
    Recibir lo que el usuario entrega (enlace web de medio chileno, texto pegado o
    captura de pantalla móvil) y extraer únicamente el contenido periodístico útil:
    titular, bajada y cuerpo limpio, descartando publicidad, menús de navegación,
    barras de estado del teléfono y comentarios de lectores.

Tecnologías (`stack_tecnologico.md`):
    - `trafilatura` para extracción desde URLs (Fase 1).
    - `google-genai` (Gemini Flash Multimodal) para OCR inteligente desde capturas (Fase 2).
"""


class InputCollectorService:
    """
    TODO (Fase 1):
    Implementar extracción limpia desde URL y normalización de texto plano.
    TODO (Fase 2):
    Implementar sub-rol visual (`extract_from_screenshot`) para capturas de pantalla.
    """

    def extract_from_url(self, url: str):
        """
        TODO (Fase 1):
        Descargar artículo con `trafilatura`, separar titular, bajada y cuerpo,
        y validar que no sea una columna de opinión.
        """
        raise NotImplementedError("Pendiente de implementar en Fase 1.")

    def extract_from_raw_text(self, text: str, title: str = ""):
        """
        TODO (Fase 1):
        Limpiar saltos de línea, artefactos de copiado y normalizar estructura.
        """
        raise NotImplementedError("Pendiente de implementar en Fase 1.")

    def extract_from_screenshot(self, image_bytes: bytes, mime_type: str = "image/png"):
        """
        TODO (Fase 2 - Lector de Imágenes / OCR Inteligente):
        Enviar captura a Gemini Flash multimodal con prompt estricto para extraer
        solo titular, bajada y cuerpo periodístico ignorando menús y publicidad.
        """
        raise NotImplementedError("Pendiente de implementar en Fase 2.")
