from app.rag.rag import search_knowledge_base

def schedule_appointment(name: str, date: str, reason: str) -> dict:
    return {
        "status": "success",
        "message": f"Dummy appointment scheduled for {name} on {date} for {reason}."
    }


def send_confirmation(name: str, method: str) -> dict:
    return {
        "status": "success",
        "message": f"Dummy confirmation sent to {name} via {method}."
    }

def search_appointments(name: str) -> dict:
    return {
        "status": "success",
        "appointments": [
            {
                "appointment_id": "appt-demo-123",
                "name": name,
                "date": "2026-05-07",
                "reason": "financials review",
                "status": "scheduled"
            }
        ]
    }

def reschedule_appointment(appointment_id: str, new_date: str) -> dict:
    return {
        "status": "success",
        "message": f"Appointment {appointment_id} rescheduled to {new_date}."
    }


def cancel_appointment(appointment_id: str) -> dict:
    return {
        "status": "success",
        "message": f"Appointment {appointment_id} has been canceled."
    }


def create_lead(name: str, reason: str, phone: str | None = None) -> dict:
    return {
        "status": "success",
        "lead_id": "lead-demo-123",
        "message": f"Lead created for {name}: {reason}."
    }


def create_callback_request(name: str, reason: str, phone: str | None = None) -> dict:
    return {
        "status": "success",
        "callback_id": "callback-demo-123",
        "message": f"Callback request created for {name}: {reason}."
    }


def send_confirmation(name: str, method: str) -> dict:
    return {
        "status": "success",
        "message": f"Dummy confirmation sent to {name} via {method}."
    }

TOOL_MAP = {
    "schedule_appointment": schedule_appointment,
    "send_confirmation": send_confirmation,
    "search_appointments": search_appointments,
    "reschedule_appointment": reschedule_appointment,
    "cancel_appointment": cancel_appointment,
    "create_lead": create_lead,
    "create_callback_request": create_callback_request,
    "search_knowledge_base": search_knowledge_base,
}