"""Message templates for WhatsApp notifications."""

RENT_REMINDER_TEMPLATES = {
    "en": (
        "Dear {name}, your rent of ₹{amount} is due on {due_date}. "
        "Please pay promptly."
    ),
    "hi": (
        "{name} जी, आपका ₹{amount} किराया {due_date} को देना है। "
        "कृपया समय पर भुगतान करें।"
    ),
    "mr": (
        "{name}, तुमचं ₹{amount} भाडं {due_date} रोजी भरायचं आहे. "
        "कृपया वेळेत भरणा करा."
    ),
}

TAX_REMINDER_TEMPLATES = {
    "en": (
        "Dear {name}, your property tax of ₹{amount} is due on {due_date}. "
        "Please pay promptly."
    ),
    "hi": (
        "{name} जी, आपकी प्रॉपर्टी टैक्स ₹{amount} {due_date} को देना है। "
        "कृपया समय पर भुगतान करें।"
    ),
    "mr": (
        "{name}, तुमची प्रॉपर्टी टैक्स ₹{amount} {due_date} रोजी भरायची आहे. "
        "कृपया वेळेत भरणा करा."
    ),
}
