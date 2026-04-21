import openai
from django.conf import settings
from datetime import date

openai.api_key = settings.OPENAI_API_KEY

def gpt_smart_reply(user, user_query, context_data):
    # prompt = f"""
    # You are a smart assistant for a rent management system. Based on the following data, answer the user's question smartly.

    # User Data:
    # {context_data}

    # User's Question: "{user_query}"

    # Respond in Hindi or English based on user tone, keep response short and clear.
    # """

    prompt = f"""
    You're RentSecure's SmartBot, a financial assistant for property owners.

    User: {user.username}
    Current Date: {date.today()}

    Context:
    {context_data}

    User's Question: {user_query}

    Respond naturally. If it's a financial question, be precise. Use memory from chat history when possible.
    """

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant for rent management."},
            {"role": "user", "content": prompt}
        ]
    )

    return response['choices'][0]['message']['content']