"""
TEMPLATE: Actor 4 — El "Juez Entrenado" (Clasificador Especializado BETO)
Ubicación: backend/app/services/judge_classifier.py

Propósito:
    Cargar el modelo Transformer entrenado por el equipo con noticias chilenas
    (`dccuchile/bert-base-spanish-wwm-cased` ajustado mediante fine-tuning),
    evaluar exclusivamente el **texto anonimizado** y emitir un veredicto
    probabilístico en porcentajes (`Izquierda % / Centro % / Derecha %`).
    No redacta explicaciones; solo calcula la inclinación discursiva con rigor matemático.

Tecnologías (`stack_tecnologico.md`):
    - `transformers` (`AutoTokenizer`, `AutoModelForSequenceClassification`) + `torch`.
    - Pesos alojados en Hugging Face Hub (entrenados en Kaggle Notebooks).
"""


class TrainedJudgeService:
    """
    TODO (Fase 1):
    Cargar tokenizer y pesos del modelo BETO V1 (y V2 en Fase 2) al iniciar el backend.
    """

    def load_model(self, model_id_or_path: str):
        """
        TODO (Fase 1):
        Inicializar modelo desde Hugging Face Hub o caché local en modo evaluación (`model.eval()`).
        """
        raise NotImplementedError("Pendiente de implementar en Fase 1.")

    def predict_framing_probabilities(self, anonymized_text: str):
        """
        TODO (Fase 1):
        1. Tokenizar `anonymized_text` con truncamiento/sliding window si supera 512 tokens.
        2. Ejecutar inferencia sin gradientes (`torch.no_grad()`).
        3. Aplicar `softmax` a los logits para obtener `Izquierda % / Centro % / Derecha %`.
        4. Retornar `BiasProbabilitiesSchema`.
        """
        raise NotImplementedError("Pendiente de implementar en Fase 1.")
