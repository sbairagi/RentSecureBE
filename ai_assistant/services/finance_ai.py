from typing import Any


def analyze_financial_health(rents: list[Any], taxes: list[Any]) -> dict[str, Any]:
    on_time_rents = sum(1 for r in rents if not r.is_late)
    total_rents = len(rents)

    rent_score = (on_time_rents / total_rents) * 100 if total_rents else 0

    paid_taxes = sum(1 for t in taxes if t.status == "PAID")
    total_taxes = len(taxes)
    tax_score = (paid_taxes / total_taxes) * 100 if total_taxes else 0

    overall_score = int((0.6 * rent_score) + (0.4 * tax_score))

    suggestions = []
    if rent_score < 80:
        suggestions.append("⚠️ Improve rent payment timeliness")
    if tax_score < 70:
        suggestions.append("💡 Set property tax reminders")

    return {
        "rent_score": round(rent_score, 2),
        "tax_score": round(tax_score, 2),
        "overall_score": overall_score,
        "suggestions": suggestions,
    }
