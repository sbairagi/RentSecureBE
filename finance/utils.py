"""Tax reporting utility functions for the finance app.

All public functions declare precise parameter and return types so they
can be invoked safely from DRF views, services, and management commands.
"""

from __future__ import annotations

import os
import tempfile
import zipfile
from typing import TYPE_CHECKING, Any

from django.core.files import File
from django.db.models import QuerySet
from django.template.loader import render_to_string
from openpyxl import Workbook  # type: ignore[import-untyped]
from weasyprint import HTML

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser

    from properties.models import Unit


def generate_tax_excel(
    user: AbstractUser,
    properties: QuerySet[Unit] | list[Unit],
    fy: str,
) -> str:
    """Render the per-FY tax Excel sheet and return the temp-file path.

    Args:
        user: Owner of the workbook. Used for filename prefix.
        properties: Units to render rows for.
        fy: Financial year label (e.g. ``"2024-25"``).

    Returns:
        Absolute path of the generated ``.xlsx`` file.
    """
    wb = Workbook()
    ws = wb.active
    if ws is None:
        raise RuntimeError("Failed to create active worksheet")
    ws.title = f"FY {fy}"

    headers: list[str] = [
        "Property",
        "Address",
        "Renter",
        "Rent Received",
        "Tax Paid",
        "Net Income",
    ]
    ws.append(headers)

    for p in properties:
        renter_name: str = (
            p.renter.name
            if hasattr(p, "renter") and getattr(p, "renter", None) is not None
            else "—"
        )
        row: list[Any] = [
            p.title,
            p.address_line,
            renter_name,
            p.rent_income_for_fy(fy),
            p.tax_paid_for_fy(fy),
            p.net_income_for_fy(fy),
        ]
        ws.append(row)

    fd, path = tempfile.mkstemp(suffix=".xlsx", prefix=f"{user.username}_tax_{fy}_")
    os.close(fd)
    wb.save(path)
    return path


def generate_tax_pdf(
    user: AbstractUser,
    properties: QuerySet[Unit] | list[Unit],
    fy: str,
) -> str:
    """Render the per-FY tax PDF and return the temp-file path."""
    html_string: str = render_to_string(
        "templates/pdf_templates/tax_summary_template.html",
        {
            "user": user,
            "properties": properties,
            "fy": fy,
        },
    )
    fd, pdf_file = tempfile.mkstemp(suffix=".pdf", prefix=f"{user.username}_tax_{fy}_")
    os.close(fd)
    HTML(string=html_string).write_pdf(pdf_file)
    return pdf_file


def create_tax_zip(
    user: AbstractUser,
    excel_path: str,
    pdf_path: str,
    extra_docs: list[File | str],
) -> str:
    """Bundle the Excel, PDF and any renter-uploaded files into a single zip.

    Args:
        user: Owner (used to prefix the zip filename).
        excel_path: Absolute path of the Excel file.
        pdf_path: Absolute path of the PDF file.
        extra_docs: Iterable of Django ``File`` objects (or strings) to
            include in the archive.

    Returns:
        Absolute path of the generated ``.zip`` file.
    """
    fd, zip_path = tempfile.mkstemp(suffix=".zip", prefix=f"{user.username}_tax_docs_")
    os.close(fd)
    with zipfile.ZipFile(zip_path, "w") as zipf:
        zipf.write(excel_path, os.path.basename(excel_path))
        zipf.write(pdf_path, os.path.basename(pdf_path))

        for doc in extra_docs:
            if not doc:
                continue
            doc_path: str = getattr(doc, "path", doc)  # type: ignore[arg-type]
            if os.path.exists(doc_path):
                zipf.write(doc_path, os.path.basename(doc_path))

    return zip_path
