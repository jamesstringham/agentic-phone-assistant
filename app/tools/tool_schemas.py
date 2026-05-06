TOOLS = [
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
    },
    {
        "type": "function",
        "function": {
            "name": "search_appointments",
            "description": "Search for existing appointments for a caller by name.",
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
            "name": "reschedule_appointment",
            "description": "Reschedule an existing appointment to a new date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "appointment_id": {
                        "type": "string",
                        "description": "The ID of the appointment to reschedule"
                    },
                    "new_date": {
                        "type": "string",
                        "description": "The new requested appointment date"
                    }
                },
                "required": ["appointment_id", "new_date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_appointment",
            "description": "Cancel an existing appointment.",
            "parameters": {
                "type": "object",
                "properties": {
                    "appointment_id": {
                        "type": "string",
                        "description": "The ID of the appointment to cancel"
                    }
                },
                "required": ["appointment_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_lead",
            "description": "Create a new prospective client lead.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Full name of the prospective client"
                    },
                    "reason": {
                        "type": "string",
                        "description": "What the prospective client is interested in or needs help with"
                    },
                    "phone": {
                        "type": "string",
                        "description": "Optional phone number for the prospective client"
                    }
                },
                "required": ["name", "reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_callback_request",
            "description": "Create a callback request for a staff member to follow up with the caller.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Full name of the caller"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason the caller wants a callback"
                    },
                    "phone": {
                        "type": "string",
                        "description": "Optional phone number for callback"
                    }
                },
                "required": ["name", "reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Search Stringham Consulting Services internal business information, including services, office hours, address, staff, appointment policies, onboarding, pricing, and FAQs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The caller's question or the business information to search for"
                    }
                },
                "required": ["query"]
            }
        }
    }
]