from groq import AsyncGroq, APIError

from app.core.exceptions.errors import LLMUavailableError
from app.integrations.llm.base import ChatMessage


ROLES = {"user": "user", "assistant": "assistant"}


class GroqProvider:
    def __init__(self, api_key: str, model: str) -> None:
        self.client = AsyncGroq(api_key = api_key)
        self.model = model

    async def chat(self, system: str, message: list[ChatMessage]) -> str:
        contents = [
            {
                "role": ROLES[m.role],
                "content": m.content
            }
            for m in message
        ] 

        try:
            response = await self.client.chat.completions.create(
                model = self.model,
                messages = [
                    {"role": "system", "content": system},
                    *contents
                ]
            ) 
        except APIError as exc:
            raise LLMUavailableError(str(exc)) from exc

        return response.choices[0].message.content or ""                                    