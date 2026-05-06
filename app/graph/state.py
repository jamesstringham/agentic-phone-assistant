from typing import TypedDict, Optional, List, Dict, Any


class CallState(TypedDict, total=False):
    # Call/session metadata
    session_id: str
    caller_phone: str

    # Routing
    route: str

    # Core conversation fields
    user_message: str
    assistant_message: str

    # Caller/task details
    caller_name: str
    requested_service: str
    phone: str

    # Appointment details
    appointment_id: str
    appointment_date: str

    # Confirmation flow
    needs_confirmation: bool
    confirmation_type: str

    # Conversation control
    end_call: bool