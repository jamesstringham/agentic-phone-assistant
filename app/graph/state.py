from typing import TypedDict, Optional, List, Dict, Any


class CallState(TypedDict, total=False):
    session_id: str
    caller_phone: str
    caller_name: str
    known_customer: bool
    customer_id: str

    intent: str
    route: str
    needs_confirmation: bool
    confirmation_type: str

    requested_service: str
    requested_consultant: str
    appointment_id: str
    appointment_date: str
    appointment_time: str
    appointment_mode: str

    user_message: str
    assistant_message: str

    rag_query: str
    rag_answer: str

    tool_results: List[Dict[str, Any]]
    memory_summary: str

    end_call: bool