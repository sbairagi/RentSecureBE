from django.shortcuts import redirect, render

from properties.models import RentRecord


def agreement_status_view(request):
    records = RentRecord.objects.select_related("renter").all().order_by("-created_at")
    return render(request, "dashboard/agreement_status.html", {"records": records})


from django.views.decorators.csrf import csrf_exempt

from smartbot.actions import send_agreement_for_signature


@csrf_exempt
def retry_signature(request, rent_id):
    if request.method == "POST":
        rent = RentRecord.objects.get(id=rent_id)
        send_agreement_for_signature(rent.renter.name)
        return redirect("agreement_status")
