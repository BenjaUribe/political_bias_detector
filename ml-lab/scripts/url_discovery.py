"""
Descubrimiento de URLs de noticias desde RSS o Sitemaps (Fase 0 - Bloque 2, Tarea 6).
Ubicación: ml-lab/scripts/url_discovery.py

Propósito:
    Consultar feeds RSS o sitemaps XML de medios chilenos seleccionados,
    filtrar secciones no elegibles (opinión, columnas, deportes, farándula, clima)
    y generar una lista revisable de URLs (`discovered_urls.csv`) antes de descargar HTML.

Uso:
    python ml-lab/scripts/url_discovery.py --media biobiochile.cl elmostrador.cl --limit 25
"""

import argparse
import csv
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse

import httpx


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "ml-lab" / "datasets" / "discovered_urls.csv"

USER_AGENT = (
    "PoliticalBiasDetectorBot/0.1 (Academic/Personal NLP Research; "
    "+https://github.com/political_bias_detector)"
)

# Patrones de URL que corresponden a secciones excluidas (Bloque 1: Tarea 2 y Bloque 2: Tarea 6)
EXCLUDED_URL_PATTERNS: List[str] = [
    r"/opinion/",
    r"/columnas/",
    r"/columna/",
    r"/editorial/",
    r"/cartas-al-director/",
    r"/deportes/",
    r"/bbcl-tv/",
    r"/espectaculos/",
    r"/espectaculos-y-tv/",
    r"/entretencion/",
    r"/cultura/",
    r"/cultura-y-entretencion/",
    r"/revista-jengibre/",
    r"/gastronomia/",
    r"/datos-utiles/",
    r"/servicios/",
    r"/ciencia-y-tecnologia/",
    r"/tendencias/",
    r"/horoscopo/",
    r"/tiempo/",
    r"/clima/",
    r"/podcast/",
    r"/videos/",
    r"/especial/",
]

# Configuración inicial de feeds/sitemaps por medio (empezando con 2 medios de prueba - Tarea 9)
MEDIA_SOURCES: Dict[str, List[Dict[str, str]]] = {
    "biobiochile.cl": [
        {
            "type": "sitemap",
            "url": "https://www.biobiochile.cl/news-sitemap.xml",
            "section": "news-sitemap",
        },
    ],
    "elmostrador.cl": [
        {
            "type": "sitemap",
            "url": "https://www.elmostrador.cl/sitemap_news.xml",
            "section": "news-sitemap",
        },
    ],
}


@dataclass
class DiscoveredURL:
    medio: str
    url: str
    titulo_feed: str
    fecha_feed: str
    seccion_inferida: str
    fuente_descubrimiento: str


def is_eligible_url(url: str) -> bool:
    """Descarta URLs vacías o pertenecientes a secciones excluidas (opinión, deportes, etc.)."""
    if not url or not url.startswith("http"):
        return False
    lowered = url.lower()
    return not any(re.search(pattern, lowered) for pattern in EXCLUDED_URL_PATTERNS)


def _strip_ns(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag


def _find_child_text(element: ET.Element, target_names: List[str]) -> str:
    for child in element:
        if _strip_ns(child.tag) in target_names and child.text:
            return child.text.strip()
    return ""


def parse_rss_or_atom(
    xml_content: str,
    medio: str,
    default_section: str,
    source_url: str,
) -> List[DiscoveredURL]:
    """Extrae URLs y metadatos básicos desde un feed RSS 2.0 o Atom."""
    root = ET.fromstring(xml_content)
    results: List[DiscoveredURL] = []

    # RSS 2.0: <channel>/<item>
    for item in root.iter():
        tag_name = _strip_ns(item.tag)
        if tag_name == "item":
            link = _find_child_text(item, ["link"])
            title = _find_child_text(item, ["title"])
            pub_date = _find_child_text(item, ["pubDate", "date", "published"])
            category = _find_child_text(item, ["category"]) or default_section
            if is_eligible_url(link):
                results.append(
                    DiscoveredURL(
                        medio=medio,
                        url=link,
                        titulo_feed=title,
                        fecha_feed=pub_date,
                        seccion_inferida=category,
                        fuente_descubrimiento=source_url,
                    )
                )
        elif tag_name == "entry":
            # Atom: <entry><link href="..."/>
            link = ""
            for child in item:
                if _strip_ns(child.tag) == "link":
                    href = child.attrib.get("href", "")
                    if href:
                        link = href.strip()
                        break
            title = _find_child_text(item, ["title"])
            pub_date = _find_child_text(item, ["published", "updated"])
            if is_eligible_url(link):
                results.append(
                    DiscoveredURL(
                        medio=medio,
                        url=link,
                        titulo_feed=title,
                        fecha_feed=pub_date,
                        seccion_inferida=default_section,
                        fuente_descubrimiento=source_url,
                    )
                )
    return results


def parse_sitemap(
    xml_content: str,
    medio: str,
    default_section: str,
    source_url: str,
) -> List[DiscoveredURL]:
    """Extrae URLs desde un Sitemap XML estándar (<urlset>/<url>/<loc>)."""
    root = ET.fromstring(xml_content)
    results: List[DiscoveredURL] = []

    for url_node in root.iter():
        if _strip_ns(url_node.tag) == "url":
            loc = _find_child_text(url_node, ["loc"])
            lastmod = _find_child_text(url_node, ["lastmod", "publication_date"])
            title = _find_child_text(url_node, ["title"])
            if is_eligible_url(loc):
                results.append(
                    DiscoveredURL(
                        medio=medio,
                        url=loc,
                        titulo_feed=title,
                        fecha_feed=lastmod,
                        seccion_inferida=default_section,
                        fuente_descubrimiento=source_url,
                    )
                )
    return results


def discover_urls_for_media(
    media_list: List[str],
    limit_per_media: int = 30,
    timeout: float = 15.0,
) -> List[DiscoveredURL]:
    """Consulta los feeds/sitemaps de cada medio y retorna URLs deduplicadas."""
    discovered: List[DiscoveredURL] = []
    seen_urls: set[str] = set()

    headers = {"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/xml, text/xml"}

    with httpx.Client(headers=headers, timeout=timeout, follow_redirects=True) as client:
        for medio in media_list:
            sources = MEDIA_SOURCES.get(medio, [])
            if not sources:
                print(f"[WARN] No hay fuentes configuradas para '{medio}'.")
                continue

            media_count = 0
            for src in sources:
                if media_count >= limit_per_media:
                    break
                src_url = src["url"]
                src_type = src.get("type", "rss")
                section = src.get("section", "general")

                try:
                    resp = client.get(src_url)
                    resp.raise_for_status()
                except httpx.HTTPError as exc:
                    print(f"[ERROR] Falló descarga de {src_url}: {exc}")
                    continue

                try:
                    if src_type == "sitemap":
                        entries = parse_sitemap(resp.text, medio, section, src_url)
                    else:
                        entries = parse_rss_or_atom(resp.text, medio, section, src_url)
                except ET.ParseError as exc:
                    print(f"[ERROR] XML inválido en {src_url}: {exc}")
                    continue

                for entry in entries:
                    normalized = entry.url.split("?")[0].rstrip("/")
                    if normalized in seen_urls:
                        continue
                    seen_urls.add(normalized)
                    entry.url = normalized
                    discovered.append(entry)
                    media_count += 1
                    if media_count >= limit_per_media:
                        break

            print(f"[OK] {medio}: {media_count} URLs elegibles descubiertas.")

    return discovered


def save_discovered_urls(entries: List[DiscoveredURL], output_path: Path) -> None:
    """Guarda la lista revisable de URLs en CSV UTF-8."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "medio",
        "url",
        "titulo_feed",
        "fecha_feed",
        "seccion_inferida",
        "fuente_descubrimiento",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for entry in entries:
            writer.writerow(asdict(entry))
    print(f"[SAVE] {len(entries)} URLs guardadas en {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Descubre URLs elegibles desde RSS/Sitemaps de medios chilenos (Fase 0)."
    )
    parser.add_argument(
        "--media",
        nargs="+",
        default=list(MEDIA_SOURCES.keys()),
        help="Lista de dominios configurados a consultar (por defecto todos los configurados).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=25,
        help="Máximo de URLs por medio (default: 25).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Ruta del CSV de salida.",
    )
    args = parser.parse_args()

    entries = discover_urls_for_media(args.media, limit_per_media=args.limit)
    save_discovered_urls(entries, args.output)


if __name__ == "__main__":
    main()
