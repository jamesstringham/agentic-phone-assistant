def lookup_customer(name: str) -> dict:
    return {
        "status": "success",
        "customer": {
            "name": name,
            "account_id": "demo-123",
            "dob": "01/01/1995"
        }
    }


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


TOOL_MAP = {
    "lookup_customer": lookup_customer,
    "schedule_appointment": schedule_appointment,
    "send_confirmation": send_confirmation,
}