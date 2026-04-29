import json
from typing import TypedDict, Optional

from app.llm.azure_chatlib import AzureChatLib
from app.prompts.agent_prompts import ROUTER_SYSTEM_PROMPT


class RouterDecision(TypedDict):
    route: str
    caller_name: Optional[str]
    requested_service: Optional[str]
    appointment_date: Optional[str]
    appointment_time: Optional[str]


class RouterAgent:
    def __init__(self):
        self.chatlib = AzureChatLib()

    def route(self, user_message: str, state: dict | None = None) -> RouterDecision:
        state = state or {}

        state_view = {
            "current_route": state.get("route"),
            "caller_name": state.get("caller_name"),
            "requested_service": state.get("requested_service"),
            "appointment_date": state.get("appointment_date"),
            "appointment_time": state.get("appointment_time"),
            "assistant_message": state.get("assistant_message"),
        }

        messages = [
            {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Current call state:\n"
                    f"{json.dumps(state_view)}\n\n"
                    "Latest caller message:\n"
                    f"{user_message}"
                ),
            },
        ]

        response = self.chatlib.chat(messages=messages, tools=None)
        content = response.choices[0].message.content or ""

        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            data = {
                "route": state.get("route") or "business_info",
                "caller_name": None,
                "requested_service": None,
                "appointment_date": None,
                "appointment_time": None,
            }

        route = data.get("route") or state.get("route") or "business_info"
        if route not in {"business_info", "schedule", "modify", "cancel", "lead", "escalate"}:
            route = state.get("route") or "business_info"

        return {
            "route": route,
            "caller_name": data.get("caller_name"),
            "requested_service": data.get("requested_service"),
            "appointment_date": data.get("appointment_date"),
            "appointment_time": data.get("appointment_time"),
        }