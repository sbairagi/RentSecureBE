# mypy: disable-error-code="import-not-found"

import os
import tempfile
from typing import Any

from PyPDF2 import PdfMerger

from django.conf import settings
from django.template.loader import render_to_string

from properties.models import RentAgreementDraft


def _read_pdf_if_exists(path: str | None) -> bytes:
    if not path or not os.path.exists(path):
        return b""
    with open(path, "rb") as output:
        return output.read()


def _get_tax_records(unit_obj: Any) -> Any:
    if hasattr(unit_obj, "unittaxrecord_set"):
        return unit_obj.unittaxrecord_set.all()
    if hasattr(unit_obj, "tax_records"):
        return unit_obj.tax_records
    return []


def generate_unit_history_pdf(unit_obj: Any) -> bytes:
    from weasyprint import HTML

    context = _build_pdf_context(unit_obj)
    agreement_paths = _collect_agreement_paths(unit_obj)
    html_string = render_to_string("pdf_templates/unit_history.html", context)

    with tempfile.TemporaryDirectory() as tmpdir:
        base_pdf_path = os.path.join(tmpdir, "unit_history_base.pdf")
        HTML(string=html_string, base_url=settings.BASE_DIR).write_pdf(base_pdf_path)

        if not agreement_paths:
            return _read_pdf_if_exists(base_pdf_path)

        return _merge_pdfs(base_pdf_path, agreement_paths, tmpdir)


def _build_pdf_context(unit_obj: Any) -> dict[str, Any]:
    return {
        "unit": unit_obj,
        "owner": unit_obj.owner,
        "caretakers": unit_obj.caretakers.all(),
        "renters": [],
        "tax_records": _get_tax_records(unit_obj),
    }


def _collect_agreement_paths(unit_obj: Any) -> list[str]:
    agreement_paths: list[str] = []
    context = _build_pdf_context(unit_obj)
    for renter in unit_obj.renters.all():
        renter_data = _build_renter_data(renter)
        context["renters"].append(renter_data)
        agreement_paths.extend(_get_renter_agreement_paths(renter))
    return agreement_paths


def _build_renter_data(renter: Any) -> dict[str, Any]:
    rent_records = renter.rent_records.all()
    rent_agreement_url = renter.rent_agreement.url if renter.rent_agreement else None
    police_verification_url = (
        renter.police_verification_pdf.url if renter.police_verification_pdf else None
    )
    possession_images = renter.unit.images.filter(renter=renter)

    return {
        "renter": renter,
        "rent_records": rent_records,
        "rent_agreement_url": rent_agreement_url,
        "police_verification_url": police_verification_url,
        "images": [img.image.url for img in possession_images],
    }


def _get_renter_agreement_paths(renter: Any) -> list[str]:
    paths: list[str] = []
    if renter.rent_agreement and hasattr(renter.rent_agreement, "path"):
        agreement_path = renter.rent_agreement.path
        if agreement_path and os.path.exists(agreement_path):
            paths.append(agreement_path)

    drafts = RentAgreementDraft.objects.filter(
        renter=renter,
        owner_signed=True,
        renter_signed=True,
    )
    for draft in drafts:
        if draft.file and hasattr(draft.file, "path"):
            draft_path = draft.file.path
            if draft_path and os.path.exists(draft_path):
                paths.append(draft_path)
    return paths


def _merge_pdfs(base_pdf_path: str, agreement_paths: list[str], tmpdir: str) -> bytes:
    merged_pdf_path = os.path.join(tmpdir, "unit_history_full.pdf")
    merger = PdfMerger()
    merger.append(base_pdf_path)
    for agreement_path in agreement_paths:
        merger.append(agreement_path)
    merger.write(merged_pdf_path)
    merger.close()
    return _read_pdf_if_exists(merged_pdf_path)
