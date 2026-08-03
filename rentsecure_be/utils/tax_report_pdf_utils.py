"""PDF generation utilities for income tax reports.

All public functions declare precise parameter and return types so they
can be invoked safely from DRF views, services, and management commands.
"""

# mypy: disable-error-code="import-untyped"

from __future__ import annotations

import os
import tempfile
from typing import TYPE_CHECKING, Any

from django.template.loader import render_to_string

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser


def generate_tax_report_pdf(user: AbstractUser) -> str:
    """Generate a CA-style income tax report PDF for the given user.

    The report includes:
    - Personal info
    - Income summary (salary, rent, other)
    - Deductions (80C, 80D, 24(b), 80GG)
    - Tax computation
    - Personalized tax saving suggestions

    Args:
        user: Authenticated user for whom the report is generated.

    Returns:
        Absolute path of the generated ``.pdf`` file.
    """
    from rentsecure_be.utils.tax_advice_utils import (  # nosonar
        get_rent_income,
        suggest_tax_savings,
    )

    profile = user.userprofile

    income: dict[str, int] = {
        "salary": profile.salary or 0,
        "rent_income": get_rent_income(user),
        "other_income": profile.other_income or 0,
    }

    deductions: dict[str, int] = {
        "80C": profile.elss_investment or 0,
        "80D": 25000 if profile.has_health_insurance else 0,
        "24(b)": min(profile.home_loan_interest or 0, 200000),
        "80GG": (
            60000 if (profile.rent_paid or 0) > 0 and not profile.receives_hra else 0
        ),
    }

    suggestions = suggest_tax_savings(user)

    total_income = sum(income.values())
    total_deductions = sum(deductions.values())
    taxable_income = max(total_income - total_deductions, 0)
    estimated_tax = taxable_income * 0.2

    context: dict[str, Any] = {
        "user": user,
        "now": user.date_joined,
        "income": income,
        "deductions": deductions,
        "suggestions": suggestions,
        "total_income": total_income,
        "total_deductions": total_deductions,
        "taxable_income": taxable_income,
        "estimated_tax": estimated_tax,
    }

    html = render_to_string("pdfs/tax_report.html", context)

    fd, file_path = tempfile.mkstemp(suffix=".pdf", prefix="tax_report_")
    os.close(fd)
    from weasyprint import HTML  # nosonar

    HTML(string=html).write_pdf(file_path)
    return file_path
