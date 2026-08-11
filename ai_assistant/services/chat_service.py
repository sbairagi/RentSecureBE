from __future__ import annotations

import logging
from typing import Any

from django.conf import settings

from .tools import execute_tool, get_available_tools_definition

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """
You are RentSecure's AI Assistant. You help property owners and renters
with questions about their properties, rent, payments, agreements, and more.

RULES:
- Only answer based on the data provided from tools.
- Never fabricate numbers, dates, or names.
- If data is missing, say so clearly.
- Use the user's role context when interpreting questions.
- Be concise and helpful.
- Currency is INR unless stated otherwise.
"""


def _call_openai(
    messages: list[dict[str, Any]], tools: list[dict[str, Any]]
) -> dict[str, Any] | None:
    if not getattr(settings, "ENABLE_OPENAI", False):
        return None
    if not getattr(settings, "OPENAI_API_KEY", ""):
        return None

    try:
        import openai

        openai.api_key = settings.OPENAI_API_KEY

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            tools=[{"type": "function", "function": t} for t in tools],
            temperature=0.2,
            max_tokens=500,
        )
        return response
    except Exception as exc:
        logger.warning("OpenAI call failed: %s", exc)
        return None


def _format_tool_result(result: dict[str, Any]) -> str:
    if "error" in result:
        return f"Error: {result['error']}"
    parts = []
    for key, value in result.items():
        if key == "tool":
            continue
        if isinstance(value, list):
            parts.append(f"{key}: {len(value)} items")
        elif isinstance(value, dict):
            parts.append(f"{key}: {value}")
        else:
            parts.append(f"{key}: {value}")
    return "; ".join(parts)


def generate_ai_response(
    user: Any, message: str, conversation_history: list[dict[str, Any]]
) -> dict[str, Any]:
    tools = get_available_tools_definition()
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(conversation_history[-10:])
    messages.append({"role": "user", "content": message})

    response = _call_openai(messages, tools)
    if response is not None:
        choice = response["choices"][0]["message"]
        tool_calls = choice.get("tool_calls")

        if tool_calls:
            tool_name = tool_calls[0]["function"]["name"]
            tool_result = execute_tool(tool_name, user)
            tool_context = _format_tool_result(tool_result)

            follow_up = _call_openai(
                messages
                + [
                    {
                        "role": "assistant",
                        "content": choice.get("content") or "",
                        "tool_calls": tool_calls,
                    },
                    {
                        "role": "tool",
                        "tool_call_id": tool_calls[0]["id"],
                        "content": tool_context,
                    },
                ],
                tools,
            )

            if follow_up is not None:
                reply = follow_up["choices"][0]["message"]["content"]
                return {
                    "response": reply,
                    "tools_used": [tool_name],
                    "data": tool_result,
                    "sources": ["backend"],
                }

            return {
                "response": tool_context,
                "tools_used": [tool_name],
                "data": tool_result,
                "sources": ["backend"],
            }

        reply = choice.get("content") or "I'm not sure how to help with that."
        return {
            "response": reply,
            "tools_used": [],
            "data": {},
            "sources": ["openai"],
        }

    tool_name = _detect_tool_from_message(message, user)
    if tool_name:
        tool_result = execute_tool(tool_name, user)
        return {
            "response": _format_tool_result(tool_result),
            "tools_used": [tool_name],
            "data": tool_result,
            "sources": ["backend"],
        }

    return {
        "response": (
            "I couldn't retrieve that information right now. " "Please try again later."
        ),
        "tools_used": [],
        "data": {},
        "sources": [],
    }


def _get_renter_profile(user: Any) -> Any | None:
    try:
        return user.renter_profile
    except Exception:
        logger.debug("User has no renter profile", exc_info=True)
        return None


def _matches_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _detect_renter_tool(lowered: str, renter_profile: Any) -> str | None:
    if not renter_profile:
        return None
    if _matches_any(lowered, ["payment history", "paid"]):
        return "get_payment_history"
    if _matches_any(lowered, ["next rent", "rent due"]):
        return "get_next_rent_due"
    if "agreement" in lowered:
        return "get_agreement_status"
    return None


def _detect_owner_tool(lowered: str, renter_profile: Any) -> str | None:
    if renter_profile:
        return None
    if "pending" in lowered and "rent" in lowered:
        return "get_pending_rents"
    if _matches_any(lowered, ["collection", "collected"]):
        return "get_rent_collection_summary"
    if "vacant" in lowered:
        return "get_vacant_units"
    if _matches_any(lowered, ["occupancy", "occupied"]):
        return "get_occupancy_summary"
    if _matches_any(lowered, ["renter", "tenant"]):
        return "get_renter_summary"
    return None


def _detect_tool_from_message(message: str, user: Any) -> str | None:
    lowered = message.lower()
    renter_profile = _get_renter_profile(user)

    owner_keywords = [
        "pending rent",
        "overdue rent",
        "rent collection",
        "vacant",
        "occupancy",
        "renters",
        "owner",
    ]

    is_owner_query = _matches_any(lowered, owner_keywords)

    tool = _detect_renter_tool(lowered, renter_profile)
    if tool:
        return tool

    tool = _detect_owner_tool(lowered, renter_profile)
    if tool:
        return tool

    if _matches_any(lowered, ["subscription", "plan"]):
        return "get_subscription_status"
    if _matches_any(lowered, ["notification", "alerts"]):
        return "get_notification_summary"
    if "maintenance" in lowered:
        return "get_maintenance_summary"

    if is_owner_query:
        return "get_pending_rents"

    return None
