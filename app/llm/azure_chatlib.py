from openai import AzureOpenAI
from app.config import settings


class AzureChatLib:
    def __init__(self):
        if not settings.azure_openai_endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT is not set")
        if not settings.azure_openai_api_key:
            raise ValueError("AZURE_OPENAI_API_KEY is not set")
        if not settings.azure_openai_deployment:
            raise ValueError("AZURE_OPENAI_DEPLOYMENT is not set")

        self.client = AzureOpenAI(
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            azure_endpoint=settings.azure_openai_endpoint,
        )
        self.deployment = settings.azure_openai_deployment

    def chat(self, messages: list, tools: list | None = None):
        kwargs = {
            "model": self.deployment,
            "messages": messages,
        }

        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        return self.client.chat.completions.create(**kwargs)

    def stream_chat(self, messages: list, tools: list | None = None):
        """
        Streams chat completion deltas and normalizes them into small dict events.

        Yields event dicts like:
            {"type": "content_delta", "delta": "..."}
            {
                "type": "tool_call_delta",
                "index": 0,
                "id": "call_xxx",
                "name": "lookup_customer",
                "arguments_delta": "{\"name\":\"James\""
            }
            {"type": "message_stop"}
        """
        kwargs = {
            "model": self.deployment,
            "messages": messages,
            "stream": True,
        }

        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        stream = self.client.chat.completions.create(**kwargs)

        for chunk in stream:
            if not chunk.choices:
                continue

            choice = chunk.choices[0]
            delta = getattr(choice, "delta", None)
            if delta is None:
                finish_reason = getattr(choice, "finish_reason", None)
                if finish_reason is not None:
                    yield {"type": "message_stop"}
                    break
                continue

            # Regular assistant text deltas
            content = getattr(delta, "content", None)
            if content:
                yield {
                    "type": "content_delta",
                    "delta": content,
                }

            # Tool / function call deltas
            tool_calls = getattr(delta, "tool_calls", None)
            if tool_calls:
                for tc in tool_calls:
                    function = getattr(tc, "function", None)
                    yield {
                        "type": "tool_call_delta",
                        "index": getattr(tc, "index", 0),
                        "id": getattr(tc, "id", None),
                        "name": getattr(function, "name", None) if function else None,
                        "arguments_delta": getattr(function, "arguments", None) if function else "",
                    }

            finish_reason = getattr(choice, "finish_reason", None)
            if finish_reason is not None:
                yield {"type": "message_stop"}
                break