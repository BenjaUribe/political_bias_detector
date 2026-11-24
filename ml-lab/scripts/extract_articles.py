import csv
import hashlib
import json
import re
import time
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse
import requests
import trafilatura

BASE_DIR = Path(__file__).resolve().parents[1]
INPUT_CSV = BASE_DIR / "datasets" / "candidate_urls.csv"
RAW_HTML_DIR = BASE_DIR / "datasets" / "raw_html"
OUTPUT_CSV = BASE_DIR / "datasets" / "extracted_pool.csv"

LIMIT_PER_MEDIA = None  # Pon un número (ej. 10) si quieres hacer una prueba corta primero
MIN_WORDS = 150         # Descarta notas demasiado cortas
REQUEST_DELAY = 0.6     # Pausa entre peticiones (segundos)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

CSV_FIELDNAMES = [
    "id",
    "medio",
    "url",
    "fecha",
    "titular",
    "bajada",
    "cuerpo",
    "seccion",
    "score_A",
    "score_B",
    "score_C",
    "etiqueta_a1",
    "confianza_a1",
    "etiqueta_a2",
    "confianza_a2",
    "etiqueta_final",
]


def clean_text(text: str | None) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def compute_hash(text: str) -> str:
    normalized = re.sub(r"\W+", "", text.lower())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def infer_section(url: str) -> str:
    parts = [p for p in urlparse(url).path.split("/") if p]
    if len(parts) >= 2 and parts[0] in {"noticias", "noticia"}:
        return parts[1]
    return parts[0] if parts else "desconocida"


def load_existing_progress(output_path: Path) -> tuple[set[str], set[str], dict[str, int]]:
    seen_urls: set[str] = set()
    seen_hashes: set[str] = set()
    counts_by_media: dict[str, int] = {}

    if not output_path.exists():
        return seen_urls, seen_hashes, counts_by_media

    with open(output_path, mode="r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            url = row.get("url", "").strip()
            cuerpo = row.get("cuerpo", "").strip()
            medio = row.get("medio", "").strip()
            if url:
                seen_urls.add(url)
            if cuerpo:
                seen_hashes.add(compute_hash(cuerpo))
            if medio:
                counts_by_media[medio] = counts_by_media.get(medio, 0) + 1

    return seen_urls, seen_hashes, counts_by_media


def extract_articles() -> None:
    if not INPUT_CSV.exists():
        print(f"No se encontró {INPUT_CSV}. Ejecuta primero discover_sitemaps.py.")
        return

    RAW_HTML_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    with open(INPUT_CSV, mode="r", encoding="utf-8") as f:
        candidates = list(csv.DictReader(f))

    seen_urls, seen_hashes, counts_by_media = load_existing_progress(OUTPUT_CSV)
    file_exists = OUTPUT_CSV.exists() and OUTPUT_CSV.stat().st_size > 0

    new_count = 0
    skipped_count = 0

    with open(OUTPUT_CSV, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
        if not file_exists:
            writer.writeheader()

        for idx, row in enumerate(candidates, start=1):
            medio = row["medio"].strip()
            url = row["url"].strip()

            if LIMIT_PER_MEDIA and counts_by_media.get(medio, 0) >= LIMIT_PER_MEDIA:
                continue
            if url in seen_urls:
                continue

            try:
                resp = requests.get(url, headers=HEADERS, timeout=15)
                if resp.status_code != 200:
                    print(f"[{idx}/{len(candidates)}] [SKIP HTTP {resp.status_code}] {url}")
                    skipped_count += 1
                    continue

                html = resp.text
                result_json = trafilatura.extract(
                    html,
                    url=url,
                    output_format="json",
                    include_comments=False,
                    include_tables=False,
                    favor_precision=True,
                )

                if not result_json:
                    print(f"[{idx}/{len(candidates)}] [SKIP SIN TEXTO] {url}")
                    skipped_count += 1
                    continue

                data = json.loads(result_json)
                titular = clean_text(data.get("title") or row.get("titular_rss"))
                bajada = clean_text(data.get("excerpt") or data.get("description"))
                cuerpo = clean_text(data.get("text"))
                fecha = (data.get("date") or row.get("fecha_rss") or "").strip()

                word_count = len(cuerpo.split())
                if word_count < MIN_WORDS:
                    print(f"[{idx}/{len(candidates)}] [SKIP CORTA: {word_count} palabras] {url}")
                    skipped_count += 1
                    continue

                text_hash = compute_hash(cuerpo)
                if text_hash in seen_hashes:
                    print(f"[{idx}/{len(candidates)}] [SKIP DUPLICADA] {url}")
                    skipped_count += 1
                    continue

                seen_urls.add(url)
                seen_hashes.add(text_hash)
                counts_by_media[medio] = counts_by_media.get(medio, 0) + 1

                article_id = f"{medio}_{counts_by_media[medio]:03d}"

                raw_path = RAW_HTML_DIR / f"{article_id}.html"
                raw_path.write_text(html, encoding="utf-8")

                writer.writerow({
                    "id": article_id,
                    "medio": medio,
                    "url": url,
                    "fecha": fecha,
                    "titular": titular,
                    "bajada": bajada,
                    "cuerpo": cuerpo,
                    "seccion": infer_section(url),
                    "score_A": "",
                    "score_B": "",
                    "score_C": "",
                    "etiqueta_a1": "",
                    "confianza_a1": "",
                    "etiqueta_a2": "",
                    "confianza_a2": "",
                    "etiqueta_final": "",
                })
                f.flush()
                new_count += 1

                print(f"[{idx}/{len(candidates)}] [OK] {article_id} ({word_count} palabras) - {titular[:55]}...")
                time.sleep(REQUEST_DELAY)

            except Exception as e:
                print(f"[{idx}/{len(candidates)}] [ERROR] {url} -> {e}")
                skipped_count += 1

    print(f"\nExtracción finalizada.")
    print(f"Nuevas noticias guardadas: {new_count} | Descartadas/Errores: {skipped_count}")
    print(f"Archivo de salida: {OUTPUT_CSV}")
    print("\nTotal acumulado por medio:")
    for medio, count in Counter(counts_by_media).most_common():
        print(f"  - {medio}: {count}")


if __name__ == "__main__":
    extract_articles()