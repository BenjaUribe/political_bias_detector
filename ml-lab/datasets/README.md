# Datasets del Laboratorio ML (Fase 0 - Fase 3)

Este directorio almacena localmente los conjuntos de datos de entrenamiento y validación (los archivos `.csv` reales están ignorados en `.gitignore` para evitar subir datos crudos o pesados por error antes de su anonimización y publicación en Fase 3).

## Archivos Esperados

1. **`raw_scraped_articles.jsonl`** *(Fase 0)*
   - Salida cruda del recolector manual desde los 5–8 medios chilenos seleccionados.
2. **`annotations_annotator_a.csv` y `annotations_annotator_b.csv`** *(Fase 0)*
   - Etiquetas independientes para validar el índice Kappa de Cohen ($\kappa \ge 0.75$).
3. **`train_dataset_v1.csv`** *(Fase 0 -> Fase 1)*
   - 150 a 200 noticias informativas limpias, anonimizadas y etiquetadas con consenso para el primer *fine-tuning* de BETO.
4. **`gold_standard_test.csv`** *(Fase 0 - Intocable)*
   - 30 noticias reservadas exclusivamente para evaluar precisión real en todas las fases (meta Fase 1: $\ge 80\%$). Nunca debe usarse para entrenamiento.
5. **`train_dataset_v2.csv`** *(Fase 2)*
   - Expansión a 400–500 noticias incorporando casos difíciles detectados en el análisis de errores de la V1.

## Esquema de Columnas Sugerido (`CSV`)

| Columna | Tipo | Descripción |
| :--- | :--- | :--- |
| `article_id` | `str` | Identificador único (hash o UUID) |
| `source_domain` | `str` | Medio de origen (solo para auditoría de balance; se oculta al modelo) |
| `title_clean` | `str` | Titular limpio |
| `lead_clean` | `str` | Bajada o entradilla limpia |
| `body_clean` | `str` | Cuerpo de la noticia limpio |
| `text_anonymized` | `str` | Texto completo tras pasar por el Anonimizador (`[POLITICO_1]`, `[PARTIDO_A]`, `[MEDIO]`) |
| `label` | `str` | Etiqueta consensuada (`LEFT`, `CENTER`, `RIGHT`) |
| `annotator_agreement` | `bool` | Si hubo acuerdo directo o requirió resolución de consenso |
