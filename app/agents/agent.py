import json
from typing import Any, Callable

from app.llm.azure_chatlib import AzureChatLib


ToolFn = Callable[..., dict[str, Any]]


class SpecialistAgent:
    def __init__(
        self,
        *,
        name: str,
        system_prompt: str,
        tools_schema: list[dict] | None = None,
        tool_map: dict[str, ToolFn] | None = None,
    ):
        self.name = name
        self.system_prompt = system_prompt
        self.tools_schema = tools_schema or []
        self.tool_map = tool_map or {}
        self.chatlib = AzureChatLib()

    def _build_messages(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        state_view = {
            "session_id": state.get("session_id"),
            "caller_phone": state.get("caller_phone"),
            "caller_name": state.get("caller_name"),
            "known_customer": state.get("known_customer"),
            "intent": state.get("intent"),
            "route": state.get("route"),
            "requested_service": state.get("requested_service"),
            "requested_consultant": state.get("requested_consultant"),
            "appointment_id": state.get("appointment_id"),
            "appointment_date": state.get("appointment_date"),
            "appointment_time": state.get("appointment_time"),
            "appointment_mode": state.get("appointment_mode"),
            "confirmation_type": state.get("confirmation_type"),
            "memory_summary": state.get("memory_summary"),
        }

        user_message = state.get("user_message", "")

        return [
            {"role": "system", "content": self.system_prompt},
            {
                "role": "user",
                "content": (
                    "Current call state:\n"
                    f"{json.dumps(state_view, ensure_ascii=False)}\n\n"
                    "Latest caller message:\n"
                    f"{user_message}\n\n"
                    "Return a concise phone-friendly reply and update any relevant fields."
                ),
            },
        ]

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        messages = self._build_messages(state)
        max_tool_rounds = 5

        for _ in range(max_tool_rounds):
            response = self.chatlib.chat(
                messages=messages,
                tools=self.tools_schema if self.tools_schema else None,
            )
            msg = response.choices[0].message

            if getattr(msg, "tool_calls", None):
                messages.append({
                    "role": "assistant",
                    "content": msg.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": tc.type,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in msg.tool_calls
                    ]
                })

                for tool_call in msg.tool_calls:
                    tool_name = tool_call.function.name
                    raw_args = tool_call.function.arguments or "{}"

                    try:
                        parsed_args = json.loads(raw_args)
                    except json.JSONDecodeError:
                        parsed_args = {}

                    print(f"[{self.name.upper()} TOOL CALL] {tool_name}({parsed_args})")

                    if tool_name not in self.tool_map:
                        tool_result = {
                            "status": "error",
                            "message": f"Unknown tool: {tool_name}"
                        }
                    else:
                        try:
                            tool_result = self.tool_map[tool_name](**parsed_args)
                        except Exception as e:
                            tool_result = {
                                "status": "error",
                                "message": f"Tool execution failed: {str(e)}"
                            }

                    print(f"[{self.name.upper()} TOOL RESULT] {tool_result}")

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(tool_result),
                    })

                continue

            content = (msg.content or "").strip()
            return self._parse_final_output(content, state)

        return {
            "assistant_message": "I'm sorry, I'm having trouble completing that right now.",
            "needs_confirmation": False,
        }

    def _parse_final_output(self, content: str, state: dict[str, Any]) -> dict[str, Any]:
        """
        Expect strict JSON from the specialist. Fall back safely if parsing fails.
        """
        try:
            data = json.loads(content)
            if not isinstance(data, dict):
                raise ValueError("Final output was not a dict")
        except Exception:
            return {
                "assistant_message": content or "I'm sorry, could you repeat that?",
                "needs_confirmation": False,
            }

        result: dict[str, Any] = {}

        allowed_fields = [
            "assistant_message",
            "caller_name",
            "intent",
            "route",
            "requested_service",
            "requested_consultant",
            "appointment_id",
            "appointment_date",
            "appointment_time",
            "appointment_mode",
            "confirmation_type",
            "needs_confirmation",
            "end_call",
        ]

        for field in allowed_fields:
            if field in data and data[field] is not None:
                result[field] = data[field]

        if "assistant_message" not in result:
            result["assistant_message"] = "I'm sorry, could you repeat that?"

        if "needs_confirmation" not in result:
            result["needs_confirmation"] = False

        return result