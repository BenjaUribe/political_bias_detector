import csv
import html
import re
from pathlib import Path
import trafilatura

BASE_DIR = Path(__file__).resolve().parents[1]
CSV_PATH = BASE_DIR / "datasets" / "extracted_pool.csv"
RAW_HTML_DIR = BASE_DIR / "datasets" / "raw_html"


def clean_text(text: str | None) -> str:
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def fallback_meta_regex(raw_html: str) -> tuple[str, str]:
    title = ""
    desc = ""

    og_title = re.search(
        r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']',
        raw_html,
        re.IGNORECASE,
    )
    if og_title:
        title = og_title.group(1)
    else:
        title_tag = re.search(r"<title[^>]*>(.*?)</title>", raw_html, re.IGNORECASE | re.DOTALL)
        if title_tag:
            title = title_tag.group(1)

    og_desc = re.search(
        r'<meta[^>]+(?:property=["\']og:description["\']|name=["\']description["\'])[^>]+content=["\']([^"\']+)["\']',
        raw_html,
        re.IGNORECASE,
    )
    if og_desc:
        desc = og_desc.group(1)

    return clean_text(title), clean_text(desc)


def repair_metadata() -> None:
    if not CSV_PATH.exists():
        print(f"No se encontró {CSV_PATH}")
        return

    with open(CSV_PATH, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    repaired_titles = 0
    repaired_bajadas = 0
    missing_titles = 0

    for row in rows:
        article_id = row["id"].strip()
        raw_path = RAW_HTML_DIR / f"{article_id}.html"
        if not raw_path.exists():
            continue

        raw_html = raw_path.read_text(encoding="utf-8", errors="ignore")
        meta = trafilatura.extract_metadata(raw_html, default_url=row.get("url"))

        title = clean_text(meta.title) if meta and meta.title else ""
        bajada = clean_text(meta.description) if meta and meta.description else ""
        fecha = meta.date.strip() if meta and meta.date else ""

        if not title or not bajada:
            fb_title, fb_desc = fallback_meta_regex(raw_html)
            if not title:
                title = fb_title
            if not bajada:
                bajada = fb_desc

        if not row.get("titular") and title:
            row["titular"] = title
            repaired_titles += 1
        if not row.get("bajada") and bajada:
            row["bajada"] = bajada
            repaired_bajadas += 1
        if not row.get("fecha") and fecha:
            row["fecha"] = fecha

        if not row.get("titular"):
            missing_titles += 1

    with open(CSV_PATH, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Reparación completada en {CSV_PATH}")
    print(f"  - Titulares recuperados: {repaired_titles}/{len(rows)}")
    print(f"  - Bajadas recuperadas:   {repaired_bajadas}/{len(rows)}")
    print(f"  - Sin titular restante:  {missing_titles}")


if __name__ == "__main__":
    repair_metadata()