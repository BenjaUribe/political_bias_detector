"""
TEMPLATE: Script de Recolección y Limpieza para el Dataset Inicial (Fase 0)
Ubicación: ml-lab/scripts/dataset_builder.py

Propósito:
    Recibir una lista de URLs recolectadas manualmente desde 5 a 8 medios informativos
    chilenos (El Mercurio, La Tercera, BioBioChile, El Mostrador, CIPER, El Desconcierto, etc.),
    extraer titular, bajada y cuerpo limpio usando `trafilatura`, aplicar el filtro de
    anonimización y exportar las plantillas CSV para el Taller de Etiquetado.

Entregables que alimenta:
    - ml-lab/datasets/train_dataset_v1.csv (200 noticias)
    - ml-lab/datasets/gold_standard_test.csv (30 noticias intocables)
"""

from pathlib import Path
from typing import List, Dict, Any


# TODO (Fase 0): Definir lista oficial de 5 a 8 medios chilenos soportados
SUPPORTED_CHILEAN_MEDIA: List[str] = [
    "biobiochile.cl",
    "latercera.com",
    "emol.com",
    "elmostrador.cl",
    "ciperchile.cl",
    "eldesconcierto.cl",
]


def fetch_and_clean_article(url: str) -> Dict[str, Any]:
    """
    TODO (Fase 0):
    1. Descargar HTML de la URL y extraer contenido periodístico con `trafilatura`.
    2. Separar titular, bajada y cuerpo descartando publicidad, menús y bloques de opinión.
    3. Retornar diccionario estructurado libre de etiquetas HTML.
    """
    raise NotImplementedError("Pendiente de implementar en Fase 0.")


def anonymize_for_annotation(raw_article: Dict[str, Any]) -> Dict[str, Any]:
    """
    TODO (Fase 0 / Fase 1):
    Invocar la lógica del Anonimizador (spaCy + diccionario político chileno) para generar
    la columna `text_anonymized` antes de entrenar o etiquetar a ciegas.
    """
    raise NotImplementedError("Pendiente de implementar en Fase 0 / Fase 1.")


def export_annotation_batch(articles: List[Dict[str, Any]], output_csv_path: Path) -> None:
    """
    TODO (Fase 0):
    Guardar el lote de noticias limpias en formato CSV listo para el etiquetado paralelo
    de ambos integrantes.
    """
    raise NotImplementedError("Pendiente de implementar en Fase 0.")


if __name__ == "__main__":
    # Punto de entrada CLI para ejecutar la recolección del dataset de Fase 0
    pass
