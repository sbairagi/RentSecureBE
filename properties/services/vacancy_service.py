"""Vacancy Service Module.

Provides business logic for managing unit vacancy.
Owns vacancy detection, vacancy period tracking, and vacancy-related operations.
"""

from __future__ import annotations

from typing import Any


class VacancyService:
    """Service for vacancy business workflows.

    Expected responsibilities:
    - Vacancy detection and reporting
    - Vacancy period tracking
    - Vacancy cost calculation
    - Vacancy-based analytics
    """

    @staticmethod
    def detect_vacancy(unit: Any) -> bool:
        raise NotImplementedError

    @staticmethod
    def get_vacancy_period(unit: Any) -> Any:
        raise NotImplementedError

    @staticmethod
    def calculate_vacancy_cost(unit: Any, start_date: Any, end_date: Any) -> float:
        raise NotImplementedError

    @staticmethod
    def get_vacancy_report(user: Any) -> Any:
        raise NotImplementedError
