import openai
from django.utils import timezone
from properties.models import RentRecord

def handle_chat_message(user, message):
    # Sample rule-based handler
    message = message.lower()
    if "rent due" in message:
        next_due = RentRecord.objects.filter(renter__user=user, paid=False).order_by("due_date").first()
        if next_due:
            return f"🏠 Your next rent of ₹{next_due.amount} is due on {next_due.due_date}."
        return "✅ No upcoming rent dues."
    
    if "agreement" in message:
        latest = RentRecord.objects.filter(renter__user=user).last()
        return f"📄 Here is your latest rent agreement: {latest.agreement_pdf.url}" if latest and latest.agreement_pdf else "No agreement found."

    # Fallback to OpenAI assistant
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant for RentSecure users."},
            {"role": "user", "content": message}
        ]
    )
    return response.choices[0].message["content"]