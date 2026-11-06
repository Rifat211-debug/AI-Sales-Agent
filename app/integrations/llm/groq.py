import logging
import json

from groq import AsyncGroq, APIError

from app.core.exceptions.errors import LLMUnavailableError
from app.integrations.llm.base import ChatMessage, LLMReply, ToolRunner, ToolSpec


ROLES = {"user": "user", "assistant": "assistant"}

MAX_TOOL_ROUNDS = 5

logger = logging.getLogger("uvicorn.error")


def to_contents(messages: list[ChatMessage]) -> list[dict[str, str]]:
    return [
        {
            "role": m.role,
            "content": m.content
        }
        for m in messages
    ]


def to_groq_tools(tools: list[ToolSpec]) -> list[dict]:
    return [
        {
            "name": "function",
            "function": {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters
            }
        }
        for t in tools
    ]


def describe_call(name: str, args: dict) -> str:
    return f"{name}({', '.join(f"{k} = {v!r}" for k, v in args.items())})"
    

class GroqProvider:
    def __init__(self, api_key: str, model: str) -> None:
        self.client = AsyncGroq(api_key = api_key)
        self.model = model

    async def chat(self, system: str, messages: list[ChatMessage]) -> str:
        contents = [
            {
                "role": ROLES[m.role],
                "content": m.content
            }
            for m in messages
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
            raise LLMUnavailableError(str(exc)) from exc

        return response.choices[0].message.content or ""     


    async def chat_with_tools(
    self,
    system: str,
    messages: list[ChatMessage],
    tools: list[ToolSpec],
    run_tool: ToolRunner,
) -> LLMReply:
        contents = to_contents(messages)
        groq_tools = to_groq_tools(tools)
        tool_calls: list[str] = []

        for round_no in range(1, MAX_TOOL_ROUNDS + 1):
            try:
                response = await self.client.chat.completions.create(
                    model = self.model,
                    messages = [
                       {"role": "system", "content": system},
                       *contents,
                  ],
                tools = groq_tools,
                tool_choice = "auto",
            )

            except APIError as exc:
                raise LLMUnavailableError(str(exc)) from exc

            message = response.choices[0].message
            calls = message.tool_calls or []

            if not calls:
                logger.info("[round %s] model answered with text", round_no)

                return LLMReply(
                    text = message.content or "",
                    tool_calls = tool_calls,
                )

            contents.append({
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {
                            "name": call.function.name,
                            "arguments": call.function.arguments,
                        },
                    }
                    for call in calls
                ],
            })

       
            for call in calls:
                name = call.function.name
                args = json.loads(call.function.arguments)

                tool_calls.append(describe_call(name, args))

                logger.info(
                    "[round %s] model asked for %s",
                    round_no,
                    tool_calls[-1],
                )

                result = await run_tool(name, args)

                contents.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(result, default = str),
                })

        return LLMReply(
            text = "Sorry, I couldn't finish that. Please ask in a simpler way.",
            tool_calls = tool_calls,
        )