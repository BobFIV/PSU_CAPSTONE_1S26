from django.shortcuts import render
from .services import final_registration_status
# Create your views here.
def dashboard(request):
    return render(request, "ui/dashboard.html", {
        "registration_status": final_registration_status
    })