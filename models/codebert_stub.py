"""
Minimal wrapper that lazily loads CodeBERT tokenizer and model via HuggingFace.
This is a non-blocking stub: it only loads the model when predict() is called.
"""
from typing import Optional

_tokenizer = None
_model = None


def _ensure_loaded():
    global _tokenizer, _model
    if _tokenizer is None or _model is None:
        try:
            from transformers import AutoTokenizer, AutoModel
            _tokenizer = AutoTokenizer.from_pretrained("microsoft/codebert-base")
            _model = AutoModel.from_pretrained("microsoft/codebert-base")
        except Exception as e:
            raise RuntimeError(f"Failed to load CodeBERT: {e}")


def predict(code: str) -> dict:
    """Return a dummy prediction dict or run a forward pass when model is available.

    Returns:
      { 'label': 'unknown'|'buggy'|'clean', 'score': float }
    """
    try:
        _ensure_loaded()
    except RuntimeError as e:
        return {"label": "unknown", "score": 0.0, "error": str(e)}

    inputs = _tokenizer(code, return_tensors="pt", truncation=True, max_length=512)
    outputs = _model(**inputs)
    # Without a classifier head, we'll return a placeholder using embedding norms
    emb = outputs.last_hidden_state.mean(dim=1).detach()
    score = float(emb.norm().item())
    return {"label": "unknown", "score": score}
