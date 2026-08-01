"""Vacancy detection and suggestion service.

Provides utilities for finding vacant units and generating
owner-facing suggestions for re-renting them.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import TYPE_CHECKING, Any, TypedDict

from django.db.models import QuerySet
from django.utils import timezone

if TYPE_CHECKING:
    from properties.models import Unit


class VacancySuggestion(TypedDict):
    unit_id: int
    unit_label: str
    building_name: str
    days_vacant: int
    suggestions: list[str]


class VacancyReport(TypedDict):
    total_vacant_units: int
    recent_vacancies: list[VacancySuggestion]
    long_term_vacancies: list[VacancySuggestion]


def _recent_cutoff(days: int = 7) -> date:
    return timezone.now().date() - timedelta(days=days)


def detect_vacant_units(owner: Any | None = None) -> QuerySet[Unit]:
    """Return units that are currently vacant.

    A unit is considered vacant when ``is_vacant=True``.
    Optionally filter by owner.
    """
    from properties.models import Unit

    qs = Unit.objects.filter(is_vacant=True, last_vacated_at__isnull=False)
    if owner is not None:
        qs = qs.filter(owner=owner)
    return qs.select_related("owner", "building")


def get_vacancy_suggestions(unit: Unit, days_vacant: int) -> list[str]:
    """Return actionable suggestions for a vacant unit."""
    suggestions: list[str] = [
        "📋 Add a new renter from your dashboard",
    ]
    if days_vacant >= 7:
        suggestions.append("📢 Consider posting this unit on rental marketplaces")
    if days_vacant >= 30:
        suggestions.append(
            "💰 Review pricing or offer limited-time discounts to attract tenants"
        )
    return suggestions


def build_vacancy_report(
    owner: Any | None = None, recent_days: int = 7, long_term_days: int = 30
) -> VacancyReport:
    """Build a vacancy report split into recent and long-term vacancies."""
    today = timezone.now().date()
    units = detect_vacant_units(owner)

    recent_vacancies: list[VacancySuggestion] = []
    long_term_vacancies: list[VacancySuggestion] = []

    for unit in units:
        last_vacated: date | None = unit.last_vacated_at
        if last_vacated is None:
            continue

        days_vacant = (today - last_vacated).days
        if days_vacant < recent_days:
            continue

        building_name = (
            unit.building.name
            if unit.building
            else getattr(unit, "building_name", None) or "your property"
        )
        unit_label = unit.unit

        suggestion = VacancySuggestion(
            unit_id=unit.pk,
            unit_label=unit_label,
            building_name=building_name,
            days_vacant=days_vacant,
            suggestions=get_vacancy_suggestions(unit, days_vacant),
        )

        if days_vacant >= long_term_days:
            long_term_vacancies.append(suggestion)
        else:
            recent_vacancies.append(suggestion)

    return VacancyReport(
        total_vacant_units=units.count(),
        recent_vacancies=recent_vacancies,
        long_term_vacancies=long_term_vacancies,
    )
