import csv
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
CSV_PATH = BASE_DIR / "datasets" / "extracted_pool.csv"

MOJIBAKE_RE = re.compile(r"Ã[\x80-\xbf¡-¿]|Â[\x80-\xbf¡-¿]|â€[™œ“”–—¦•]")
TEXT_COLS = ["titular", "bajada", "cuerpo"]


def fix_mojibake(text: str) -> str:
    if not text or not MOJIBAKE_RE.search(text):
        return text

    for enc in ("cp1252", "latin-1"):
        try:
            fixed = text.encode(enc).decode("utf-8")
            if fixed != text:
                return fixed
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue

    # Respaldo por si hay caracteres mixtos dentro del mismo texto
    def _fix_chunk(match: re.Match) -> str:
        chunk = match.group(0)
        for enc in ("cp1252", "latin-1"):
            try:
                return chunk.encode(enc).decode("utf-8")
            except (UnicodeEncodeError, UnicodeDecodeError):
                continue
        return chunk

    return re.sub(r"[^\x00-\x7f]+", _fix_chunk, text)


def run() -> None:
    if not CSV_PATH.exists():
        print(f"No se encontró {CSV_PATH}")
        return

    with open(CSV_PATH, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    fixed_rows = 0
    examples = []

    for row in rows:
        row_changed = False
        for col in TEXT_COLS:
            original = row.get(col, "")
            repaired = fix_mojibake(original)
            if repaired != original:
                if col == "titular" and len(examples) < 5:
                    examples.append((original, repaired))
                row[col] = repaired
                row_changed = True
        if row_changed:
            fixed_rows += 1

    with open(CSV_PATH, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Limpieza terminada en {CSV_PATH}")
    print(f"Filas reparadas: {fixed_rows} / {len(rows)}")

    if examples:
        print("\nEjemplos de titulares reparados:")
        for before, after in examples:
            print(f"  ANTES:   {before[:80]}")
            print(f"  DESPUÉS: {after[:80]}\n")


if __name__ == "__main__":
    run()