"""
Sanitizador y Deduplicador de Dataset de Noticias (Fase 0 - Bloque 2, Tarea 8).
Ubicación: ml-lab/scripts/sanitize_dataset.py

Propósito:
    Limpiar, validar y deduplicar un CSV de noticias recolectadas desde múltiples medios:
    1. Deduplicación exacta por URL normalizada y por hash SHA-256 del cuerpo.
    2. Deduplicación casi exacta por similitud de titular (ej. cables de agencias como EFE)
       y similitud de inicio del cuerpo.
    3. Filtro de género y temática: descarta columnas de opinión, editoriales, cartas al
       director, deportes y policiales puros (por URL, sección y heurísticas léxicas).
    4. Filtro de extensión: descarta notas con menos de `min_words` palabras (default: 120).
    5. Limpieza profunda: elimina residuos HTML, pies de foto, avisos de suscripción y
       enlaces tipo "Lee también..." incluso al final de los párrafos.

Uso:
    python ml-lab/scripts/sanitize_dataset.py --input ml-lab/datasets/raw_480.csv --output ml-lab/datasets/sanitized_pool.csv
"""

import argparse
import csv
import hashlib
import html as html_lib
import re
import unicodedata
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from bs4 import BeautifulSoup


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_CSV = PROJECT_ROOT / "ml-lab" / "datasets" / "candidate_pool.csv"
DEFAULT_OUTPUT_CSV = PROJECT_ROOT / "ml-lab" / "datasets" / "sanitized_pool.csv"
DEFAULT_AUDIT_CSV = PROJECT_ROOT / "ml-lab" / "datasets" / "discarded_audit.csv"

# Parámetros de tracking que se eliminan al normalizar URLs
TRACKING_QUERY_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "fbclid",
    "gclid",
    "ref",
    "outputType",
}

# Patrones de secciones/URLs excluidas por género o tema
EXCLUDED_URL_OR_SECTION_PATTERNS: List[Tuple[str, str]] = [
    (r"/(opinion|opinión|columnas?|editorial|cartas-al-director|entrevista)/", "excluded_genre_opinion_or_interview"),
    (r"/(deportes?|el-deportivo|futbol|fútbol|tenis|basquetbol|básquetbol|golf)/", "excluded_topic_sports"),
    (r"/(espectaculos|espectáculos|entretencion|entretención|cultura|culto|artes-y-cultura|cine|cine-y-series|tv|farándula|farandula|horoscopo|horóscopo|magazine|finde|paula)/", "excluded_topic_entertainment_culture"),
    (r"/(especial|corporativo|club-la-tercera|avisos_a_socios|servicios|afteroffice|lt-board|tecnologia|ciencia-y-tecnologia|salud-y-bienestar)/", "excluded_topic_offtopic_or_corporate"),
    (r"/(policial|sucesos|cronica-roja|crónica-roja)/", "excluded_topic_crime_pure"),
]

# Marcadores de género de opinión en titular o inicio del cuerpo
OPINION_MARKERS = (
    "columna de opinión",
    "columna de opinion",
    "cartas al director",
    "carta al director",
    "editorial:",
    "la opinión de",
    "opinión |",
    "análisis de",
)

# Términos fuertes para detectar notas netamente deportivas (si aparecen múltiples)
SPORTS_KEYWORDS = {
    "campeonato nacional",
    "copa libertadores",
    "copa sudamericana",
    "champions league",
    "torneo de clausura",
    "torneo de apertura",
    "selección chilena",
    "la roja",
    "goles",
    "penales",
    "tiro de esquina",
    "tarjeta amarilla",
    "tarjeta roja",
    "estadio monumental",
    "estadio nacional",
    "entrenador",
    "director técnico",
}

# Términos de crónica roja / policial puro (solo se descarta si NO hay contexto político/legislativo)
PURE_CRIME_KEYWORDS = {
    "portonazo",
    "encerrona",
    "homicidio",
    "baleado",
    "balacera",
    "puñaladas",
    "detenido por robo",
    "robo con intimidación",
    "asalto a mano armada",
    "hallazgo de cadáver",
    "cuerpo sin vida",
}

POLITICAL_OR_POLICY_CONTEXT = {
    "gobierno",
    "ministerio",
    "ministro",
    "ministra",
    "congreso",
    "senado",
    "cámara de diputados",
    "proyecto de ley",
    "ley",
    "reforma",
    "presupuesto",
    "política pública",
    "politica publica",
    "fiscalía nacional",
    "subsecretaría",
    "municipio",
    "alcalde",
    "recurso",
}

OFFTOPIC_KEYWORDS = {
    "tormenta eléctrica",
    "precipitaciones",
    "sistema frontal",
    "aluvión",
    "hutíes",
    "arabia saudita",
    "premio nobel de economía",
}

CHILE_CONTEXT_KEYWORDS = {
    "chile",
    "chileno",
    "chilena",
    "chilenos",
    "chilenas",
    "santiago",
    "valparaíso",
    "la moneda",
    "congreso",
    "senado",
    "cámara de diputados",
    "ministerio",
    "banco central",
    "senapred",
}

# Patrones de ruido a limpiar dentro de párrafos o líneas completas
INLINE_NOISE_PATTERNS: List[str] = [
    r"(?:lee|revisa|mira|ver)\s+también\s*:.*$",
    r"te\s+podría\s+interesar\s*:.*$",
    r"noticias\s+relacionadas\s*:.*$",
    r"contenido\s+exclusivo\s+para\s+suscriptores.*$",
    r"suscríbete\s+(?:a|para|en)\s+.*$",
    r"inicia\s+sesión\s+para\s+seguir\s+leyendo.*$",
    r"hazte\s+socio\s+de\s+.*$",
    r"síguenos\s+en\s+(?:google\s+news|instagram|facebook|twitter|x|whatsapp).*$",
    r"comparte\s+esta\s+noticia.*$",
]

LEADING_BOILERPLATE_PATTERNS: List[str] = [
    r"^.*?VER\s+RESUMEN\s+Resumen\s+generado\s+con\s+una\s+herramienta\s+de\s+Inteligencia\s+Artificial.*?artículo\.?\s*",
    r"^.*?>\s*Noticia\s+[^|]+\|\s*\d{1,2}:\d{2}\s+",
]

# --- Diccionarios para text_anonymized ---
MEDIA_ALIASES: List[str] = [
    "BioBioChile",
    "Radio Bío-Bío",
    "Radio Bio-Bio",
    "Bío-Bío",
    "Bío Bío",
    "BioBio",
    "Ex-Ante",
    "Ex Ante",
    "CIPER Chile",
    "CIPER",
    "The Clinic",
    "Radio Cooperativa",
    "Cooperativa.cl",
    "Cooperativa",
]

# "La Tercera" se maneja aparte con lookahead para no afectar "La Tercera Sala" ni "la tercera vez"
LA_TERCERA_RE = re.compile(r"\bLa Tercera\b(?!\s+Sala\b)")

PARTY_AND_COALITION_NAMES: List[str] = [
    "Unión Demócrata Independiente",
    "Renovación Nacional",
    "Evolución Política",
    "Evópoli",
    "Partido Republicano",
    "Republicanos",
    "Partido Social Cristiano",
    "Democracia Cristiana",
    "Partido Demócrata Cristiano",
    "Partido Por la Democracia",
    "Partido Socialista",
    "Frente Amplio",
    "Partido Comunista",
    "Partido Radical",
    "Partido Liberal",
    "Partido de la Gente",
    "Amarillos por Chile",
    "Demócratas",
    "Chile Vamos",
    "Socialismo Democrático",
    "Apruebo Dignidad",
    "Revolución Democrática",
    "Convergencia Social",
    "Comunes",
]

PARTY_ACRONYMS: List[str] = [
    "UDI",
    "RN",
    "PSC",
    "DC",
    "PDC",
    "PPD",
    "PS",
    "FA",
    "PC",
    "PR",
    "PL",
    "PDG",
    "RD",
]

_PARTY_ACRONYMS_GROUP = "|".join(PARTY_ACRONYMS)
_POLITICAL_CONTEXT_NOUNS = (
    r"(?:partido|bancada|comité|directiva|timonel|presidente|presidenta|"
    r"vicepresidente|vicepresidenta|secretario|secretaria|vocero|vocera|"
    r"militante|militantes|dirigente|dirigentes|diputado|diputada|diputados|diputadas|"
    r"senador|senadora|senadores|senadoras|alcalde|alcaldesa|alcaldes|"
    r"gobernador|gobernadora|candidato|candidata|precandidato|precandidata|"
    r"ministro|ministra|exministro|exministra|subsecretario|subsecretaria|"
    r"jefe\s+de\s+bancada|parlamentario|parlamentaria|parlamentarios|"
    r"legislador|legisladora|legisladores|lista|pacto)"
)

PARTY_ACRONYM_PARENS_RE = re.compile(rf"\((?:{_PARTY_ACRONYMS_GROUP})\)")
PARTY_ACRONYM_CONTEXT_BEFORE_RE = re.compile(
    rf"\b((?i:{_POLITICAL_CONTEXT_NOUNS})\s+(?:(?i:de\s+la|del|de)\s+)?)(?:{_PARTY_ACRONYMS_GROUP})\b"
)
PARTY_ACRONYM_CONTEXT_AFTER_RE = re.compile(
    rf"\b(?:{_PARTY_ACRONYMS_GROUP})\b(?=\s+(?i:{_POLITICAL_CONTEXT_NOUNS})\b)"
)

KNOWN_CHILEAN_POLITICIANS: List[str] = [
    "Gabriel Boric",
    "José Antonio Kast",
    "Evelyn Matthei",
    "Michelle Bachelet",
    "Sebastián Piñera",
    "Johannes Kaiser",
    "Carolina Tohá",
    "Mario Marcel",
    "Camila Vallejo",
    "Jeannette Jara",
    "Gonzalo Winter",
    "Tomás Vodanovic",
    "Rodolfo Carter",
    "Matías Walker",
    "Ximena Rincón",
    "Javier Macaya",
    "Guillermo Ramírez",
    "Paulina Vodanovic",
    "Lautaro Carmona",
    "Jaime Quintana",
    "Manuel José Ossandón",
    "Franco Parisi",
    "Marco Enríquez-Ominami",
    "Giorgio Jackson",
    "Izkia Siches",
    "Maya Fernández",
    "Álvaro Elizalde",
    "Luis Cordero",
    "Alberto van Klaveren",
    "Nicolás Grau",
    "Jaime Gajardo",
    "Antonia Orellana",
    "Diego Pardow",
    "Juan Carlos Muñoz",
    "Jessica López",
    "Carlos Montes",
    "Ximena Aguilera",
    "Nicolás Cataldo",
    "Esteban Valenzuela",
    "Aurora Williams",
    "Maisa Rojas",
    "Marcela Sandoval",
    "Aisén Etcheverry",
    "Rodrigo Galilea",
    "Gloria Hutt",
    "Arturo Squella",
    "Fidel Espinoza",
    "Rojo Edwards",
    "Karol Cariola",
    "Daniel Jadue",
    "Irací Hassler",
    "Mario Desbordes",
    "Claudio Orrego",
    "Francisco Orrego",
    "Macarena Ripamonti",
    "Camila Flores",
    "Diego Schalper",
    "Juan Antonio Coloma",
    "Luciano Cruz-Coke",
    "Vlado Mirosevic",
    "Raúl Soto",
    "Pamela Jiles",
    "Yasna Provoste",
    "Iván Moreira",
    "Matías Toledo",
    "Catalina Pérez",
    "Maite Orsini",
    # Gabinete y Congreso 2026
    "Trinidad Steinert",
    "Martín Arrau",
    "Fernando Rabat",
    "Jorge Quiroz",
    "Ximena Lincolao",
    "Carolina Rossi",
    "Raúl Leiva",
    "Luis Fernando Sánchez",
    "Benjamín Moreno",
]

# Palabras comunes o apellidos muy polisémicos que NO deben reemplazarse sueltos en 2da pasada
COMMON_SURNAME_EXCLUSIONS = {
    "Rojas",
    "Flores",
    "Campos",
    "Fuentes",
    "Reyes",
    "Cortés",
    "Blanco",
    "Mesa",
    "Cruz",
    "Paz",
    "León",
    "Sierra",
    "Prado",
    "Vega",
    "Silva",
    "Soto",
    "Lara",
    "Mora",
    "Lagos",
    "Ríos",
    "Montes",
    "Bravo",
    "Castillo",
    "Guerra",
    "Paredes",
    "Salas",
    "Valle",
    "Vera",
    "Estado",
    "Chile",
    "Gobierno",
    "República",
    "Nacional",
    "Público",
    "Justicia",
    "Hacienda",
    "Interior",
    "Salud",
    "Trabajo",
    "Educación",
    "Economía",
    "Defensa",
    "Energía",
    "Medio",
    "Ambiente",
}

POLITICAL_ROLE_NAME_RE = re.compile(
    r"\b(presidente|presidenta|expresidente|expresidenta|ministro|ministra|"
    r"exministro|exministra|subsecretario|subsecretaria|senador|senadora|"
    r"exsenador|exsenadora|diputado|diputada|exdiputado|exdiputada|"
    r"alcalde|alcaldesa|gobernador|gobernadora|candidato|candidata|"
    r"precandidato|precandidata|timonel|vocero|vocera|convencional|consejero)\s+"
    r"(?:de\s+[a-záéíóúñ]+\s+)?([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+(?:de\s+|del\s+|van\s+)?[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){0,2})"
)

PHOTO_CREDIT_LINE_PATTERNS: List[str] = [
    r"^(?:foto|fotografía|imagen|crédito|fuente)\s*:\s*.*$",
    r"^imagen\s+referencial\.?$",
    r"^agencia\s+uno\s*/?.*$",
    r"^archivo\s*\|\s*.*$",
]


def strip_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)
    )


def normalize_url(url: str) -> str:
    """Normaliza URL eliminando parámetros de tracking, fragmentos y slash final."""
    url = url.strip()
    if not url:
        return ""
    parsed = urlparse(url)
    clean_query = [
        (k, v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=False)
        if k not in TRACKING_QUERY_PARAMS
    ]
    normalized = parsed._replace(
        scheme=parsed.scheme.lower(),
        netloc=parsed.netloc.lower().replace("www.", ""),
        path=parsed.path.rstrip("/"),
        query=urlencode(clean_query),
        fragment="",
    )
    return urlunparse(normalized)


def normalize_for_similarity(text: str) -> str:
    """Normaliza texto (minúsculas, sin tildes ni puntuación) para hash o comparación."""
    text = strip_accents(text.lower())
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def compute_text_hash(text: str) -> str:
    return hashlib.sha256(normalize_for_similarity(text).encode("utf-8")).hexdigest()[:16]


MOJIBAKE_PAIR_RE = re.compile(
    r"[\u00c2-\u00f4][\u0080-\u00bf\u20ac\u201a\u0192\u201e\u2026\u2020\u2021\u02c6\u2030\u0160\u2039\u0152\u017d\u2018\u2019\u201c\u201d\u2022\u2013\u2014\u02dc\u2122\u0161\u203a\u0153\u017e\u0178]{1,3}"
)


def _decode_mojibake_match(match: re.Match) -> str:
    token = match.group(0)
    try:
        return token.encode("cp1252").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        try:
            return token.encode("latin-1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            return token


def fix_mojibake(text: str) -> str:
    """Repara secuencias con doble codificación UTF-8->Latin1/CP1252 y 'Ã' residual."""
    if not text:
        return ""
    if "Ã" in text or "Â" in text:
        text = MOJIBAKE_PAIR_RE.sub(_decode_mojibake_match, text)
        # Caso especial observado en biobiochile: 'í' (\xc3\xad) perdió el byte 0xAD y quedó como 'Ã'
        text = re.sub(r"Ã(?=[a-z])", "í", text)
        text = text.replace("Â", "")
    return text


def anonymize_text(titular: str, bajada: str, cuerpo: str) -> str:
    """Construye `text_anonymized` ocultando medios, partidos y políticos chilenos."""
    parts = [p.strip() for p in (titular, bajada, cuerpo) if p and p.strip()]
    text = "\n".join(parts)
    if not text:
        return ""

    # 1. Ocultar nombres de los medios (sin "Pulso" ni "La Tercera Sala")
    text = LA_TERCERA_RE.sub("[MEDIO]", text)
    for alias in sorted(MEDIA_ALIASES, key=len, reverse=True):
        text = re.sub(rf"\b{re.escape(alias)}\b", "[MEDIO]", text, flags=re.IGNORECASE)

    # 2. Ocultar partidos y coaliciones
    for party in sorted(PARTY_AND_COALITION_NAMES, key=len, reverse=True):
        text = re.sub(rf"\b{re.escape(party)}\b", "[PARTIDO]", text, flags=re.IGNORECASE)
    # Para siglas cortas (PC, PS, RN, etc.), exigir paréntesis o contexto político explícito
    text = PARTY_ACRONYM_PARENS_RE.sub("([PARTIDO])", text)
    text = PARTY_ACRONYM_CONTEXT_BEFORE_RE.sub(r"\1[PARTIDO]", text)
    text = PARTY_ACRONYM_CONTEXT_AFTER_RE.sub("[PARTIDO]", text)

    # 3. Ocultar políticos conocidos y menciones por cargo + nombre propio
    detected_full_names: List[str] = []

    for person in sorted(KNOWN_CHILEAN_POLITICIANS, key=len, reverse=True):
        pattern = re.compile(rf"\b{re.escape(person)}\b")
        if pattern.search(text):
            detected_full_names.append(person)
            text = pattern.sub("[POLITICO]", text)

    def _replace_role_name(match: re.Match) -> str:
        detected_full_names.append(match.group(2))
        return f"{match.group(1)} [POLITICO]"

    text = POLITICAL_ROLE_NAME_RE.sub(_replace_role_name, text)

    # 4. Segunda pasada: ocultar apellidos sueltos de los políticos detectados (>3 letras y no comunes)
    surnames: set[str] = set()
    for full_name in detected_full_names:
        parts = full_name.strip().split()
        if len(parts) >= 2:
            surname = parts[-1]
            if len(surname) > 3 and surname not in COMMON_SURNAME_EXCLUSIONS:
                surnames.add(surname)

    for surname in sorted(surnames, key=len, reverse=True):
        text = re.sub(rf"\b{re.escape(surname)}\b", "[POLITICO]", text)

    return text


def clean_article_text(text: str, bajada: str = "") -> str:
    """Elimina mojibake, HTML residual, pies de foto, avisos de suscripción y 'Lee también...'."""
    if not text:
        return ""

    text = fix_mojibake(text)
    text = html_lib.unescape(text)
    if "<" in text and ">" in text:
        text = BeautifulSoup(text, "lxml").get_text("\n", strip=True)

    for lead_pat in LEADING_BOILERPLATE_PATTERNS:
        text = re.sub(lead_pat, "", text, flags=re.IGNORECASE | re.DOTALL).strip()

    # Si sigue empezando con VER RESUMEN y conocemos la bajada, recortar todo lo previo a la bajada
    if re.match(r"^(?:.*?>\s*Noticia\s+.*?)?VER\s+RESUMEN\b", text, flags=re.IGNORECASE):
        bajada_clean = bajada.strip().rstrip(".")
        if len(bajada_clean) >= 25:
            anchor = bajada_clean[:40]
            idx = text.find(anchor)
            if idx != -1:
                text = text[idx:].strip()
        text = re.sub(r"^VER\s+RESUMEN\s+", "", text, flags=re.IGNORECASE).strip()

    cleaned_paragraphs: List[str] = []
    for raw_para in text.splitlines():
        para = re.sub(r"\s+", " ", raw_para).strip()
        if not para:
            continue

        # Descartar líneas completas que son créditos/pies de foto
        if any(re.match(pat, para.lower()) for pat in PHOTO_CREDIT_LINE_PATTERNS):
            continue

        # Recortar ruido al final del párrafo (ej. "...en la región. Lee también: ...")
        for pat in INLINE_NOISE_PATTERNS:
            para = re.sub(pat, "", para, flags=re.IGNORECASE).strip()

        # Limpiar separadores sobrantes si quedó algo truncado
        para = para.rstrip("|-• ").strip()
        if para and len(para) > 3:
            cleaned_paragraphs.append(para)

    return "\n".join(cleaned_paragraphs).strip()


def count_words(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def classify_discard_reason(
    url: str,
    seccion: str,
    titular: str,
    cuerpo: str,
    min_words: int,
) -> Optional[str]:
    """Retorna motivo de descarte si la nota no es elegible, o None si pasa todos los filtros."""
    url_and_section = f"{url} /{seccion}/".lower()
    for pattern, reason in EXCLUDED_URL_OR_SECTION_PATTERNS:
        if re.search(pattern, url_and_section):
            return reason

    head_text = f"{titular} {cuerpo[:400]}".lower()
    if any(marker in head_text for marker in OPINION_MARKERS):
        return "excluded_genre_opinion"

    words = count_words(cuerpo)
    if words < min_words:
        return f"too_short (<{min_words} words: {words})"

    full_lower = f"{titular} {cuerpo}".lower()

    # Heurística de deportes: >= 2 señales deportivas fuertes sin contexto político
    sports_hits = sum(1 for kw in SPORTS_KEYWORDS if kw in full_lower)
    if sports_hits >= 2 and not any(p in full_lower for p in POLITICAL_OR_POLICY_CONTEXT):
        return "excluded_topic_sports"

    # Heurística policial puro: >= 2 señales de crónica roja sin contexto de política pública/legislativa
    crime_hits = sum(1 for kw in PURE_CRIME_KEYWORDS if kw in full_lower)
    if crime_hits >= 2 and not any(p in full_lower for p in POLITICAL_OR_POLICY_CONTEXT):
        return "excluded_topic_crime_pure"

    # Heurística off-topic (meteorología o internacional sin relación con Chile/instituciones chilenas)
    offtopic_hits = sum(1 for kw in OFFTOPIC_KEYWORDS if kw in full_lower)
    if offtopic_hits >= 2 and not any(c in full_lower for c in CHILE_CONTEXT_KEYWORDS):
        return "excluded_topic_weather_or_international"

    return None


def title_similarity(t1: str, t2: str) -> float:
    n1 = normalize_for_similarity(t1)
    n2 = normalize_for_similarity(t2)
    if not n1 or not n2:
        return 0.0
    return SequenceMatcher(None, n1, n2).ratio()


def body_prefix_similarity(b1: str, b2: str, chars: int = 400) -> float:
    n1 = normalize_for_similarity(b1[:chars])
    n2 = normalize_for_similarity(b2[:chars])
    if not n1 or not n2:
        return 0.0
    return SequenceMatcher(None, n1, n2).ratio()


def resolve_column(row: Dict[str, str], candidates: Tuple[str, ...]) -> str:
    for col in candidates:
        if col in row and row[col] is not None:
            return row[col].strip()
    return ""


def sanitize_and_deduplicate(
    input_csv: Path,
    output_csv: Path,
    audit_csv: Optional[Path] = None,
    min_words: int = 120,
    title_sim_threshold: float = 0.85,
    body_sim_threshold: float = 0.85,
) -> Dict[str, int]:
    """Ejecuta limpieza, filtros temáticos/extensión y deduplicación sobre el CSV."""
    if not input_csv.exists():
        raise FileNotFoundError(f"No se encontró el archivo de entrada: {input_csv}")

    with input_csv.open("r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        input_rows = list(reader)
        original_fieldnames = list(reader.fieldnames or [])

    kept_rows: List[Dict[str, str]] = []
    discarded_rows: List[Dict[str, str]] = []
    stats: Counter[str] = Counter()

    seen_urls: set[str] = set()
    seen_hashes: set[str] = set()
    kept_signatures: List[Tuple[str, str]] = []  # (titular, cuerpo)

    for row in input_rows:
        raw_url = resolve_column(row, ("url", "link"))
        norm_url = normalize_url(raw_url)
        medio = resolve_column(row, ("medio", "source_domain", "source"))
        titular = clean_article_text(resolve_column(row, ("titular", "title_clean", "title")))
        bajada = clean_article_text(resolve_column(row, ("bajada", "lead_clean", "lead", "excerpt")))
        cuerpo = clean_article_text(
            resolve_column(row, ("cuerpo", "body_clean", "body", "text")),
            bajada=bajada,
        )
        seccion = resolve_column(row, ("seccion", "section"))

        def discard(reason: str) -> None:
            stats[reason] += 1
            audit_entry = dict(row)
            audit_entry["discard_reason"] = reason
            discarded_rows.append(audit_entry)

        # 1. Deduplicación exacta por URL
        if norm_url and norm_url in seen_urls:
            discard("duplicate_url")
            continue

        # 2. Filtros de género, tema y longitud mínima (< min_words)
        reason = classify_discard_reason(
            url=raw_url,
            seccion=seccion,
            titular=titular,
            cuerpo=cuerpo,
            min_words=min_words,
        )
        if reason:
            discard(reason)
            continue

        # 3. Deduplicación exacta por hash del cuerpo limpio
        text_hash = compute_text_hash(cuerpo)
        if text_hash in seen_hashes:
            discard("duplicate_text_hash")
            continue

        # 4. Deduplicación casi exacta (cables de agencias como EFE o republicaciones)
        is_near_dup = False
        for prev_title, prev_body in kept_signatures:
            if title_similarity(titular, prev_title) >= title_sim_threshold:
                is_near_dup = True
                break
            if body_prefix_similarity(cuerpo, prev_body) >= body_sim_threshold:
                is_near_dup = True
                break

        if is_near_dup:
            discard("near_duplicate_agency_or_republish")
            continue

        # Registrar como válida
        if norm_url:
            seen_urls.add(norm_url)
        seen_hashes.add(text_hash)
        kept_signatures.append((titular, cuerpo))

        cleaned_row = dict(row)
        if "titular" in cleaned_row or "titular" in original_fieldnames:
            cleaned_row["titular"] = titular
        if "bajada" in cleaned_row or "bajada" in original_fieldnames:
            cleaned_row["bajada"] = bajada
        if "cuerpo" in cleaned_row or "cuerpo" in original_fieldnames:
            cleaned_row["cuerpo"] = cuerpo
        cleaned_row["text_hash"] = text_hash
        cleaned_row["word_count"] = str(count_words(cuerpo))
        cleaned_row["text_anonymized"] = anonymize_text(titular, bajada, cuerpo)

        kept_rows.append(cleaned_row)
        stats["kept"] += 1

    # Exportar CSV sanitizado
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    out_fields = list(original_fieldnames)
    for extra_col in ("text_hash", "word_count", "text_anonymized"):
        if extra_col not in out_fields:
            out_fields.append(extra_col)

    with output_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(kept_rows)

    # Exportar CSV de auditoría de descartes
    if audit_csv and discarded_rows:
        audit_fields = list(original_fieldnames) + ["discard_reason"]
        with audit_csv.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=audit_fields)
            writer.writeheader()
            writer.writerows(discarded_rows)

    print("=== RESUMEN DE SANITIZACIÓN ===")
    print(f"Total entrada : {len(input_rows)}")
    print(f"Conservadas   : {stats['kept']}")
    print(f"Descartadas   : {len(discarded_rows)}")
    for key, count in sorted(stats.items()):
        if key != "kept":
            print(f"  - {key}: {count}")
    print(f"Salida limpia : {output_csv}")
    if audit_csv and discarded_rows:
        print(f"Auditoría     : {audit_csv}")

    return dict(stats)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sanitiza, filtra y deduplica un CSV de noticias chilenas (Fase 0)."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_CSV, help="CSV de entrada.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_CSV, help="CSV limpio de salida.")
    parser.add_argument(
        "--audit",
        type=Path,
        default=DEFAULT_AUDIT_CSV,
        help="CSV con noticias descartadas y motivo.",
    )
    parser.add_argument(
        "--min-words",
        type=int,
        default=120,
        help="Mínimo de palabras en el cuerpo (default: 120).",
    )
    parser.add_argument(
        "--title-sim",
        type=float,
        default=0.85,
        help="Umbral de similitud de titular para near-duplicates (default: 0.85).",
    )
    parser.add_argument(
        "--body-sim",
        type=float,
        default=0.85,
        help="Umbral de similitud en inicio de cuerpo para near-duplicates (default: 0.85).",
    )
    args = parser.parse_args()

    sanitize_and_deduplicate(
        input_csv=args.input,
        output_csv=args.output,
        audit_csv=args.audit,
        min_words=args.min_words,
        title_sim_threshold=args.title_sim,
        body_sim_threshold=args.body_sim,
    )


if __name__ == "__main__":
    main()
