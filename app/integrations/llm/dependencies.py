from functools import lru_cache
from typing import Annotated
from fastapi import Depends

from app.integrations.llm.base import LLMProvider
from app.integrations.llm.groq import GroqProvider
from app.core.config import get_settings


@lru_cache
def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    return GroqProvider(
        api_key = settings.GROQ_API_KEY.get_secret_value(),
        model = settings.GROQ_MODEL
    )


LLMDep = Annotated[LLMProvider, Depends(get_llm_provider)]



