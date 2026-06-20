def extract_intent(user_query: str) -> str | None:
    if "reminder" in user_query and "rent" in user_query:
        return "send_rent_reminder"
    elif "retry" in user_query and "payout" in user_query:
        return "retry_payout"
    elif "send" in user_query and "agreement" in user_query:
        return "send_rent_agreement"
    elif "signature" in user_query or "esign" in user_query:
        return "send_agreement_for_signature"
    return None
