# Detector de Sesgo Político y Asistente de Lectura Crítica (Prensa Chilena)

> **Estado del Proyecto:** Fase 0 — Cimientos, Rúbrica y Dataset Chileno (Plantilla de Arquitectura Inicial)

Asistente de lectura crítica para noticias informativas de medios chilenos. Combina un clasificador especializado (**BETO** ajustado con *fine-tuning* local sobre español de Chile), un módulo de **análisis estructural determinista** (`spaCy` + Regex) y un **explicador generativo multimodal** (`google-genai` / Gemini Flash) con anonimización previa obligatoria de entidades políticas.

---

## Arquitectura de Componentes

1. **Recolector de Entrada (Ingesta):** Extrae titular, bajada y cuerpo desde URLs (`trafilatura`), texto plano o capturas de pantalla móviles (OCR vía Gemini Flash).
2. **Anonimizador (Filtro de Neutralidad):** Oculta políticos, partidos, coaliciones y medios (`[POLITICO_A]`, `[PARTIDO_B]`, `[MEDIO]`) usando `spaCy` (`es_core_news_lg`) + diccionario local antes de clasificar.
3. **Contador Objetivo (Analizador Estructural):** Contabiliza citas directas entre comillas vs. paráfrasis por actor, proporción de adjetivos calificativos y cifras/afirmaciones sin fuente atribuida.
4. **Juez Entrenado (Clasificador BETO):** Calcula la distribución probabilística de encuadre (`Izquierda % / Centro % / Derecha %`) sobre el texto anonimizado.
5. **Memoria de Contexto:** Base de conocimiento local (`chile_political_context.json`) con siglas, coaliciones, cargos y marcos léxicos chilenos.
6. **Analista Crítico (Explicador Generativo):** Genera el reporte estructurado (`Pydantic`) con citas textuales que justifican la tendencia detectada y puntos de vista omitidos.
7. **Orquestador:** Coordina el flujo completo en el backend (`FastAPI`) para análisis individual (`/analyze`) y contraste multi-noticia (`/compare`).

---

## Estructura del Repositorio

```text
political_bias_detector/
├── backend/                  # API REST (FastAPI + Python 3.11+)
│   ├── app/
│   │   ├── api/              # Rutas (/analyze, /compare, /health)
│   │   ├── core/             # Configuración y variables de entorno (.env)
│   │   ├── schemas/          # Contratos JSON con Pydantic
│   │   ├── services/         # Orquestador, Scraper, Anonimizador, Contador, Juez BETO, Analista LLM
│   │   └── main.py           # Punto de entrada FastAPI
│   ├── data/                 # Diccionario político chileno y memoria de contexto (JSON)
│   └── requirements.txt
│
├── frontend/                 # Interfaz Web (React + TypeScript + Tailwind CSS)
│   ├── src/
│   │   ├── components/       # Gráficos de barras, tarjetas de citas, visor comparativo
│   │   ├── services/         # Cliente HTTP hacia FastAPI
│   │   ├── types/            # Interfaces TypeScript alineadas con los schemas del backend
│   │   └── App.tsx
│   └── package.json
│
├── ml-lab/                   # Entrenamiento y Experimentación (Sincronizado con Kaggle / HF)
│   ├── datasets/             # Espacio local para datasets limpios y Gold Standard
│   ├── notebooks/            # Notebooks de fine-tuning de BETO y benchmarks
│   ├── scripts/              # Scripts locales de scraping manual, limpieza y Kappa de Cohen
│   └── RUBRICA_ETIQUETADO.md # Criterios oficiales de anotación (Fase 0)
│
├── .gitignore
└── README.md
```

---

## Roadmap por Fases y Criterios de Salida (DoD)

- [ ] **Fase 0: Cimientos y Datos** — Rúbrica operativa, acuerdo inter-anotador ($\kappa \ge 0.75$), `train_dataset_v1.csv` (200 noticias) y `gold_standard_test.csv` (30 noticias).
- [ ] **Fase 1: Núcleo de Validación (MVP)** — Flujo E2E con URL/texto, Anonimizador NER, Juez BETO V1 ($\ge 80\%$ precisión en Gold Standard) y Analista Crítico V1.
- [ ] **Fase 2: Rigor Analítico y Visión (V2)** — OCR multimodal para capturas móviles, Contador Estructural Determinista, Memoria de Contexto Chileno y dataset ampliado (500 noticias).
- [ ] **Fase 3: Contraste y Portafolio (V3)** — Comparador Lado a Lado multi-medio, benchmark de arquitecturas y publicación abierta (Model Card en Hugging Face).
