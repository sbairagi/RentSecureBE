from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from properties.models import RentRecord
from smartbot.actions import send_agreement_for_signature


@require_GET
def agreement_status_view(request: HttpRequest) -> HttpResponse:
    records = RentRecord.objects.select_related("renter").all().order_by("-created_at")
    return render(request, "dashboard/agreement_status.html", {"records": records})


@csrf_exempt
@require_POST
def retry_signature(request: HttpRequest, rent_id: int) -> HttpResponse:
    if request.method == "POST":
        rent = RentRecord.objects.get(id=rent_id)
        if rent.renter is not None:
            send_agreement_for_signature(rent.renter.name)
    return redirect("agreement_status")
