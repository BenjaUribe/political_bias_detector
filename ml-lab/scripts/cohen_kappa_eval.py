"""
TEMPLATE: Evaluador de Acuerdo Inter-Anotador - Kappa de Cohen (Fase 0)
Ubicación: ml-lab/scripts/cohen_kappa_eval.py

Propósito:
    Cargar las planillas de etiquetado independiente de ambos desarrolladores,
    calcular el índice Kappa de Cohen (meta DoD Fase 0: Kappa >= 0.75),
    identificar las noticias con discrepancias para revisión conjunta y
    generar los archivos consolidados `train_dataset_v1.csv` y `gold_standard_test.csv`.
"""

from pathlib import Path
from typing import Tuple, List, Dict, Any


TARGET_KAPPA_THRESHOLD: float = 0.75


def load_annotator_files(annotator_a_path: Path, annotator_b_path: Path) -> Tuple[Any, Any]:
    """
    TODO (Fase 0):
    Cargar y alinear por `article_id` las etiquetas (`LEFT`, `CENTER`, `RIGHT`)
    asignadas por separado por cada integrante.
    """
    raise NotImplementedError("Pendiente de implementar en Fase 0.")


def compute_cohen_kappa(labels_a: List[str], labels_b: List[str]) -> Dict[str, Any]:
    """
    TODO (Fase 0):
    Calcular `cohen_kappa_score` (scikit-learn), matriz de desacuerdo entre anotadores
    y verificar si cumple el criterio de salida (Kappa >= 0.75).
    """
    raise NotImplementedError("Pendiente de implementar en Fase 0.")


def extract_disagreements(df_merged: Any) -> Any:
    """
    TODO (Fase 0):
    Filtrar y exportar las noticias donde Anotador A != Anotador B para sesión de consenso.
    """
    raise NotImplementedError("Pendiente de implementar en Fase 0.")


def split_train_and_gold_standard(
    consensus_df: Any,
    gold_standard_size: int = 30,
) -> Tuple[Any, Any]:
    """
    TODO (Fase 0):
    Realizar partición estratificada por clase y medio de origen para reservar
    las 30 noticias intocables de `gold_standard_test.csv` sin fuga de datos (data leakage).
    """
    raise NotImplementedError("Pendiente de implementar en Fase 0.")


if __name__ == "__main__":
    # Punto de entrada CLI para auditar el acuerdo inter-anotador en Fase 0
    pass
