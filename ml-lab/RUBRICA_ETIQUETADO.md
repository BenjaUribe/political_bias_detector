# Rúbrica Oficial de Etiquetado de Encuadre Discursivo (Fase 0)

> **Propósito:** Definir criterios objetivos y reproducibles para etiquetar noticias informativas de prensa chilena en tres categorías de encuadre (*framing*): `IZQUIERDA`, `CENTRO` o `DERECHA`.
> **Meta de Consenso (DoD Fase 0):** Índice Kappa de Cohen $\kappa \ge 0.75$ entre anotadores sobre muestra cruzada antes de construir `train_dataset_v1.csv` (200 noticias) y `gold_standard_test.csv` (30 noticias).

---

## 1. Criterios de Elegibilidad de Noticias (Filtro de Entrada)

- [ ] **Solo género informativo:** Crónicas, reportajes informativos y notas del día de los 5–8 medios chilenos seleccionados (*El Mercurio, La Tercera, BioBioChile, El Mostrador, CIPER, El Desconcierto*, etc.).
- [ ] **Exclusión estricta:** Descartar columnas de opinión, editoriales, cartas al director y entrevistas de pregunta-respuesta pura.
- [ ] **Pre-anonimización mental/técnica:** El etiquetado debe juzgar **cómo está escrita y estructurada la noticia** (encuadre, selección de fuentes y adjetivación), nunca qué medio la publicó ni qué político aparece.

---

## 2. Dimensiones de Evaluación por Noticia

TODO: Completar definiciones operativas y ejemplos reales durante las sesiones de calibración de la Fase 0.

### Dimensión A: Encuadre del Titular y Bajada (*Headline Framing*)
- ¿Qué actor o consecuencia protagoniza la oración activa?
- ¿Qué marco conceptual predomina (ej. *derechos sociales / desigualdad / rol garante del Estado* vs. *crecimiento económico / seguridad / orden público / eficiencia fiscal*)?

### Dimensión B: Selección y Jerarquía de Fuentes (*Source Balance*)
- ¿A qué sector político o gremial pertenecen las fuentes citadas directamente entre comillas (`"..."`)?
- ¿Qué actor abre y qué actor cierra la nota? ¿Se otorga derecho a réplica equivalente?

### Dimensión C: Carga Léxica y Adjetivación (*Lexical Framing*)
- Uso de verbos de atribución neutros (*"señaló", "informó"*) vs. verbos o adjetivos valorativos (*"admitió", "acusó", "polémico", "controvertido"*).
- Uso de cifras o afirmaciones sin fuente atribuida (*"expertos advierten..."*).

---

## 3. Definición de Etiquetas (`LABEL`)

| Etiqueta | Código | Criterio de Asignación (Template) | Ejemplos de Prensa Chilena (TODO) |
| :--- | :---: | :--- | :--- |
| **Izquierda** | `0` / `LEFT` | TODO: Definir umbral de predominio de marcos y fuentes asociados a sectores progresistas / izquierda. | *Agregar 2-3 ejemplos reales anonimizados* |
| **Centro / Neutro** | `1` / `CENTER` | TODO: Definir criterio de equilibrio de fuentes contrapuestas y lenguaje estrictamente descriptivo sin carga adjetiva. | *Agregar 2-3 ejemplos reales anonimizados* |
| **Derecha** | `2` / `RIGHT` | TODO: Definir umbral de predominio de marcos y fuentes asociados a sectores conservadores / liberal-económicos / derecha. | *Agregar 2-3 ejemplos reales anonimizados* |

---

## 4. Protocolo de Resolución de Discrepancias

1. Etiquetado ciego e independiente por cada integrante sobre lotes de $N$ noticias.
2. Ejecución de `ml-lab/scripts/cohen_kappa_eval.py` para medir acuerdo inter-anotador.
3. Revisión conjunta de casos discordantes y refinamiento de esta rúbrica antes de consolidar el *Gold Standard* (30 noticias intocables).
