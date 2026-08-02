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

RENT_PAID_CONFIRMATION_TEMPLATES = {
    "en": (
        "Hi {name}, we have received your rent payment of ₹{amount} on {paid_date}. "
        "Thank you!"
    ),
    "hi": ("{name} जी, ₹{amount} किराया {paid_date} को प्राप्त हुआ है। धन्यवाद!"),
    "mr": ("{name}, तुमचं ₹{amount} भाडं {paid_date} रोजी मिळालं आहे. धन्यवाद!"),
}
