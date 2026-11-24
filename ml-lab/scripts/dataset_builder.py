"""
Extractor y Limpiador de Noticias para el Dataset Inicial (Fase 0 - Bloque 2, Tareas 7-9).
Ubicación: ml-lab/scripts/dataset_builder.py

Propósito:
    1. Leer las URLs descubiertas (`ml-lab/datasets/discovered_urls.csv`).
    2. Descargar el HTML crudo y guardarlo en `ml-lab/datasets/raw/<medio>/`.
    3. Extraer titular, bajada, cuerpo, fecha y sección usando `trafilatura`
       (con reglas auxiliares por medio solo donde sea necesario).
    4. Limpiar HTML residual/publicidad, descartar opinión o notas muy cortas,
       y deduplicar por URL y por hash SHA-256 del cuerpo.
    5. Exportar el pool de candidatas limpias (`ml-lab/datasets/candidate_pool.csv`)
       con el esquema definido en `PHASE0_TASKS.md` (Bloque 1).

Uso:
    python ml-lab/scripts/dataset_builder.py --limit 10
"""

import argparse
import csv
import hashlib
import json
import re
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse

import httpx
import trafilatura
from bs4 import BeautifulSoup


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASETS_DIR = PROJECT_ROOT / "ml-lab" / "datasets"
RAW_HTML_DIR = DATASETS_DIR / "raw"
DEFAULT_INPUT_CSV = DATASETS_DIR / "discovered_urls.csv"
DEFAULT_OUTPUT_CSV = DATASETS_DIR / "candidate_pool.csv"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)

MIN_BODY_CHARS = 350

# Frases residuales frecuentes de navegación/promo dentro de cuerpos extraídos
NOISE_LINE_PATTERNS: List[str] = [
    r"^lee también\s*:.*$",
    r"^revisa también\s*:.*$",
    r"^te podría interesar\s*:.*$",
    r"^síguenos en\s+.*$",
    r"^comparte esta noticia.*$",
    r"^ver más\s*:.*$",
]

# Marcadores explícitos de género de opinión a excluir
OPINION_MARKERS: List[str] = [
    "columna de opinión",
    "cartas al director",
    "editorial:",
]

SUPPORTED_CHILEAN_MEDIA: List[str] = [
    "biobiochile.cl",
    "elmostrador.cl",
    "latercera.com",
    "emol.com",
    "ciperchile.cl",
    "eldesconcierto.cl",
]


@dataclass
class CandidateArticle:
    id: str
    medio: str
    url: str
    fecha: str
    titular: str
    bajada: str
    cuerpo: str
    seccion: str
    text_hash: str
    # Columnas de anotación para el Bloque 4 y 5 (se llenan en el Taller de Etiquetado)
    score_A: str = ""
    score_B: str = ""
    score_C: str = ""
    etiqueta_a1: str = ""
    confianza_a1: str = ""
    etiqueta_a2: str = ""
    confianza_a2: str = ""
    etiqueta_final: str = ""


def make_article_id(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]


def compute_text_hash(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text.strip().lower())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def clean_text_block(text: str) -> str:
    """Elimina HTML residual, espacios extra y líneas promocionales conocidas."""
    if not text:
        return ""
    # Limpiar cualquier etiqueta HTML residual si existiera
    if "<" in text and ">" in text:
        text = BeautifulSoup(text, "lxml").get_text(" ", strip=True)

    cleaned_lines: List[str] = []
    for raw_line in text.splitlines():
        line = re.sub(r"\s+", " ", raw_line).strip()
        if not line:
            continue
        if any(re.match(pat, line.lower()) for pat in NOISE_LINE_PATTERNS):
            continue
        cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip()


def extract_lead_fallback(html: str, medio: str) -> str:
    """Regla auxiliar por medio/meta-tags cuando trafilatura no entrega bajada explícita."""
    soup = BeautifulSoup(html, "lxml")

    if medio == "biobiochile.cl":
        bajada_el = soup.select_one(".post-excerpt, .bajada, h2.excerpt")
        if bajada_el:
            return clean_text_block(bajada_el.get_text(" ", strip=True))
    elif medio == "elmostrador.cl":
        bajada_el = soup.select_one(".d-the-single__excerpt, .the-single-excerpt, p.excerpt")
        if bajada_el:
            return clean_text_block(bajada_el.get_text(" ", strip=True))

    # Fallback genérico: meta description / og:description
    meta = soup.find("meta", attrs={"property": "og:description"}) or soup.find(
        "meta", attrs={"name": "description"}
    )
    if meta and meta.get("content"):
        return clean_text_block(meta["content"])
    return ""


def is_opinion_article(title: str, body: str, url: str) -> bool:
    combined = f"{url} {title} {body[:300]}".lower()
    return any(marker in combined for marker in OPINION_MARKERS)


def fetch_html(client: httpx.Client, url: str) -> Optional[str]:
    try:
        resp = client.get(url)
        resp.raise_for_status()
        return resp.text
    except httpx.HTTPError as exc:
        print(f"[ERROR] No se pudo descargar {url}: {exc}")
        return None


def save_raw_html(medio: str, article_id: str, html: str) -> Path:
    target_dir = RAW_HTML_DIR / medio
    target_dir.mkdir(parents=True, exist_ok=True)
    html_path = target_dir / f"{article_id}.html"
    html_path.write_text(html, encoding="utf-8")
    return html_path


def extract_article_from_html(
    html: str,
    url: str,
    medio: str,
    fallback_title: str = "",
    fallback_date: str = "",
    fallback_section: str = "",
) -> Optional[CandidateArticle]:
    """Extrae titular, bajada y cuerpo limpio usando trafilatura + validación."""
    extracted_json = trafilatura.extract(
        html,
        url=url,
        output_format="json",
        with_metadata=True,
        include_comments=False,
        include_tables=False,
        favor_precision=True,
    )
    if not extracted_json:
        return None

    data = json.loads(extracted_json)
    titular = clean_text_block(data.get("title") or fallback_title)
    cuerpo = clean_text_block(data.get("text") or "")
    bajada = clean_text_block(data.get("excerpt") or "") or extract_lead_fallback(html, medio)
    fecha = (data.get("date") or fallback_date or "").strip()
    seccion = (
        ",".join(data.get("categories") or [])
        if isinstance(data.get("categories"), list) and data.get("categories")
        else fallback_section
    )

    if not titular or len(cuerpo) < MIN_BODY_CHARS:
        return None
    if is_opinion_article(titular, cuerpo, url):
        return None

    # Evitar que la bajada duplique exactamente el primer párrafo del cuerpo
    if bajada and cuerpo.startswith(bajada):
        bajada = ""

    article_id = make_article_id(url)
    text_hash = compute_text_hash(cuerpo)

    return CandidateArticle(
        id=article_id,
        medio=medio,
        url=url,
        fecha=fecha,
        titular=titular,
        bajada=bajada,
        cuerpo=cuerpo,
        seccion=seccion,
        text_hash=text_hash,
    )


def build_candidate_pool(
    input_csv: Path,
    output_csv: Path,
    limit: Optional[int] = None,
    delay_seconds: float = 0.8,
) -> List[CandidateArticle]:
    """Procesa las URLs descubiertas, guarda HTML crudo, deduplica y exporta CSV."""
    if not input_csv.exists():
        raise FileNotFoundError(
            f"No existe {input_csv}. Ejecuta primero `url_discovery.py`."
        )

    with input_csv.open("r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    if limit is not None:
        rows = rows[:limit]

    articles: List[CandidateArticle] = []
    seen_urls: set[str] = set()
    seen_hashes: set[str] = set()

    headers = {"User-Agent": USER_AGENT}
    with httpx.Client(headers=headers, timeout=20.0, follow_redirects=True) as client:
        for idx, row in enumerate(rows, start=1):
            url = (row.get("url") or "").strip().rstrip("/")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)

            medio = (row.get("medio") or urlparse(url).netloc.replace("www.", "")).strip()
            html = fetch_html(client, url)
            if not html:
                continue

            article_id = make_article_id(url)
            save_raw_html(medio, article_id, html)

            article = extract_article_from_html(
                html=html,
                url=url,
                medio=medio,
                fallback_title=row.get("titulo_feed", ""),
                fallback_date=row.get("fecha_feed", ""),
                fallback_section=row.get("seccion_inferida", ""),
            )
            if not article:
                print(f"[SKIP] ({idx}/{len(rows)}) Descartada por longitud, extracción vacía u opinión: {url}")
                continue

            if article.text_hash in seen_hashes:
                print(f"[DUP] ({idx}/{len(rows)}) Contenido duplicado por hash: {url}")
                continue
            seen_hashes.add(article.text_hash)

            articles.append(article)
            print(f"[OK] ({idx}/{len(rows)}) [{medio}] {article.titular[:70]}...")
            if delay_seconds > 0 and idx < len(rows):
                time.sleep(delay_seconds)

    export_candidate_pool(articles, output_csv)
    return articles


def export_candidate_pool(articles: List[CandidateArticle], output_csv_path: Path) -> None:
    """Exporta el pool de candidatas limpias listo para el Taller de Etiquetado."""
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "id",
        "medio",
        "url",
        "fecha",
        "titular",
        "bajada",
        "cuerpo",
        "seccion",
        "text_hash",
        "score_A",
        "score_B",
        "score_C",
        "etiqueta_a1",
        "confianza_a1",
        "etiqueta_a2",
        "confianza_a2",
        "etiqueta_final",
    ]
    with output_csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for art in articles:
            writer.writerow(asdict(art))
    print(f"[SAVE] {len(articles)} noticias limpias exportadas en {output_csv_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Descarga HTML crudo y extrae noticias limpias con trafilatura (Fase 0)."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT_CSV,
        help="CSV generado por url_discovery.py.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_CSV,
        help="CSV de salida para el pool de candidatas.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limitar cantidad de URLs a procesar (útil para pruebas).",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.8,
        help="Pausa en segundos entre peticiones HTTP (default: 0.8).",
    )
    args = parser.parse_args()

    build_candidate_pool(
        input_csv=args.input,
        output_csv=args.output,
        limit=args.limit,
        delay_seconds=args.delay,
    )


if __name__ == "__main__":
    main()
