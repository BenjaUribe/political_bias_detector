import csv
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
import feedparser
import requests

FEEDS = {
    "biobiochile": [
        "https://feeds.feedburner.com/radiobiobio/NNeJ",
    ],
    "latercera": [
        "https://www.latercera.com/arc/outboundfeeds/rss/?outputType=xml",
    ],
    "exante": [
        "https://www.ex-ante.cl/feed/",
    ],
    "cooperativa": [
        "https://www.cooperativa.cl/noticias/site/tax/port/all/rss____1.xml",
    ],
    "adnradio": [
        "https://www.adnradio.cl/arc/outboundfeeds/rss/?outputType=xml",
    ],
    "theclinic": [
        "https://www.theclinic.cl/feed/",
    ],
    "radiouchile": [
        "https://radio.uchile.cl/feed/",
    ],
    "elciudadano": [
        "https://www.elciudadano.com/feed/",
    ],
    "ciperchile": [
        "https://www.ciperchile.cl/feed/",
    ],
}

EXCLUDED_KEYWORDS = [
    "/opinion",
    "/columnas",
    "/cartas",
    "/editorial",
    "/deportes",
    "/espectaculos",
    "/entretenimiento",
    "/entretencion",
    "/cultura",
    "/dopamina",
    "/internacional",
    "/mundo/",
    "/el-semanal",
    "/multimedia",
    "/tv",
    "/podcast",
    "/video",
    "/tiempo-libre",
    "/tendencias",
    "/horoscopo",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.8",
}

BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_PATH = BASE_DIR / "datasets" / "candidate_urls.csv"
FIELDNAMES = ["medio", "url", "titular_rss", "fecha_rss", "descubierto_en"]


def is_valid_url(url: str) -> bool:
    url_lower = url.lower()
    return not any(keyword in url_lower for keyword in EXCLUDED_KEYWORDS)


def load_existing_candidates(output_path: Path) -> tuple[list[dict], set[str]]:
    if not output_path.exists():
        return [], set()

    with open(output_path, mode="r", encoding="utf-8") as f:
        existing = list(csv.DictReader(f))
    seen_urls = {row["url"].strip() for row in existing if row.get("url")}
    return existing, seen_urls


def discover_urls(seen_urls: set[str]) -> list[dict]:
    new_candidates = []

    for medio, rss_list in FEEDS.items():
        for rss_url in rss_list:
            try:
                resp = requests.get(rss_url, headers=HEADERS, timeout=15)
                content_type = resp.headers.get("Content-Type", "").lower()
                print(f"[{medio}] {rss_url} -> HTTP {resp.status_code}")

                if resp.status_code != 200:
                    continue

                if "html" in content_type and "xml" not in content_type:
                    print("  [AVISO] El servidor devolvió HTML en lugar de XML/RSS.")
                    continue

                feed = feedparser.parse(resp.content)
                print(f"  Entradas encontradas en feed: {len(feed.entries)}")

                for entry in feed.entries:
                    url = entry.get("link", "").strip()
                    if not url or url in seen_urls or not is_valid_url(url):
                        continue

                    seen_urls.add(url)
                    new_candidates.append({
                        "medio": medio,
                        "url": url,
                        "titular_rss": entry.get("title", "").strip(),
                        "fecha_rss": entry.get("published", ""),
                        "descubierto_en": datetime.now().isoformat(timespec="seconds"),
                    })

                time.sleep(0.5)
            except requests.RequestException as e:
                print(f"[{medio}] Error al consultar {rss_url}: {e}")

    return new_candidates


def save_candidates(candidates: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(candidates)


if __name__ == "__main__":
    existing_candidates, seen_urls = load_existing_candidates(OUTPUT_PATH)
    new_candidates = discover_urls(seen_urls)
    all_candidates = existing_candidates + new_candidates

    save_candidates(all_candidates, OUTPUT_PATH)

    print(f"\nURLs nuevas agregadas: {len(new_candidates)}")
    print(f"Total acumulado en CSV: {len(all_candidates)} -> {OUTPUT_PATH}")
    print("\nResumen por medio:")
    for medio, count in Counter(r["medio"] for r in all_candidates).most_common():
        print(f"  - {medio}: {count}")