import json
from collections.abc import Iterator
from app.llm.azure_chatlib import AzureChatLib
from app.prompts.system_prompt import SYSTEM_PROMPT
from app.tools.tool_schemas import TOOLS
from app.tools.dummy_tools import TOOL_MAP


class ConversationAgent:
    def __init__(self):
        self.chatlib = AzureChatLib()
        self.sessions: dict[str, list] = {}

    def _get_or_create_session(self, session_id: str) -> list:
        if session_id not in self.sessions:
            self.sessions[session_id] = [
                {"role": "system", "content": SYSTEM_PROMPT}
            ]
        return self.sessions[session_id]

    def handle_user_text(self, session_id: str, user_text: str) -> str:
        """
        Non-streaming fallback. Keeps your old behavior.
        """
        messages = self._get_or_create_session(session_id)
        messages.append({"role": "user", "content": user_text})

        max_tool_rounds = 5

        for _ in range(max_tool_rounds):
            response = self.chatlib.chat(messages=messages, tools=TOOLS)
            msg = response.choices[0].message

            if getattr(msg, "tool_calls", None):
                self._append_assistant_tool_call_message(messages, msg)
                self._execute_tool_calls(messages, msg.tool_calls)
            else:
                final_text = msg.content or "Sorry, I didn't catch that."
                messages.append({"role": "assistant", "content": final_text})
                return final_text

        fallback = "I completed the requested actions, but had trouble forming the final response."
        messages.append({"role": "assistant", "content": fallback})
        return fallback

    def stream_user_text(self, session_id: str, user_text: str):
        messages = self._get_or_create_session(session_id)
        messages.append({"role": "user", "content": user_text})

        max_tool_rounds = 5

        for _ in range(max_tool_rounds):
            if not hasattr(self.chatlib, "stream_chat"):
                final_text = self.handle_user_text_without_readding_user(messages)
                yield final_text
                return

            stream_state = {
                "content_parts": [],
                "tool_calls": {},
            }

            for event in self.chatlib.stream_chat(messages=messages, tools=TOOLS):
                event_type = event.get("type")

                if event_type == "content_delta":
                    delta = event.get("delta", "")
                    if delta:
                        stream_state["content_parts"].append(delta)

                elif event_type == "tool_call_delta":
                    index = event["index"]
                    if index not in stream_state["tool_calls"]:
                        stream_state["tool_calls"][index] = {
                            "id": event.get("id"),
                            "type": "function",
                            "function": {
                                "name": event.get("name", ""),
                                "arguments": "",
                            },
                        }

                    tc = stream_state["tool_calls"][index]
                    if event.get("id"):
                        tc["id"] = event["id"]
                    if event.get("name"):
                        tc["function"]["name"] = event["name"]
                    if event.get("arguments_delta"):
                        tc["function"]["arguments"] += event["arguments_delta"]

                elif event_type == "message_stop":
                    break

            final_text = "".join(stream_state["content_parts"]).strip()
            tool_calls = [
                stream_state["tool_calls"][idx]
                for idx in sorted(stream_state["tool_calls"].keys())
            ]

            if tool_calls:
                self._append_streamed_tool_call_message(messages, final_text, tool_calls)
                self._execute_streamed_tool_calls(messages, tool_calls)
                continue

            if final_text:
                messages.append({"role": "assistant", "content": final_text})
                yield final_text
                return

            fallback = "Sorry, I didn't catch that."
            messages.append({"role": "assistant", "content": fallback})
            yield fallback
            return

        fallback = "I completed the requested actions, but had trouble forming the final response."
        messages.append({"role": "assistant", "content": fallback})
        yield fallback

    def handle_user_text_without_readding_user(self, messages: list) -> str:
        """
        Internal helper for stream_user_text fallback mode.
        Assumes the user message is already in messages.
        """
        max_tool_rounds = 5

        for _ in range(max_tool_rounds):
            response = self.chatlib.chat(messages=messages, tools=TOOLS)
            msg = response.choices[0].message

            if getattr(msg, "tool_calls", None):
                self._append_assistant_tool_call_message(messages, msg)
                self._execute_tool_calls(messages, msg.tool_calls)
            else:
                final_text = msg.content or "Sorry, I didn't catch that."
                messages.append({"role": "assistant", "content": final_text})
                return final_text

        fallback = "I completed the requested actions, but had trouble forming the final response."
        messages.append({"role": "assistant", "content": fallback})
        return fallback

    def _append_assistant_tool_call_message(self, messages: list, msg) -> None:
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

    def _execute_tool_calls(self, messages: list, tool_calls) -> None:
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            raw_args = tool_call.function.arguments or "{}"
            parsed_args = json.loads(raw_args)
            print(f"[TOOL CALL] {tool_name}({parsed_args})")

            if tool_name not in TOOL_MAP:
                tool_result = {
                    "status": "error",
                    "message": f"Unknown tool: {tool_name}"
                }
            else:
                tool_result = TOOL_MAP[tool_name](**parsed_args)
                print(f"[TOOL RESULT] {tool_result}")

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(tool_result)
            })

    def _append_streamed_tool_call_message(self, messages: list, content: str, tool_calls: list[dict]) -> None:
        messages.append({
            "role": "assistant",
            "content": content,
            "tool_calls": tool_calls,
        })

    def _execute_streamed_tool_calls(self, messages: list, tool_calls: list[dict]) -> None:
        for tool_call in tool_calls:
            tool_name = tool_call["function"]["name"]
            raw_args = tool_call["function"]["arguments"] or "{}"
            parsed_args = json.loads(raw_args)
            print(f"[TOOL CALL] {tool_name}({parsed_args})")

            if tool_name not in TOOL_MAP:
                tool_result = {
                    "status": "error",
                    "message": f"Unknown tool: {tool_name}"
                }
            else:
                tool_result = TOOL_MAP[tool_name](**parsed_args)
                print(f"[TOOL RESULT] {tool_result}")

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "content": json.dumps(tool_result)
            })