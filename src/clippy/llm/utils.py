"""LLM utility functions."""

def _is_reasoner_model(model: str) -> bool:
    """Check if a model is a DeepSeek reasoner model that needs special handling."""
    model_lower = model.lower()
    return "reasoner" in model_lower or "deepseek-r1" in model_lower