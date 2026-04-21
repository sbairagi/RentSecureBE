# utils/export_utils.py
from wealth_concierge_platform.models import RentRecord
import xlsxwriter
from io import BytesIO

def generate_owner_rent_report(owner):
    rents = RentRecord.objects.filter(renter__property__owner=owner).select_related('renter', 'renter__property')

    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    sheet = workbook.add_worksheet("Rent Report")

    headers = ["Property", "Renter", "Due Date", "Amount", "Status", "Payout"]
    for col, header in enumerate(headers):
        sheet.write(0, col, header)

    for row, rent in enumerate(rents, start=1):
        sheet.write(row, 0, rent.renter.property.title)
        sheet.write(row, 1, rent.renter.full_name)
        sheet.write(row, 2, rent.due_date.strftime('%Y-%m-%d'))
        sheet.write(row, 3, rent.amount)
        sheet.write(row, 4, rent.payment_status)
        sheet.write(row, 5, rent.payout_status)

    workbook.close()
    output.seek(0)
    return output