# Notebooks de Entrenamiento y Experimentación (Kaggle / Hugging Face)

Este directorio contiene las plantillas de Jupyter Notebooks que se sincronizan con **Kaggle Notebooks (GPU T4 x2 / P100)** para el entrenamiento y evaluación de los modelos clasificadores.

## Flujo de Trabajo planeado

1. **`01_beto_finetuning_v1.ipynb` (Fase 1 - El Juez Entrenado V1)**
   - **Modelo Base:** `dccuchile/bert-base-spanish-wwm-cased` (BETO).
   - **Entrada:** `train_dataset_v1.csv` (texto anonimizado).
   - **Salida:** Pesos del clasificador publicados en Hugging Face Hub y reporte sobre `gold_standard_test.csv` (DoD: $\ge 80\%$ de coincidencia).
2. **`02_error_analysis_and_v2_retraining.ipynb` (Fase 2 - Ciclo de Aprendizaje por Errores)**
   - Análisis de matriz de confusión de la V1, incorporación de casos de baja confianza hasta 400–500 noticias y reentrenamiento del Juez V2.
3. **`03_model_benchmarks_and_ablation.ipynb` (Fase 3 - Benchmark y Ablación)**
   - Comparativa técnica entre arquitecturas abiertas (BETO vs. otros modelos Transformer/LLMs pequeños en español con QLoRA).
   - **Estudio de Ablación:** Medición cuantitativa del impacto de la anonimización (`con anonimización` vs. `sin anonimización`) sobre la generalización del modelo.
