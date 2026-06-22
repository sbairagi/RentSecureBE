from io import BytesIO
from typing import Any

import xlsxwriter

from properties.models import RentRecord


def generate_owner_rent_report(owner: Any) -> BytesIO:
    rents = RentRecord.objects.filter(renter__unit__owner=owner).select_related(
        "renter", "renter__unit"
    )

    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    sheet = workbook.add_worksheet("Rent Report")

    headers = ["Property", "Renter", "Due Date", "Amount", "Status", "Payout"]
    for col, header in enumerate(headers):
        sheet.write(0, col, header)

    for row, rent in enumerate(rents, start=1):
        if rent.renter is not None:
            sheet.write(row, 0, rent.renter.property.title)
            sheet.write(row, 1, rent.renter.full_name)
        else:
            sheet.write(row, 0, "")
            sheet.write(row, 1, "")
        sheet.write(row, 2, rent.due_date.strftime("%Y-%m-%d"))
        sheet.write(row, 3, rent.amount)
        sheet.write(row, 4, rent.payment_status)
        sheet.write(row, 5, rent.payout_status)

    workbook.close()
    output.seek(0)
    return output
