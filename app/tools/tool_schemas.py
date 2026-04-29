TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "lookup_customer",
            "description": "Look up a customer by name before taking further action.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Full name of the customer"
                    }
                },
                "required": ["name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "schedule_appointment",
            "description": "Schedule an appointment for a customer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Full name of the customer"
                    },
                    "date": {
                        "type": "string",
                        "description": "Requested appointment date"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for the appointment"
                    }
                },
                "required": ["name", "date", "reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_confirmation",
            "description": "Send a confirmation message after an action is completed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Full name of the customer"
                    },
                    "method": {
                        "type": "string",
                        "enum": ["sms", "email"],
                        "description": "Delivery method for the confirmation"
                    }
                },
                "required": ["name", "method"]
            }
        }
    }
]