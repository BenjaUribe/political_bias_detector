"""
Divisor Estratificado del Pool Sanitizado para Fase 0 (Bloque 4 y Bloque 5).
Ubicación: ml-lab/scripts/split_dataset.py

Propósito:
    Particionar `sanitized_pool.csv` en conjuntos disjuntos y estratificados por `medio`
    siguiendo `PHASE0_TASKS.md`:
        1. Lote de Calibración (40 noticias: `calibration_round1_20.csv` y `calibration_round2_20.csv`).
           Estas 40 noticias NO entran al Gold Standard.
        2. Gold Standard (`gold_standard_test.csv`): 30 noticias intocables, diversas en medio y tema.
        3. Dataset de Entrenamiento (`train_dataset_v1.csv`): 200 noticias para etiquetado y fine-tuning.
        4. Reserva (`reserve_pool.csv`): noticias sobrantes para reemplazos o balanceo dirigido (Tarea 21).

Uso:
    python ml-lab/scripts/split_dataset.py --input ml-lab/datasets/sanitized_pool.csv
"""

import argparse
import csv
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Tuple


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASETS_DIR = PROJECT_ROOT / "ml-lab" / "datasets"
DEFAULT_INPUT_CSV = DATASETS_DIR / "sanitized_pool.csv"


def stratified_take(
    by_group: Dict[str, List[Dict[str, str]]],
    target_total: int,
) -> List[Dict[str, str]]:
    """
    Extrae `target_total` filas de forma proporcional/round-robin entre grupos (`medio`),
    removiéndolas in-place de `by_group` para garantizar conjuntos disjuntos.
    """
    available = sum(len(v) for v in by_group.values())
    if target_total > available:
        raise ValueError(
            f"No hay suficientes noticias disponibles ({available}) para extraer {target_total}."
        )

    taken: List[Dict[str, str]] = []
    groups = sorted(by_group.keys())

    while len(taken) < target_total:
        progressed = False
        for grp in groups:
            if len(taken) >= target_total:
                break
            if by_group[grp]:
                taken.append(by_group[grp].pop(0))
                progressed = True
        if not progressed:
            break

    return taken


def write_csv(path: Path, rows: List[Dict[str, str]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def split_pool(
    input_csv: Path,
    output_dir: Path,
    calibration_r1_size: int = 20,
    calibration_r2_size: int = 20,
    gold_size: int = 30,
    train_size: int = 200,
    seed: int = 42,
    make_blind_calibration: bool = True,
) -> Dict[str, Tuple[Path, int, Dict[str, int]]]:
    """Ejecuta la partición estratificada y verifica que no exista fuga entre particiones."""
    if not input_csv.exists():
        raise FileNotFoundError(f"No existe el archivo de entrada: {input_csv}")

    with input_csv.open("r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])

    rng = random.Random(seed)
    by_medio: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for row in rows:
        medio = (row.get("medio") or "desconocido").strip()
        by_medio[medio].append(row)

    # Mezclar dentro de cada medio de forma reproducible
    for medio in by_medio:
        rng.shuffle(by_medio[medio])

    # Orden de extracción:
    # 1) Gold Standard (30) primero para asegurar máxima diversidad por medio y tema
    # 2) Calibración Ronda 1 (20) y Ronda 2 (20)
    # 3) Entrenamiento (200)
    # 4) Reserva (resto)
    gold_rows = stratified_take(by_medio, gold_size)
    cal_r1_rows = stratified_take(by_medio, calibration_r1_size)
    cal_r2_rows = stratified_take(by_medio, calibration_r2_size)
    train_rows = stratified_take(by_medio, train_size)

    reserve_rows: List[Dict[str, str]] = []
    for medio in sorted(by_medio.keys()):
        reserve_rows.extend(by_medio[medio])

    # Verificación estricta de cero solapamiento (anti data-leakage)
    all_sets = {
        "gold_standard": {r["id"] for r in gold_rows},
        "cal_r1": {r["id"] for r in cal_r1_rows},
        "cal_r2": {r["id"] for r in cal_r2_rows},
        "train": {r["id"] for r in train_rows},
        "reserve": {r["id"] for r in reserve_rows},
    }
    total_ids = sum(len(s) for s in all_sets.values())
    union_ids = set().union(*all_sets.values())
    assert len(union_ids) == total_ids, "Error crítico: hay IDs duplicados entre particiones."

    partitions: List[Tuple[str, Path, List[Dict[str, str]]]] = [
        ("gold_standard_test.csv", output_dir / "gold_standard_test.csv", gold_rows),
        ("calibration_round1_20.csv", output_dir / "calibration_round1_20.csv", cal_r1_rows),
        ("calibration_round2_20.csv", output_dir / "calibration_round2_20.csv", cal_r2_rows),
        ("train_dataset_v1.csv", output_dir / "train_dataset_v1.csv", train_rows),
        ("reserve_pool.csv", output_dir / "reserve_pool.csv", reserve_rows),
    ]

    summary: Dict[str, Tuple[Path, int, Dict[str, int]]] = {}
    for name, path, data in partitions:
        write_csv(path, data, fieldnames)
        dist = dict(sorted(Counter(r["medio"] for r in data).items()))
        summary[name] = (path, len(data), dist)

    # Hojas ciegas opcionales para el Piloto de Calibración (sin `medio` ni `url`)
    if make_blind_calibration:
        blind_fields = [
            "id",
            "text_anonymized",
            "score_A",
            "score_B",
            "score_C",
            "etiqueta",
            "confianza",
            "notas",
        ]
        for label, batch in (("round1", cal_r1_rows), ("round2", cal_r2_rows)):
            blind_rows = [
                {
                    "id": r["id"],
                    "text_anonymized": r.get("text_anonymized", ""),
                    "score_A": "",
                    "score_B": "",
                    "score_C": "",
                    "etiqueta": "",
                    "confianza": "",
                    "notas": "",
                }
                for r in batch
            ]
            for annotator in ("annotator_a", "annotator_b"):
                blind_path = output_dir / f"calibration_{label}_{annotator}_blind.csv"
                write_csv(blind_path, blind_rows, blind_fields)

    print("=== PARTICIÓN DE DATASET COMPLETADA (SIN SOLAPAMIENTO) ===")
    for name, (path, count, dist) in summary.items():
        print(f"- {name:26s}: {count:3d} filas | Por medio: {dist}")
    if make_blind_calibration:
        print(
            f"- Hojas ciegas de piloto    : calibration_round{{1,2}}_annotator_{{a,b}}_blind.csv en {output_dir}"
        )

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Separa sanitized_pool.csv en Calibración (20+20), Gold Standard (30), Train (200) y Reserva."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_CSV, help="CSV sanitizado de entrada.")
    parser.add_argument("--output-dir", type=Path, default=DATASETS_DIR, help="Directorio de salida.")
    parser.add_argument("--cal-r1", type=int, default=20, help="Tamaño calibración ronda 1 (default: 20).")
    parser.add_argument("--cal-r2", type=int, default=20, help="Tamaño calibración ronda 2 (default: 20).")
    parser.add_argument("--gold", type=int, default=30, help="Tamaño Gold Standard (default: 30).")
    parser.add_argument("--train", type=int, default=200, help="Tamaño Train V1 (default: 200).")
    parser.add_argument("--seed", type=int, default=42, help="Semilla aleatoria reproducible (default: 42).")
    parser.add_argument(
        "--no-blind-sheets",
        action="store_true",
        help="No generar las hojas ciegas para anotador A y B de calibración.",
    )
    args = parser.parse_args()

    split_pool(
        input_csv=args.input,
        output_dir=args.output_dir,
        calibration_r1_size=args.cal_r1,
        calibration_r2_size=args.cal_r2,
        gold_size=args.gold,
        train_size=args.train,
        seed=args.seed,
        make_blind_calibration=not args.no_blind_sheets,
    )


if __name__ == "__main__":
    main()
