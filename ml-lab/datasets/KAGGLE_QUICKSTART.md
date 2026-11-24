# Guía Rápida: Subir el Dataset Starter y Probarlo en Kaggle

> **Nota importante:** `sample_kaggle_starter.csv` es un **dataset sintético de práctica** (18 ejemplos balanceados: 6 `LEFT`, 6 `CENTER`, 6 `RIGHT`). Sirve exclusivamente para aprender a usar Kaggle Datasets, configurar la GPU y probar el código del notebook antes de tener el dataset real de la Fase 0 (`train_dataset_v1.csv`).

---

## Paso 1: Subir el CSV como Dataset Privado en Kaggle

1. Entra a [kaggle.com/datasets](https://www.kaggle.com/datasets) e inicia sesión.
2. Haz clic en **New Dataset** (o **+ Create** $\rightarrow$ **Dataset**).
3. Arrastra el archivo `ml-lab/datasets/sample_kaggle_starter.csv`.
4. Ponle un título, por ejemplo: `chilean-news-bias-starter`.
5. Déjalo en **Private** (Recomendado) y haz clic en **Create**.

---

## Paso 2: Crear un Notebook y Conectar la GPU

1. Ve a **Code** $\rightarrow$ **New Notebook** (o importa `ml-lab/notebooks/01_beto_finetuning_v1.ipynb`).
2. En el panel derecho (**Session Options**):
   - **Accelerator:** Elige **GPU T4 x2** o **GPU P100** (necesitas verificar tu número de teléfono en Kaggle la primera vez para habilitar GPUs).
   - **Internet:** Actívalo (**On**) para poder descargar `dccuchile/bert-base-spanish-wwm-cased` desde Hugging Face.
3. En el panel derecho (**Input** $\rightarrow$ **Add Input**), busca tu dataset `chilean-news-bias-starter` y agrégalo.

---

## Paso 3: Código de Prueba Rápida en la Primera Celda

Copia y pega este snippet en una celda de tu Notebook en Kaggle para verificar que lee el CSV y que la GPU está activa:

```python
import pandas as pd
import torch

print("GPU disponible:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("Dispositivo:", torch.cuda.get_device_name(0))

# Nota: Reemplaza <tu-dataset-slug> por el nombre de tu dataset en /kaggle/input/
df = pd.read_csv("/kaggle/input/chilean-news-bias-starter/sample_kaggle_starter.csv")

print("Filas y columnas:", df.shape)
print("\nDistribución de etiquetas:")
print(df["label"].value_counts())

df[["article_id", "label", "label_id", "text_anonymized"]].head(3)
```

---

## Siguiente Paso en el Proyecto
Una vez que te sientas cómodo cargando el CSV, tokenizando con `AutoTokenizer.from_pretrained("dccuchile/bert-base-spanish-wwm-cased")` y corriendo una prueba de entrenamiento en Kaggle, el siguiente hito real es completar la **Fase 0** (rúbrica y recolección de las 200 noticias reales + 30 del *Gold Standard*).
