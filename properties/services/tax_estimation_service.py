"""Income tax estimation utilities for ITR features."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class TaxEstimate:
    """Immutable tax estimate result."""

    def __init__(
        self,
        total_income: float,
        tax: float,
        brackets: list[dict[str, Any]],
    ) -> None:
        self.total_income = total_income
        self.tax = tax
        self.brackets = brackets


def estimate_tax(total_income: float) -> TaxEstimate:
    """Estimate Indian income tax for an individual using simplified FY 2024-25 slabs.

    New Regime (default):
        Up to ₹3,00,000        → 0%
        ₹3,00,001–₹6,00,000    → 5%
        ₹6,00,001–₹9,00,000    → 10%
        ₹9,00,001–₹12,00,000   → 15%
        ₹12,00,001–₹15,00,000  → 20%
        Above ₹15,00,000        → 30%

    Returns:
        TaxEstimate with tax amount and bracket breakdown.
    """
    income = float(total_income or 0)
    brackets = [
        {"up_to": 300000, "rate": "0%"},
        {"up_to": 600000, "rate": "5%"},
        {"up_to": 900000, "rate": "10%"},
        {"up_to": 1200000, "rate": "15%"},
        {"up_to": 1500000, "rate": "20%"},
        {"above": 1500000, "rate": "30%"},
    ]

    tax = 0.0
    last_limit = 0
    bracket_details = []

    for bracket in brackets:
        up_to = bracket.get("up_to")
        rate_str = bracket.get("rate", "0%")
        rate = float(rate_str.strip("%")) / 100

        if up_to is not None:
            if income > up_to:
                taxable = up_to - last_limit
                tax += taxable * rate
                last_limit = up_to
                bracket_details.append(
                    {
                        "range": f"₹{last_limit/100000:.1f}L",
                        "rate": rate_str,
                        "tax": round(taxable * rate, 2),
                    }
                )
            else:
                taxable = income - last_limit
                if taxable > 0:
                    tax += taxable * rate
                    bracket_details.append(
                        {
                            "range": (
                                f"₹{last_limit/100000:.1f}L" f" – ₹{income/100000:.1f}L"
                            ),
                            "rate": rate_str,
                            "tax": round(taxable * rate, 2),
                        }
                    )
                last_limit = income
                break
        else:
            taxable = income - last_limit
            if taxable > 0:
                tax += taxable * rate
                bracket_details.append(
                    {
                        "range": f"Above ₹{last_limit/100000:.1f}L",
                        "rate": rate_str,
                        "tax": round(taxable * rate, 2),
                    }
                )
            break

    return TaxEstimate(
        total_income=income,
        tax=round(tax, 2),
        brackets=bracket_details,
    )
